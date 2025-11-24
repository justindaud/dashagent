# backend/app/db_init_sync.py
from sqlalchemy import text
from sqlalchemy.engine import Engine

SESSION_INSIGHTS_IVFFLAT_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS session_insights_embedding_idx 
ON session_insights 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100)
"""

def init_db_sync(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        
        conn.execute(text(SESSION_INSIGHTS_IVFFLAT_INDEX_SQL))
