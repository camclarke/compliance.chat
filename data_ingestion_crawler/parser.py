import re
from bs4 import BeautifulSoup
import markdownify

class HTMLParser:
    @staticmethod
    def clean_html(raw_html: str) -> str:
        """
        Uses BeautifulSoup to remove heavy script tags, styles, nav bars,
        and sidebars from the page so we only process the core compliance text.
        """
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # Remove noisy elements
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()
            
        # Optional: You can target a specific ID if you know the government website structure
        # main_content = soup.find('main') or soup.body
        # return str(main_content)
        
        return str(soup.body)

    @staticmethod
    def convert_to_markdown(raw_html: str) -> str:
        """
        Cleans the HTML and converts it to a structured Markdown string.
        Markdown is significantly better for RAG chunking than raw text or HTML.
        """
        cleaned_html = HTMLParser.clean_html(raw_html)
        
        # Convert HTML to Markdown format
        md_text = markdownify.markdownify(cleaned_html, heading_style="ATX", strip=['img'])
        
        # Clean up excessive newlines
        md_text = re.sub(r'\n{3,}', '\n\n', md_text)
        
        return md_text
