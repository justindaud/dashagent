import os
import asyncio
import json

from agents import Agent, Runner, trace, AgentOutputSchema
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from scripts.experience_func import fetch_experience, ingest_insights_async
from agents_tools.sematicsearch_tool import search_insights_semantic

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'postgresql://' -> 'postgresql+asyncpg://'
    DATABASE_URL = "postgresql+asyncpg://" + DATABASE_URL[len("postgresql://"):]
elif DATABASE_URL.startswith("mysql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'mysql://' -> 'mysql+aiomysql://'
    DATABASE_URL = "mysql+aiomysql://" + DATABASE_URL[len("mysql://"):]
elif DATABASE_URL.startswith("sqlite://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'sqlite:///' -> 'sqlite+aiosqlite:///'
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

class ExperienceDigest(BaseModel):
    """Structured digest returned by Experience Agent.
    Keep it short and actionable for planning/execution."""
    insights: List[str] = []
    patterns: List[str] = []
    preferences: List[str] = []

EXPERIENCE_PROMPT = """
Anda adalah agent yang memiliki tugas untuk:
1. Membaca percakapan historis dengan user dari database dan digest menjadi insight
2. Membaca dan mempelajari experience yang sudah pernah tersimpan
3. Secara selektif menambahkan atau konversikan percakapan menjadi insights untuk diingat

Insights perlu mencakup:
1. Insights: Berkaitan dengan suatu informasi penting yang perlu diingat tetapi bersifat umum
2. Patterns: Berkaitan dengan step-by-step yang perlu diingat. Bisa berupa step-by-step penggunaan agent, query, tools, dll.
3. Preferences: Berkaitan dengan preferensi gaya bahasa, penulisan format, dll.

Spesifikasi setiap poin/list insights:
1. Merupakan kalimat utuh
2. Memuat konteks
3. Consise namun rich
4. Tidak secara eksplisit menyebutkan isi/hasil data

Insights akan secara langsung digunakan oleh prompt agent untuk membuat prompt yang lebih spesifik.
Sehingga orchestrator bisa dengan baik menentukan penggunaan agent analyst atau search.
Sehingga analyst bisa membuat sql query yang tepat.
Sehingga search bisa melakukan pencarian informasi yang tepat.
"""

async def main():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    
    q = f"""
        SELECT 
            s.session_id,
            si.session_id as analyzed_session
        FROM agent_sessions s
        LEFT JOIN session_insights si ON s.session_id = si.session_id
        WHERE s.updated_at = (
            SELECT MAX(updated_at) FROM agent_sessions
        )
        AND si.session_id IS NULL
        """
    
    async with engine.connect() as conn:
        result = await conn.execute(text(q))
        row = result.fetchone()
        session_id = row[0] if row else None

    agent = Agent(
        name="Experience Agent",
        instructions=EXPERIENCE_PROMPT,
        model="gpt-5",
        output_type=AgentOutputSchema(ExperienceDigest),
        tools=[search_insights_semantic]
    )

    sql_session = SQLAlchemySession(session_id=session_id, engine=engine)
    with trace("testing experience agent"):
        experience = fetch_experience(limit=500)
        if "error" in experience:
            print(f"[yellow]No new sessions to analyze: {experience['error']}[/yellow]")
            return
        
        result = await Runner.run(
            agent,
            "Anda akan membaca keseluruhan pecakapan, pahami konteks, buat insights sebagai list dari hal-hal yang perlu diingat, sebutkan table, fields, sql, cara membuat query, link, cara menentukan url, dsb", 
            session=sql_session,)
        
        print("Generated insights:")
        print(f"Insights count: {len(result.final_output.insights)}")
        print(f"Patterns count: {len(result.final_output.patterns)}")
        print(f"Preferences count: {len(result.final_output.preferences)}")
        
        # Store insights to database
        if result.final_output and session_id:
            print("\nStoring insights to database...")
            status = await ingest_insights_async(
                session_id=session_id,
                user_id="test_user",
                insights=result.final_output.insights,
                patterns=result.final_output.patterns,
                preferences=result.final_output.preferences,
                async_engine=engine
            )
            print(f"Storage status: {status}")
        else:
            print("No insights generated or session_id missing")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())