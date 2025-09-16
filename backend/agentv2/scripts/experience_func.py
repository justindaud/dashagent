import os
from typing import Any, Dict, Optional, List
from sqlalchemy import create_engine, text, func

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
    Upload experience to database using AsyncEngine.
    """
    from sqlalchemy.ext.asyncio import AsyncEngine

    if async_engine is None or not isinstance(async_engine, AsyncEngine):
        raise RuntimeError("ingest_insights_async requires a SQLAlchemy AsyncEngine passed as async_engine")

    experience_data: List[Dict[str, Any]] = []

    for insight in insights:
        experience_data.append({
            "session_id": session_id,
            "user_id": user_id,
            "insight_type": "insight",
            "insight_content": insight,
        })

    if patterns:
        for pattern in patterns:
            experience_data.append({
                "session_id": session_id,
                "user_id": user_id,
                "insight_type": "pattern",
                "insight_content": pattern,
            })

    if preferences:
        for preference in preferences:
            experience_data.append({
                "session_id": session_id,
                "user_id": user_id,
                "insight_type": "preference",
                "insight_content": preference,
            })

    try:
        async with async_engine.begin() as conn:
            # Ensure table exists
            await conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS session_insights (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    insight_type VARCHAR(50) NOT NULL,
                    insight_content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))

            for data in experience_data:
                await conn.execute(text(
                    """
                    INSERT INTO session_insights 
                    (session_id, user_id, insight_type, insight_content, created_at)
                    VALUES (:session_id, :user_id, :insight_type, :insight_content, CURRENT_TIMESTAMP)
                    """
                ), data)

        return f"success: {len(experience_data)}"
    except Exception as e:
        return f"Failed to store insights (async): {str(e)}"
