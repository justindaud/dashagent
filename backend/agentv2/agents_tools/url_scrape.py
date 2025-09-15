from agents import function_tool
import requests
from bs4 import BeautifulSoup
import re

@function_tool
def url_scrape(url: str) -> str:
    """
    Scrape content from a URL and return clean text.
    
    Args:
        url: URL to scrape
        
    Returns:
        Clean text content from the URL
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit length
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        return text
        
    except Exception as e:
        return f"Error scraping URL: {str(e)}"

# Export the function directly for use in agents
# url_scrape is already available as a function
