import os
import argparse
from dotenv import load_dotenv

# Load environment variables from the backend folder
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma

def ingest_documents(data_dir: str, persist_dir: str):
    print(f"Loading PDFs from directory tree: {data_dir}")
    # PyPDFDirectoryLoader automatically searches subdirectories and extracts metadata
    loader = PyPDFDirectoryLoader(data_dir)
    documents = loader.load()
    print(f"Loaded {len(documents)} total document pages.")

    if not documents:
        print("No PDF documents found. Exiting.")
        return

    print("Splitting text into semantic chunks...")
    # Clean, overlapping chunks ensure we don't cut legal sentences in half
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split document pages into {len(chunks)} semantic chunks.")

    print("Connecting to Azure text-embedding-3-small...")
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        openai_api_version="2023-05-15" # Standard stable API version
    )

    print(f"Vectorizing chunks and storing in local Chroma database at: {persist_dir}")
    # Initialize Chroma
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_dir
    )
    
    import time
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1} of {(len(chunks)-1)//batch_size + 1}...")
        try:
            vectorstore.add_documents(batch)
        except Exception as e:
            if "429" in str(e):
                print("Azure Rate limit hit, sleeping for 60 seconds...")
                time.sleep(60)
                vectorstore.add_documents(batch)
            else:
                raise e
        time.sleep(2) # Micro-delay between batches
    
    
    print("✅ Ingestion complete. Vector database is populated and ready for RAG querying.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Compliance PDFs into Vector DB")
    parser.add_argument(
        "--data-dir", 
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "compliance-library", "countries"),
        help="Directory containing the target PDFs"
    )
    parser.add_argument(
        "--persist-dir", 
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db"),
        help="Directory to persist the local vector database"
    )
    
    args = parser.parse_args()
    ingest_documents(args.data_dir, args.persist_dir)
