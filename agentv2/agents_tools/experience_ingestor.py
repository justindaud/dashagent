from agents import function_tool
import os
import json
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text

@function_tool
def fetch_session_transcript(session_id: str) -> str:
    """
    Fetch transcript for a specific session ID.
    
    Args:
        session_id: Session ID to fetch transcript for
        
    Returns:
        JSON string containing session transcript
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return json.dumps({"error": "DATABASE_URL not set"})
    
    try:
        engine = create_engine(db_url, future=True, pool_pre_ping=True)
        
        query = """
        SELECT id, session_id, message_data, created_at
        FROM agent_messages
        WHERE session_id = :session_id
        ORDER BY created_at ASC, id ASC
        LIMIT 500
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query), {"session_id": session_id})
            rows = result.fetchall()
        
        if not rows:
            return json.dumps({"error": f"No messages found for session {session_id}"})
        
        def parse_message_record(msg_json: str) -> Dict[str, Any]:
            try:
                d = json.loads(msg_json)
            except Exception:
                return {"role": None, "content": msg_json}
            
            t = d.get("type")
            if t == "message":
                role = d.get("role") or "assistant"
                content = d.get("content") or []
                texts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") in ("output_text", "input_text", "text"):
                        texts.append(c.get("text", ""))
                return {"role": role, "content": "\n".join(texts)}
            elif t == "function_call":
                return {"role": "tool_call", "content": f"{d.get('name','tool')}({d.get('arguments','')})"}
            elif t == "function_call_output":
                return {"role": "tool_output", "content": str(d.get("output", ""))}
            return {"role": d.get("role"), "content": d.get("content")}
        
        transcript = []
        for rid, sid, msg_json, created_at in rows:
            parsed = parse_message_record(msg_json)
            transcript.append({
                "session_id": sid,
                "role": parsed.get("role"),
                "content": parsed.get("content"),
                "created_at": created_at.isoformat(),
                "id": rid,
            })
        
        return json.dumps({
            "session_id": session_id,
            "transcript": transcript,
            "message_count": len(transcript)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch transcript: {str(e)}"})

@function_tool
def ingest_experience_DB(
    session_id: str,
    user_id: Optional[str] = None,
    insights: List[str] = None,
    patterns: List[str] = None,
    preferences: List[str] = None
    ) -> str:
    """
    Upload experience insights to database.
    
    Args:
        session_id: Session ID
        user_id: User ID (optional)
        insights: List of insights
        patterns: List of patterns
        preferences: List of preferences
        
    Returns:
        Success message or error
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "Error: DATABASE_URL not set"
    
    try:
        engine = create_engine(db_url, future=True, pool_pre_ping=True)
        
        experience_data = []
        
        # Insert insights
        if insights:
            for insight in insights:
                experience_data.append({
                    "session_id": session_id,
                    "user_id": user_id,
                    "insight_type": "insight",
                    "insight_content": insight,
                })
        
        # Insert patterns
        if patterns:
            for pattern in patterns:
                experience_data.append({
                    "session_id": session_id,
                    "user_id": user_id,
                    "insight_type": "pattern",
                    "insight_content": pattern,
                })
        
        # Insert preferences
        if preferences:
            for preference in preferences:
                experience_data.append({
                    "session_id": session_id,
                    "user_id": user_id,
                    "insight_type": "preference",
                    "insight_content": preference,
                })
        
        # Bulk insert
        with engine.connect() as conn:
            for data in experience_data:
                conn.execute(text("""
                    INSERT INTO session_insights 
                    (session_id, user_id, insight_type, insight_content, created_at)
                    VALUES (:session_id, :user_id, :insight_type, :insight_content, CURRENT_TIMESTAMP)
                """), data)
            conn.commit()
        
        return f"Successfully stored {len(experience_data)} insights"
        
    except Exception as e:
        return f"Error storing insights: {str(e)}"

# Export the functions directly for use in agents
# fetch_session_transcript and ingest_experience_DB are already available as functions
