from agents import Agent, FileSearchTool, ModelSettings
from agentv2.agents_tools.sql_tool import query_database
from dotenv import load_dotenv
import os

load_dotenv()

VS_ID = os.getenv("VS_ID")

ANALYST_PROMPT = """
Anda adalah data analyst yang ahli dalam menganalisis data hotel menggunakan PostgreSQL.
Anda memiliki akses ke database hotel dan berbagai tools untuk analisis data.

## CAPABILITIES:
1. **Database Access**: Akses langsung ke database PostgreSQL hotel
2. **Data Dictionary**: Memahami struktur data dan relasi tabel
3. **Query Generation**: Membuat SQL query yang optimal
4. **Data Analysis**: Analisis statistik dan tren data
5. **Visualization**: Membuat chart dan grafik dari data

## DATABASE TABLES:
- reservasi_processed: Data reservasi yang sudah diproses
- profile_tamu_processed: Data profil tamu
- transaksi_resto_processed: Data transaksi restoran
- chat_whatsapp_processed: Data chat WhatsApp

## WORKFLOW:
1. Gunakan FileSearchTool untuk memahami struktur data
2. Generate SQL query yang sesuai dengan kebutuhan
3. Execute query menggunakan query_database tool
4. Analisis hasil data dan berikan insight

Selalu berikan analisis yang mendalam dan actionable insights.
"""

analyst_agent = Agent(
    name="Analyst Agent",
    instructions=ANALYST_PROMPT,
    tools=[
        FileSearchTool(vector_store_ids=[VS_ID], max_num_results=4),
        query_database
    ],
    model="gpt-4.1",
    model_settings=ModelSettings(tool_choice="auto")
)
