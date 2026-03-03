import asyncio
from playwright.async_api import async_playwright
from parser import HTMLParser
from embedder import DocumentEmbedder

async def scrape_site(url: str) -> str:
    """
    Uses Microsoft Playwright to spawn a headless Chromium browser,
    navigate to a dynamic SPA, wait for the DOM to load, and extract the raw HTML.
    """
    print(f"Starting crawler for: {url}")
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to the target page and wait for the network to idle (meaning JS is done)
        print("Navigating to page and waiting for SPA to render...")
        await page.goto(url, wait_until="networkidle")
        
        # Extract the fully rendered HTML string
        content = await page.content()
        await browser.close()
        return content

async def main():
    target_url = "https://www.fcc.gov/general/rules-regulations-title-47" # Example starting point
    
    # 1. Scrape the dynamic web page (Playwright)
    raw_html = await scrape_site(target_url)
    
    # 2. Parse HTML to structured Markdown (BeautifulSoup + Markdownify)
    print("Parsing HTML to Markdown...")
    markdown_content = HTMLParser.convert_to_markdown(raw_html)
    
    # 3. Chunk and Embed the Markdown into ChromaDB
    print("Chunking, Embedding, and Indexing into ChromaDB...")
    embedder = DocumentEmbedder()
    docs = embedder.chunk_markdown(markdown_content)
    embedder.ingest_documents(docs)
    
    print("✅ Web scraping and ingestion pipeline complete.")

if __name__ == "__main__":
    asyncio.run(main())
