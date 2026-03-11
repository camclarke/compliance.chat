import os
import asyncio
import uuid
import logging
from typing import Optional, Dict, Any
from crawl4ai import AsyncWebCrawler
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import AzureTextEmbedding
from azure.cosmos.aio import CosmosClient

logger = logging.getLogger(__name__)

class CrawlerService:
    """
    Handles Tier 2 (Official Fallback) and Tier 3 (Secondary Sources) retrieval using Crawl4AI.
    """

    def __init__(self):
        from app.core.config import settings
        self.settings = settings
        
        # Initialize Embedding Service
        self.embedding_service = AzureTextEmbedding(
            deployment_name=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
        )
        
        # Initialize Cosmos DB Client definition (lazy loaded)
        self.cosmos_endpoint = os.getenv("AZURE_COSMOS_DB_ENDPOINT")
        self.cosmos_key = os.getenv("AZURE_COSMOS_DB_KEY")
        self.database_name = os.getenv("AZURE_COSMOS_DB_DATABASE_NAME", "ComplianceDB")
        self.container_name = "vectors"

    async def _crawl_url(self, url: str) -> Optional[str]:
        """
        Base method to crawl a single URL and return its markdown content.
        Uses Playwright under the hood via Crawl4AI.
        """
        print(f"[Crawl4AI] Navigating to: {url}")
        try:
            async with AsyncWebCrawler(verbose=True) as crawler:
                # fit_markdown ensures we get clean, RAG-ready text
                result = await crawler.arun(url=url, bypass_cache=True)
                if result.success:
                    return result.fit_markdown
                else:
                    print(f"[Crawl4AI] Failed to index {url}. Error: {result.error_message}")
                    return None
        except Exception as e:
            print(f"[Crawl4AI] Exception during crawl: {str(e)}")
            return None

    def search_government_sources(self, query: str) -> Optional[str]:
        """
        Tier 2: Direct-to-Source search restricted to government domains.
        In a full implementation, this would use a search API (e.g. Bing Custom Search) 
        restricted to `site:.gov` or specific regulatory domains, then crawl the results.
        For MVP simulation, we return a mock URL text if it matches a known domain, 
        or None to trigger Tier 3.
        """
        print(f"[Tier 2] Searching government sources for: '{query}'")
        
        # TODO: Integrate Bing Web Search API restricted to site:.gov.mx, site:.gov, etc.
        # For now, we simulate a failure to find it on a government site to demonstrate Tier 3
        # unless the query explicitly asks for a mock government link.
        if "mock_gov" in query.lower():
            # Simulate a successful crawl of a government site
            return "## Mexican Official Standard NOM-001-SCFI-2018\n\nArticle 1: This standard applies to highly specialized electronic equipment. Voltage must be 220V."
        
        print("[Tier 2] No official government sources found.")
        return None

    def search_secondary_sources(self, query: str) -> Dict[str, str]:
        """
        Tier 3: Query 3 high-authority secondary sources.
        Returns a dictionary of {source_name: markdown_content}.
        """
        print(f"[Tier 3] Searching secondary sources for: '{query}'")
        
        # TODO: Integrate Bing Web Search API here to find 3 law firm/consultancy articles.
        # For MVP simulation, returning mock markdown from two "competitor" sources.
        
        source_1 = """
        # Compliance Guide by Baker McKenzie
        According to the latest regulatory updates in Brazil (Resolution 715), the power limit for Bluetooth devices is strictly 100W. 
        """
        
        source_2 = """
        # Tech Regulations - Deloitte Insights
        When exporting to the LATAM region, be aware that Anatel Resolution 715 enforces a 100W power limit on short-range devices.
        """
        
        return {
            "source_1": source_1,
            "source_2": source_2
        }

    async def lazy_index_background_task(self, compliance_data: Dict[str, Any]):
        """
        Background Ingestion Loop: Triggers chunking, embedding, and permanently routing 
        the newly found data into Cosmos DB.
        """
        source = compliance_data.get('attribution_id', 'Unknown_Source')
        text_data = compliance_data.get('data', '')
        
        if not text_data:
            logger.warning("[Lazy Indexing] No text data provided to vectorize.")
            return

        logger.info(f"[Lazy Indexing] Triggering background job to vectorize and store data into Cosmos DB: {source}")
        
        try:
            # 1. Simple Chunking (In production, use semantic_kernel.text.text_chunker)
            chunk_size = 1000
            overlap = 100
            chunks = []
            for i in range(0, len(text_data), chunk_size - overlap):
                chunks.append(text_data[i:i + chunk_size])
                
            logger.info(f"[Lazy Indexing] Split data into {len(chunks)} chunks.")

            # 2. Vectorize the chunks
            embeddings_result = await self.embedding_service.generate_embeddings(chunks)
            if not getattr(embeddings_result, "success", True) and not isinstance(embeddings_result, list): # Basic check since sk object varies
                logger.error("[Lazy Indexing] Failed to generate embeddings.")
                return
                
            # Assume embeddings_result is a list of floats arrays (or list of numpy arrays)
            embeddings = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings_result]

            # 3. Store into Azure Cosmos DB
            if not self.cosmos_endpoint or not self.cosmos_key:
                logger.warning("[Lazy Indexing] Cosmos DB endpoint/key not configured. Tracing only.")
                for idx, chunk in enumerate(chunks):
                    logger.debug(f"[Vector Simulated Insert] Document ID: {source}_{idx} inserted with dim: {len(embeddings[idx])}")
                return

            async with CosmosClient(self.cosmos_endpoint, credential=self.cosmos_key) as client:
                database = client.get_database_client(self.database_name)
                container = database.get_container_client(self.container_name)
                
                ops = []
                for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                    doc_id = str(uuid.uuid4())
                    doc = {
                        "id": doc_id,
                        "source": source,
                        "text": chunk_text,
                        "contentVector": embedding,
                        "type": "Crawl4AI_Ingestion"
                    }
                    ops.append(doc)
                    
                    # Batch inserts loosely
                    try:
                        await container.upsert_item(doc)
                    except Exception as cx:
                        logger.error(f"[Lazy Indexing] Cosmos insert err: {cx}")
                        
                logger.info(f"[Lazy Indexing] Successfully upserted {len(ops)} vectorized items to Cosmos DB.")

        except Exception as e:
            logger.error(f"[Lazy Indexing] Exception during background task: {e}")
