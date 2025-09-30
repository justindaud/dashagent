import os
from typing import Any, Dict, Optional, List
from sqlalchemy import create_engine, text, func
import openai
from dotenv import load_dotenv

load_dotenv()

def fetch_experience(
    *,
    limit
    ) -> Dict[str, Any]:
    """
    Get latest session from agent_messages, then fetch the latest session transcript
    """
    import json

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    '''
            WHERE session_id NOT IN (
            SELECT DISTINCT session_id 
            FROM session_insights
        )
    '''
    engine = create_engine(db_url, future=True, pool_pre_ping=True)
    q = f"""
    SELECT id, session_id, message_data, created_at
    FROM agent_messages
    WHERE session_id = (
        SELECT session_id 
        FROM agent_messages 
        ORDER BY created_at DESC 
        LIMIT 1
    )
    ORDER BY created_at ASC, id ASC
    LIMIT {limit}
    """
    
    with engine.connect() as conn:  # type: Connection
        cur = conn.execute(text(q))
        rows = cur.fetchall()

    if not rows:
        return {"error": "No sessions found"}

    session_id = rows[0][1]

    def parse_message_record(msg_json: str) -> Dict[str, Any]:
        try:
            d = json.loads(msg_json)
        except Exception:
            return {"role": None, "content": msg_json}
        t = d.get("type")
        # Standard assistant/user message
        if t == "message":
            role = d.get("role") or "assistant"
            content = d.get("content") or []
            texts = []
            for c in content:
                if isinstance(c, dict) and c.get("type") in ("output_text", "input_text", "text"):
                    texts.append(c.get("text", ""))
            return {"role": role, "content": "\n".join(texts)}
        # Tool call and outputs collapsed into content for context
        if t == "function_call":
            return {"role": "tool_call", "content": f"{d.get('name','tool')}({d.get('arguments','')})"}
        if t == "function_call_output":
            return {"role": "tool_output", "content": str(d.get("output", ""))}
        return {"role": d.get("role"), "content": d.get("content")}
    
    out_rows: List[Dict[str, Any]] = []
    for rid, sid, msg_json, created_at in rows:
        parsed = parse_message_record(msg_json)
        out_rows.append({
            "session_id": sid,
            "role": parsed.get("role"),
            "content": parsed.get("content"),
            "created_at": created_at.isoformat(),
            "id": rid,
        })
    return {
        "session_id": session_id,
        "transcript": out_rows,
        "message_count": len(out_rows)
    }

