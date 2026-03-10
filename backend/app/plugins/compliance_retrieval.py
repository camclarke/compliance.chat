import os
import asyncio
from dotenv import load_dotenv
from semantic_kernel.functions import kernel_function

from app.services.crawler_service import CrawlerService
from app.services.sanitization_service import SanitizationService

class ComplianceRetrievalPlugin:
    """
    Tiered Retrieval RAG Engine:
    Tier 1: Query local Cosmos DB for vectorized regulations.
    Tier 2: Direct-to-Source government domain search (Crawl4AI).
    Tier 3: Secondary sources crawl and cross-referencing.
    """

    def __init__(self):
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
        
        # In a real implementation, we would instantiate Cosmos DB client here.
        # self.cosmos_client = ...
        
        self.crawler_service = CrawlerService()
        self.sanitization_service = SanitizationService()
        
    def _query_cosmos_db(self, query: str) -> str | None:
        """
        Tier 1: Simulated CosmosDB query.
        Returns None if confidence < 0.9 or data not found.
        """
        print(f"[Tier 1] Querying Azure Cosmos DB for: '{query}'")
        # Currently simulated. In a real environment, this utilizes native vector search.
        if "fcc" in query.lower():
            return "## FCC Part 15\n\nSection 15.247: Operation within the bands 902-928 MHz, 2400-2483.5 MHz, and 5725-5850 MHz."
        return None

    @kernel_function(
        description="Searches the official compliance database (NOMs, FCC rules, etc.) for legal text relevant to a user's question.",
        name="search_compliance_rules"
    )
    def search_compliance_rules(self, query: str) -> str:
        """
        Executes the Tiered Retrieval and Lazy Indexing loop.
        """
        print(f"\n[RAG Engine] Starting retrieval loop for: '{query}'")
        
        # --- TIER 1: INTERNAL GOLD DB ---
        tier1_result = self._query_cosmos_db(query)
        if tier1_result:
            print("[RAG Engine] Match found in Tier 1 (Cosmos DB).")
            return f"Source: Internal Tier 1 DB\n\n{tier1_result}"
            
        print("[RAG Engine] Tier 1 failed or low confidence. Falling back to Tier 2...")
        
        # --- TIER 2: OFFICIAL FALLBACK ---
        tier2_result = self.crawler_service.search_government_sources(query)
        if tier2_result:
            print("[RAG Engine] Match found in Tier 2 (Government Site).")
            # Trigger lazy indexing background task
            asyncio.create_task(self.crawler_service.lazy_index_background_task({"attribution_id": "Tier2_Source", "data": tier2_result}))
            return f"Source: Direct Government Source (Tier 2 Workflow)\n\n{tier2_result}"
            
        print("[RAG Engine] Tier 2 failed. Falling back to Tier 3 (Cross-Referencing)...")
        
        # --- TIER 3: SECONDARY SOURCE WASHING ---
        secondary_sources = self.crawler_service.search_secondary_sources(query)
        
        # Attempt to cross-reference and wash the data
        if "source_1" in secondary_sources and "source_2" in secondary_sources:
            washed_data = self.sanitization_service.cross_reference_and_wash(
                secondary_sources["source_1"], 
                secondary_sources["source_2"]
            )
            
            if washed_data.get("status") == "MANUAL_REVIEW_REQUIRED":
                print(f"[RAG Engine] ⚠️ ALERT: {washed_data['reason']}")
                return "[SYSTEM ALERT] I found conflicting data regarding your query across multiple secondary sources. A manual review by a Compliance Engineer is completely necessary before providing a technical bulletin. Do NOT rely on this query."
            
            if washed_data.get("status") == "WASHED_PROPRIETARY":
                print("[RAG Engine] Success: Tier 3 facts agree and have been washed of competitor branding.")
                
                # Format to a technical bulletin
                bulletin = f"--- TECHNICAL BULLETIN ---\nRegulation ID: {washed_data['attribution_id']}\n\nConfirmed Facts:\n"
                for key, val in washed_data['technical_facts'].items():
                    bulletin += f"- {key}: {val}\n"
                
                # Trigger lazy indexing background task with washed data
                asyncio.create_task(self.crawler_service.lazy_index_background_task({
                    "attribution_id": washed_data['attribution_id'],
                    "data": bulletin
                }))
                
                return bulletin
                
        return "[RAG Engine] Total retrieval failure. No verified official or secondary data could be synthesized for this query."
