from agents import Agent, function_tool, WebSearchTool, ModelSettings
from bs4 import BeautifulSoup
import requests

@function_tool
def url_scrape(url: str) -> str:
    """
    Scrape the content of a web page and return the text from the given url
    """
    try:
        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP errors

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.extract()
            
            text = soup.get_text(separator=' ', strip=True)

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text[:5000]
        except ImportError:
            return response.text[:5000]
    except Exception as e:
        return f"Failed to scrape content from {url}: {str(e)}"

SEARCH_AGENT_PROMPT = """
Anda adalah peneliti yang terfokus untuk melakukan pencarian informasi di web.
Anda akan menggunakan WebSearchTool untuk mencari informasi relevan, cari beberapa URL yang relevan.
Anda akan menganalisis isi konten dari URL tersebut.
Anda akan membuat ringkasan concise dari konten yang ditemukan, memuat sekitar 2-3 paragraf. Peroleh poin utama, buat tulisan succinctly.
Anda tidak perlu membuat kalimat utuh atau dengan grammar sempurna. Anda tidak akan memberikan komentar tambahan diluar ringkasan tersebut
"""
search_agent = Agent(
    name="Search Agent",
    instructions=SEARCH_AGENT_PROMPT,
    tools=[
        WebSearchTool(user_location={"type": "approximate", "city": "Yogyakarta"})
    ],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)
