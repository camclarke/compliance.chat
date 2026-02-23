import os
from dotenv import load_dotenv
from semantic_kernel.functions import kernel_function
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings

class ComplianceRetrievalPlugin:
    """
    A Semantic Kernel Plugin that gives the AI the ability to search for physical compliance laws
    within the local Azure Data Lake (ChromaDB) simulator.
    """

    def __init__(self):
        # Load environment variables
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
        
        # Initialize the same embedding model used during ingestion
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            openai_api_version="2023-05-15"
        )
        
        # Connect to the local vector database
        persist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma_db")
        self.vectorstore = Chroma(
            embedding_function=self.embeddings,
            persist_directory=persist_dir
        )

    @kernel_function(
        description="Searches the official compliance database (NOMs, FCC rules, etc.) for legal text relevant to a user's question.",
        name="search_compliance_rules"
    )
    def search_compliance_rules(self, query: str) -> str:
        """
        Takes a natural language query, vectorizes it, and returns the top 3 most relevant paragraphs 
        from the official compliance documents.
        """
        print(f"[RAG Plugin] Searching database for: '{query}'")
        try:
            # Perform similarity search, returning the top 3 closest chunks
            docs = self.vectorstore.similarity_search(query, k=3)
            
            if not docs:
                return "I could not find any specific compliance rules related to this query in the database."
            
            # Format the output for the LLM to read easily
            formatted_results = "Here are the official compliance rules found in the database:\n\n"
            for i, doc in enumerate(docs):
                source = doc.metadata.get('source', 'Unknown Document')
                # Extract just the filename for cleaner citations
                filename = os.path.basename(source)
                formatted_results += f"--- SOURCE {i+1}: {filename} ---\n{doc.page_content}\n\n"
                
            return formatted_results
            
        except Exception as e:
            return f"An error occurred while searching the database: {str(e)}"
