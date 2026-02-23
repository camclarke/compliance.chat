import urllib.request
from bs4 import BeautifulSoup
from semantic_kernel.functions import kernel_function

class WebScraperPlugin:
    """
    A Semantic Kernel Plugin that gives the AI the ability to scrape text directly from 
    live government websites or compliance portals.
    """

    @kernel_function(
        description="Scrapes the readable text content from a given live URL (e.g., Anatel or FCC website). Use this ONLY when you need real-time data or if the PDF database doesn't have the answer.",
        name="scrape_website_text"
    )
    def scrape_website_text(self, url: str) -> str:
        """
        Takes a URL, fetches the HTML, and extracts clean text using BeautifulSoup.
        """
        print(f"[Scraper Plugin] Autonomously crawling URL: {url}")
        try:
            # We use a standard User-Agent so government sites don't immediately block the request
            req = urllib.request.Request(
                url, 
                data=None, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove navigation, scripts, and styles to get just the actual regulation text
            for script in soup(['script', 'style', 'header', 'footer', 'nav']):
                script.decompose()

            # Get the text
            text = soup.get_text(separator='\n')

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)

            # Return the first 4000 characters to avoid breaking the LLM context window
            # Most compliance answers are found near the top of the official notice pages anyway.
            return clean_text[:4000]

        except Exception as e:
            return f"Failed to scrape the website {url}. Error: {str(e)}"