def ingest_insights(
    *,
    session_id: str,
    user_id: Optional[str] = None,
    insights: List[str],
    patterns: Optional[List[str]] = None,
    preferences: Optional[List[str]] = None,
    engine=None
    ) -> str:
    """
    Upload experience to database
    """
    if engine is None:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL not set")
        engine = create_engine(db_url, future=True, pool_pre_ping=True)

    experience_data = []
    
    # insert insights
    for insight in insights:
        experience_data.append({
            "session_id": session_id,
            "user_id": user_id,
            "insight_type": "insight",
            "insight_content": insight,
        })
    
    # insert patterns
    if patterns:
        for pattern in patterns:
            experience_data.append({
                "session_id": session_id,
                "user_id": user_id,
                "insight_type": "pattern",
                "insight_content": pattern,
            })
    
    # insert preferences
    if preferences:
        for preference in preferences:
            experience_data.append({
                "session_id": session_id,
                "user_id": user_id,
                "insight_type": "preference",
                "insight_content": preference,
            })
    
    # Bulk insert
    try:
        # Check if engine is async or sync
        if hasattr(engine, 'connect') and hasattr(engine.connect(), '__aenter__'):
            # Async engine - use async context manager
            import asyncio
            async def async_insert():
                async with engine.connect() as conn:
                    # Create table if not exists
                    await conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS session_insights (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(255) NOT NULL,
                            user_id VARCHAR(255),
                            insight_type VARCHAR(50) NOT NULL,
                            insight_content TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    await conn.commit()
                    
                    # Insert insights
                    for data in experience_data:
                        await conn.execute(text("""
                            INSERT INTO session_insights 
                            (session_id, user_id, insight_type, insight_content, created_at)
                            VALUES (:session_id, :user_id, :insight_type, :insight_content, CURRENT_TIMESTAMP)
                        """), data)
                    await conn.commit()
            
            # Run async function
            asyncio.run(async_insert())
        else:
            # Sync engine - use sync context manager
            with engine.connect() as conn:
                # Create table if not exists
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS session_insights (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255) NOT NULL,
                        user_id VARCHAR(255),
                        insight_type VARCHAR(50) NOT NULL,
                        insight_content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                
                # Insert insights
                for data in experience_data:
                    conn.execute(text("""
                        INSERT INTO session_insights 
                        (session_id, user_id, insight_type, insight_content, created_at)
                        VALUES (:session_id, :user_id, :insight_type, :insight_content, CURRENT_TIMESTAMP)
                    """), data)
                conn.commit()
        
        total_insights = len(experience_data)
        return f"success: {total_insights}"

    except Exception as e:
        return f"Failed to store insights: {str(e)}"


# Async variant for use with SQLAlchemy AsyncEngine
async def ingest_insights_async(
    *,
    session_id: str,
    user_id: Optional[str] = None,
    insights: List[str],
    patterns: Optional[List[str]] = None,
    preferences: Optional[List[str]] = None,
    async_engine=None,
) -> str:
    """
    Upload experience to database using AsyncEngine with embeddings.
    """
    from sqlalchemy.ext.asyncio import AsyncEngine

    if async_engine is None or not isinstance(async_engine, AsyncEngine):
        raise RuntimeError("ingest_insights_async requires a SQLAlchemy AsyncEngine passed as async_engine")

    # Initialize OpenAI client for embeddings
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return "Failed to store insights (async): OPENAI_API_KEY not set"
    
    client = openai.OpenAI(api_key=openai_api_key)
    experience_data: List[Dict[str, Any]] = []

    # Helper function to generate embedding
    def generate_embedding(text: str) -> str:
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding_list = response.data[0].embedding
            # Convert list to PostgreSQL VECTOR format string
            return str(embedding_list)
        except Exception as e:
            print(f"Warning: Failed to generate embedding for text: {str(e)}")
            return None

    # Process insights with embeddings
    for insight in insights:
        embedding = generate_embedding(insight)
        experience_data.append({
            "session_id": session_id,
            "user_id": user_id,
            "insight_type": "insight",
            "insight_content": insight,
            "embedding": embedding
        })

    # Process patterns with embeddings
    if patterns:
        for pattern in patterns:
            embedding = generate_embedding(pattern)
            experience_data.append({
                "session_id": session_id,
                "user_id": user_id,
                "insight_type": "pattern",
                "insight_content": pattern,
                "embedding": embedding
            })

    # Process preferences with embeddings
    if preferences:
        for preference in preferences:
            embedding = generate_embedding(preference)
            experience_data.append({
                "session_id": session_id,
                "user_id": user_id,
                "insight_type": "preference",
                "insight_content": preference,
                "embedding": embedding
            })

    try:
        async with async_engine.begin() as conn:
            # Ensure table exists with embedding column
            await conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS session_insights (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    insight_type VARCHAR(50) NOT NULL,
                    insight_content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))

            # Create index for efficient similarity search if not exists
            await conn.execute(text(
                """
                CREATE INDEX IF NOT EXISTS session_insights_embedding_idx 
                ON session_insights 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
                """
            ))

            # Insert data with embeddings
            for data in experience_data:
                await conn.execute(text(
                    """
                    INSERT INTO session_insights 
                    (session_id, user_id, insight_type, insight_content, embedding, created_at)
                    VALUES (:session_id, :user_id, :insight_type, :insight_content, :embedding, CURRENT_TIMESTAMP)
                    """
                ), data)

        return f"success: {len(experience_data)}"
    except Exception as e:
        return f"Failed to store insights (async): {str(e)}"
