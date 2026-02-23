import asyncio
import sys
import logging

# Set up logging so we can see Semantic Kernel deciding to use the scraper
logging.basicConfig(level=logging.INFO)

from app.services.agent_orchestrator import create_kernel, process_chat_message

async def main():
    print("Initializing Semantic Kernel with Web Scraper Plugin...")
    kernel = create_kernel()
    
    # We ask a question that requires scraping a live URL that doesn't actively block basic Python requests
    test_question = "Please go to https://en.wikipedia.org/wiki/Federal_Communications_Commission and tell me what the FCC regulates. Summarize it in one short paragraph."
    
    print(f"\nUser Question:\n{test_question}\n")
    print("Asking the Swarm (Watch for it to trigger the WebScraper plugin)...\n")
    
    try:
        reply = await process_chat_message(kernel, test_question)
        print("\n--- FINAL AI REPLY ---")
        print(reply)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
