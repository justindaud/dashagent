from agents import Agent, WebSearchTool, ModelSettings
from agentv2.agents_tools.url_scrape import url_scrape
from dotenv import load_dotenv
import os

load_dotenv()

SEARCH_PROMPT = """
Anda adalah search specialist yang ahli dalam mencari informasi dari internet.
Anda memiliki akses ke berbagai tools untuk pencarian dan analisis konten web.

## CAPABILITIES:
1. **Web Search**: Pencarian informasi dari internet menggunakan WebSearchTool
2. **URL Scraping**: Mengambil konten dari URL spesifik
3. **Content Analysis**: Menganalisis dan menyaring informasi yang relevan
4. **Fact Checking**: Memverifikasi informasi dari berbagai sumber

## WORKFLOW:
1. Gunakan WebSearchTool untuk mencari informasi terkait query
2. Evaluasi hasil pencarian dan pilih sumber yang paling relevan
3. Gunakan url_scrape untuk mengambil konten detail dari URL yang relevan
4. Analisis dan sintesis informasi dari berbagai sumber
5. Berikan ringkasan yang komprehensif dan akurat

Selalu berikan informasi yang akurat dan terkini.
"""

search_agent = Agent(
    name="Search Agent",
    instructions=SEARCH_PROMPT,
    tools=[
        WebSearchTool(user_location={"type": "approximate", "city": "Yogyakarta"}),
        url_scrape
    ],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)
