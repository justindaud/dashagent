import os
import asyncio
from agents import Agent, Runner, ModelSettings, trace, FileSearchTool, ItemHelpers
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine
from agents_tools.sematicsearch_tool import search_insights_semantic
load_dotenv()

EXPERIENCE_VS_ID = os.getenv("EXPERIENCE_VS_ID")
VS_ID = os.getenv("VS_ID")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'postgresql://' -> 'postgresql+asyncpg://'
    DATABASE_URL = "postgresql+asyncpg://" + DATABASE_URL[len("postgresql://"):]
elif DATABASE_URL.startswith("mysql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'mysql://' -> 'mysql+aiomysql://'
    DATABASE_URL = "mysql+aiomysql://" + DATABASE_URL[len("mysql://"):]
elif DATABASE_URL.startswith("sqlite://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'sqlite:///' -> 'sqlite+aiosqlite:///'
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

PROMPT_AGENT_PROMPT = """
    Anda adalah agent prompt decomposer yang akan menerima user prompt dan menjelaskan prompt pada tim agent.
    Anda akan menghasilkan satu prompt untuk diterima oleh orchestrator.
    Jika user prompt tidak kompleks anda tidak perlu overcomplicate.

    Anda perlu memahami anggota dan kapabilitas tim agent yang sebagai berikut:

    ## PERAN AGENTS:
    1. **Orchestrator**: Agent untuk melakukan orkestrasi kerja dari Analyst Agent dan Search Agent menyesuaikan kebutuhan tugas.
    1. **Analyst Agent**: Agent untuk menganalisis data dengan mengakses database (PostgreSQL)
    2. **Search Agent**: Agent untuk melakukan pencarian informasi dari internet

    ## TOOLS AGENTS:
    1. **Orchestrator**: Agent dilengkapi dengan Analyst Agent dan Search Agent as tool.
    1. **Analyst Agent**: Agent dilengkapi tool FileSearchTool untuk melihat data dictionary & manifest, query_database untuk generate dan execute query, CodeInterpreterTool analisis kompleks lanjutan dari data yang telah diambil dari database.
    2. **Search Agent**: Agent ini dilengkapi WebSearchTool dan url_scrape untuk melakukan pencarian informasi di web dan menganalisis konten yang ditemukan.

    Jika prompt user kompleks, maka buat prompt/query yang mengikuti spesifikasi:
    1. Memuat user prompt asli 
    2. Memuat eksplanasi intent user dari prompt asli
    3. Memuat detail spesifik terkait step-by-step, agent & tools yang perlu digunakan, contoh sql query, contoh web untuk search, dll.
    4. Memuat thoughts kenapa anda menyarankan cara response tersebut
    """
HANDOFF_DESCRIPTION = """
    Agent ini memiliki peranan sebagai prompt user decomposer untuk menghasilkan prompt-prompt
    baru untuk menjawab user dengan lebih holistik
    """

class PromptResponse(BaseModel):
    queries: list[str]
    #thoughts: list[str]
    @field_validator("queries", mode="before")
    def enforce_prefix(cls, v):
        prefix = "TASK DARI DECOMPOSER UNTUK ORCHESTRATOR"
        # v di sini bisa berupa list[str] atau str tunggal, tergantung context
        if isinstance(v, list):
            return [q if q.startswith(prefix) else f"{prefix}\n{q}" for q in v]
        if isinstance(v, str):
            return v if v.startswith(prefix) else f"{prefix}\n{v}"
        return v

async def main():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

    # make session
    session = SQLAlchemySession(
        "testsematictool5",
        engine=engine,
        create_tables=True,
    )
    
    agent = Agent(
        name="Prompt_Agent",
        instructions=PROMPT_AGENT_PROMPT,
        tools=[
            #FileSearchTool(vector_store_ids=[VS_ID], max_num_results=4),
            #FileSearchTool(vector_store_ids=[EXPERIENCE_VS_ID], max_num_results=4),
            search_insights_semantic
        ],
        model="gpt-5",
        output_type=PromptResponse,
        model_settings=ModelSettings(tool_choice="required")
        )
    
    with trace("testing agent"):
        result = await Runner.run(
            agent,
            "apakah kita menyimpan data instagram hotel kita?",
            session=session,
            )
        print(result.final_output)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())