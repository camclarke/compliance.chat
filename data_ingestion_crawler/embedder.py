import os
import chromadb
from dotenv import load_dotenv
from langchain_community.embeddings.openai import AzureOpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Load the same Azure environment variables used by the backend
load_dotenv(dotenv_path="../backend/.env")

class DocumentEmbedder:
    def __init__(self):
        print("Initializing Azure OpenAI Embeddings...")
        # Grab these from the local .env we built in Phase 1
        self.embeddings_model = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
            azure_deployment="text-embedding-3-small" # The deployment name in Microsoft Foundry
        )
        
        # Initialize LOCAL ChromaDB inside the data_ingestion_crawler directory
        print("Initializing local ChromaDB Vector Store...")
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Create or Get the collection for compliance documents
        self.collection = self.chroma_client.get_or_create_collection(
            name="compliance_library",
            metadata={"hnsw:space": "cosine"}
        )

    def chunk_markdown(self, markdown_text: str):
        """
        Splits a giant Markdown string into meaningful semantic chunks based on headers.
        """
        headers_to_split_on = [
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3"),
        ]
        
        # Split semantically by headers
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(markdown_text)
        
        # Ensure chunks aren't too massive for the embedding model to handle
        chunk_size = 1000
        chunk_overlap = 150
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
        
        final_splits = text_splitter.split_documents(md_header_splits)
        print(f"Generated {len(final_splits)} semantic chunks from Markdown document.")
        return final_splits
        
    def ingest_documents(self, documents):
        """
        Generates vectors for all chunks via Azure OpenAI and saves them locally.
        """
        text_chunks = [doc.page_content for doc in documents]
        
        # The metadata dictionary contains the original Markdown Header tags
        metadata_chunks = [doc.metadata for doc in documents]
        
        # Generate generic IDs
        ids = [f"doc_chunk_{i}" for i in range(len(documents))]
        
        print(f"Submitting {len(text_chunks)} chunks to Azure OpenAI 'text-embedding-3-small'...")
        
        # Note: In a production scenario with thousands of chunks, you would 
        # batch these requests to avoid Azure Rate Limits, but for a single page this is safe.
        embeddings = self.embeddings_model.embed_documents(text_chunks)
        
        print("Saving vectors and text to local ChromaDB...")
        self.collection.add(
            embeddings=embeddings,
            documents=text_chunks,
            metadatas=metadata_chunks,
            ids=ids
        )
        print("Ingestion complete.")
