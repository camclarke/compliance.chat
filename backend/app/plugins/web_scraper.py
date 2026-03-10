import asyncio
from crawl4ai import AsyncWebCrawler
from semantic_kernel.functions import kernel_function
from app.services.crawler_service import CrawlerService
from semantic_kernel.functions import kernel_function

class WebScraperPlugin:
    """
    A Semantic Kernel Plugin that gives the AI the ability to scrape text directly from 
    live government websites or compliance portals.
    """

    def __init__(self):
        self.crawler_service = CrawlerService()

    @kernel_function(
        description="Scrapes the readable text content from a given live URL (e.g., Anatel or FCC website). Use this ONLY when you need real-time data or if the PDF database doesn't have the answer.",
        name="scrape_website_text"
    )
    async def scrape_website_text(self, url: str) -> str:
        """
        Takes a URL, fetches the page using Crawl4AI, and returns cleaned Markdown.
        """
        print(f"[Scraper Plugin] Autonomously crawling URL (Crawl4AI): {url}")
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                
                if result.success:
                    # Trigger the lazy indexing background task to permanently embed this knowledge
                    asyncio.create_task(self.crawler_service.lazy_index_background_task({
                        "attribution_id": url,
                        "data": result.markdown
                    }))
                    
                    # Return the first 8000 characters to provide richer context
                    # while avoiding breaking the LLM context window
                    return result.markdown[:8000]
                else:
                    return f"Failed to scrape the website {url}. Error: {result.error_message}"

        except Exception as e:
            return f"Failed to scrape the website {url}. Exception: {str(e)}"
