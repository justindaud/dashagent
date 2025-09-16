import os
import asyncio
from agents import Agent, Runner, ModelSettings, trace, FileSearchTool, ItemHelpers
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine
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
    Anda adalah agent prompt decomposer yang akan menerima user prompt.
    Anda akan menghasilkan beberapa prompt untuk diterima oleh orchestrator.

    Setiap prompt/query yang anda hasilkan perlu mengikuti spesifikasi:
    1. Memuat user prompt asli 
    2. Memuat eksplanasi intent user dari prompt asli
    3. Memuat detail spesifik terkait step-by-step, agent & tools yang perlu digunakan, contoh sql query, contoh web untuk search, dll.
    4. Memuat thoughts kenapa anda menyarankan cara response tersebut
    """

class PromptResponse(BaseModel):
    queries: list[str]
    #thoughts: list[str]

async def main():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

    # make session
    session = SQLAlchemySession(
        "test",
        engine=engine,
        create_tables=True,
    )
    
    agent = Agent(
        name="Prompt_Agent",
        instructions=PROMPT_AGENT_PROMPT,
        tools=[
            FileSearchTool(vector_store_ids=[VS_ID], max_num_results=4),
            FileSearchTool(vector_store_ids=[EXPERIENCE_VS_ID], max_num_results=4)
        ],
        model="gpt-5",
        output_type=PromptResponse,
        model_settings=ModelSettings(tool_choice="required")
        )
    
    with trace("testing agent"):
        result = Runner.run_streamed(
            agent,
            "berikan saya data tamu yang paling sering menginap",
            session=session,
            )
        #print(result.final_output)

        print("=== Run starting ===")

        async for event in result.stream_events():
            # We'll ignore the raw responses event deltas
            if event.type == "raw_response_event":
                continue
            # When the agent updates, print that
            elif event.type == "agent_updated_stream_event":
                print(f"Agent updated: {event.new_agent.name}")
                continue
            # When items are generated, print them
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    print("-- Tool was called")
                elif event.item.type == "tool_call_output_item":
                    print(f"-- Tool output: {event.item.output}")
                elif event.item.type == "message_output_item":
                    print(f"-- Message output:\n {ItemHelpers.text_message_output(event.item)}")
                else:
                    pass  # Ignore other event types

        print("=== Run complete ===")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())