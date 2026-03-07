import os
import logging
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.cosmos import CosmosClient

from langchain_community.embeddings.openai import AzureOpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Initialize logging for our Container App
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

app = FastAPI(title="Compliance Chat Document Ingestion Worker")

@app.post("/api/process-blob")
async def process_blob(request: Request):
    """
    Webhook endpoint for Azure Event Grid.
    Listens for new blobs created in the 'inbox' container.
    """
    events = await request.json()
    
    for event in events:
        event_type = event.get("eventType")
        data = event.get("data", {})
        
        if event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
            validation_code = data.get("validationCode")
            logger.info("Successfully received Event Grid subscription validation handshake.")
            return {"validationResponse": validation_code}
            
        elif event_type == "Microsoft.Storage.BlobCreated":
            blob_url = data.get("url")
            logger.info(f"Wake Up Call! New Blob Created: {blob_url}")
            
            try:
                await handle_new_document(blob_url)
            except Exception as e:
                logger.error(f"Error processing document {blob_url}: {str(e)}")
                
    return {"status": "success"}


async def handle_new_document(blob_url: str):
    """
    Core business logic for processing a new PDF document.
    """
    logger.info(f"Starting pipeline for {blob_url}...")
    
    # Quick string parsing string to extract container and blob name
    parts = blob_url.split('/')
    container_name = parts[3]
    blob_name = '/'.join(parts[4:])
    logger.info(f"Container: {container_name}, Blob: {blob_name}")
    
    # =========================================================================
    # 1. Download PDF from Azure Blob Storage
    # =========================================================================
    storage_conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not storage_conn:
        logger.error("Missing AZURE_STORAGE_CONNECTION_STRING")
        return

    blob_service_client = BlobServiceClient.from_connection_string(storage_conn)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    pdf_bytes = blob_client.download_blob().readall()
    logger.info(f"Successfully downloaded {len(pdf_bytes)} bytes from Azure Blob Storage.")

    # =========================================================================
    # 2. Extract Text and Markdown using Azure Document Intelligence
    # =========================================================================
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    document_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    
    logger.info("Sending document precisely to Azure Document Intelligence for Markdown extraction...")
    poller = document_client.begin_analyze_document(
        "prebuilt-layout", 
        body=pdf_bytes,
        output_content_format="markdown"
    )
    result = poller.result()
    markdown_content = result.content
    logger.info("Successfully extracted clean Markdown from PDF.")

    # =========================================================================
    # 3. Chunk the Document into Semantic Pieces
    # =========================================================================
    headers_to_split_on = [("#", "Header_1"), ("##", "Header_2"), ("###", "Header_3")]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_content)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    final_splits = text_splitter.split_documents(md_header_splits)
    logger.info(f"Generated {len(final_splits)} semantic chunks.")

    # =========================================================================
    # 4. Generate Embeddings using Azure OpenAI
    # =========================================================================
    # Reusing the existing pattern defined in embedder.py
    embeddings_model = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview",
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    )
    
    text_chunks = [doc.page_content for doc in final_splits]
    metadata_chunks = [doc.metadata for doc in final_splits]
    logger.info("Submitting chunks to Azure OpenAI for Vectorization...")
    embeddings = embeddings_model.embed_documents(text_chunks)
    
    # =========================================================================
    # 5. Store Final Vectorized Data Securely in Azure Cosmos DB
    # =========================================================================
    cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
    cosmos_key = os.getenv("AZURE_COSMOS_KEY")
    cosmos_db_name = os.getenv("AZURE_COSMOS_DATABASE")
    cosmos_container_name = os.getenv("AZURE_COSMOS_CONTAINER", "documents")
    
    cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
    database = cosmos_client.get_database_client(cosmos_db_name)
    container = database.get_container_client(cosmos_container_name)
    
    logger.info(f"Inserting into Cosmos DB Container: {cosmos_container_name}...")
    for i, (text, metadata, vector) in enumerate(zip(text_chunks, metadata_chunks, embeddings)):
        # Cosmos DB requires an 'id'
        doc_id = f"{blob_name.replace('.pdf', '')}_chunk_{i}"
        
        # Build the physical document payload
        cosmos_doc = {
            "id": doc_id,
            "source_file": blob_name,
            "content": text,
            "metadata": metadata,
            "embedding": vector # DiskANN will natively index this!
        }
        container.upsert_item(body=cosmos_doc)

    logger.info(f"Successfully finished processing pipeline for {blob_name}. Cosmos DB updated.")

if __name__ == "__main__":
    import uvicorn
    # The Container App will continuously listen on Port 80
    uvicorn.run("data_ingestion_crawler.app:app", host="0.0.0.0", port=80, reload=True)
