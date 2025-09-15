import os
import asyncio
from agents import Agent, Runner, ModelSettings, trace, FileSearchTool
from dotenv import load_dotenv
from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine
from agents_tools.sql_tool import query_database
load_dotenv()

VS_ID = os.getenv("VS_ID")

DATABASE_URL = os.getenv("DATABASE_URL")

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

if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'postgresql://' -> 'postgresql+asyncpg://'
    DATABASE_URL = "postgresql+asyncpg://" + DATABASE_URL[len("postgresql://"):]
elif DATABASE_URL.startswith("mysql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'mysql://' -> 'mysql+aiomysql://'
    DATABASE_URL = "mysql+aiomysql://" + DATABASE_URL[len("mysql://"):]
elif DATABASE_URL.startswith("sqlite://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'sqlite:///' -> 'sqlite+aiosqlite:///'
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

async def main():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

    # make session
    session = SQLAlchemySession(
        "testing",
        engine=engine,
        create_tables=True,
    )
    
    agent = Agent(
        name="Analyst Agent",
        instructions=ANALYST_PROMPT,
        tools=[
            FileSearchTool(vector_store_ids=[VS_ID], max_num_results=4),
            query_database
        ],
        model_settings=ModelSettings(tool_choice="required")
    )
    with trace("testing agent"):
        result = await Runner.run(agent, "Berikan profile orang tersebut", session=session)
        print(result.final_output)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())