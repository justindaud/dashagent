from agents import Agent, FileSearchTool, ModelSettings
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

EXPERIENCE_VS_ID = os.getenv("EXPERIENCE_VS_ID")
VS_ID = os.getenv("VS_ID")

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
# split them to make each queries got their thoughts
class PromptResponse(BaseModel):
    queries: list[str]
    #thoughts: list[str]

prompt_agent = Agent(
    name="Prompt Generator Agent",
    instructions=PROMPT_AGENT_PROMPT,
    output_type=PromptResponse,
    tools=[
        FileSearchTool(vector_store_ids=[EXPERIENCE_VS_ID], max_num_results=4),
        FileSearchTool(vector_store_ids=[VS_ID], max_num_results=4)
    ],
    model_settings=ModelSettings(tool_choice="auto"),
    model="gpt-5",
    handoff_description=HANDOFF_DESCRIPTION
    )
