import asyncio
import uuid
from datetime import datetime
from typing import Optional
from agents import Runner
from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine
import os

'''
def generate_session_id(user_id: Optional[str] = None) -> str:
    """Generate automatic session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_uuid = str(uuid.uuid4())[:8]
    
    if user_id:
        return f"user_{user_id}_session_{timestamp}_{session_uuid}"
    else:
        return f"session_{timestamp}_{session_uuid}"


# === SQLAlchemy engine & session factory ===
# Normalize DATABASE_URL to an **async** driver flavor if user supplies a sync DSN

DATABASE_URL = os.getenv("DATABASE_URL")

# If user provided a sync URL (e.g., postgresql:// uses psycopg2), rewrite to async
if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'postgresql://' -> 'postgresql+asyncpg://'
    DATABASE_URL = "postgresql+asyncpg://" + DATABASE_URL[len("postgresql://"):]
elif DATABASE_URL.startswith("mysql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'mysql://' -> 'mysql+aiomysql://'
    DATABASE_URL = "mysql+aiomysql://" + DATABASE_URL[len("mysql://"):]
elif DATABASE_URL.startswith("sqlite://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'sqlite:///' -> 'sqlite+aiosqlite:///'
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)


engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)


def make_sa_session(session_id: str) -> SQLAlchemySession:
    # create_tables=True is convenient for dev; in production use migrations
    return SQLAlchemySession(
        session_id=session_id,
        engine=engine,
        create_tables=True,
    )

async def run_with_session_streamed(
    orchestrator,
    user_input: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Run agent with session management (streaming events).
    Returns a RunResultStreaming handle; consume with:
        async for event in result.stream_events():
            ...
    """
    if not session_id:
        session_id = generate_session_id(user_id)

    session = make_sa_session(session_id)
    # NOTE: run_streamed returns a streaming handle (do not await here)
    result = Runner.run_streamed(
        orchestrator,
        user_input,
        session=session,
    )
    return result
'''