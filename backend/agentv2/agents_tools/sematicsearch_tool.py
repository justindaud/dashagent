# agents_tools/semantic_search_tool.py
from agents import function_tool
import os
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
import openai
from dotenv import load_dotenv

load_dotenv()

@function_tool
def search_insights_semantic(
    query: str,
    user_id: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.7
) -> str:
    """
    Search session insights using semantic similarity based on embeddings.
    
    Args:
        query: Search query text
        user_id: Optional user ID to filter results
        limit: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        JSON string containing matching insights with similarity scores
    """
    db_url = os.getenv("DATABASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not db_url:
        return json.dumps({"error": "DATABASE_URL not set"})
    if not openai_api_key:
        return json.dumps({"error": "OPENAI_API_KEY not set"})
    
    try:
        # Generate embedding for query
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding
        query_embedding_str = str(query_embedding)  # Convert to string format for PostgreSQL
        
        # Build SQL query with SQLAlchemy style parameters
        base_query = """
        SELECT 
            id,
            session_id,
            user_id,
            insight_type,
            insight_content,
            created_at,
            1 - (embedding <=> :query_embedding::vector) as similarity
        FROM session_insights 
        WHERE embedding IS NOT NULL
        """
        
        params = {
            "query_embedding": query_embedding_str,
            "similarity_threshold": similarity_threshold,
            "limit": limit
        }
        
        # Add user filter if specified
        if user_id:
            base_query += " AND user_id = :user_id"
            params["user_id"] = user_id
        
        # Add similarity threshold and ordering
        base_query += """
        AND 1 - (embedding <=> :query_embedding::vector) >= :similarity_threshold
        ORDER BY similarity DESC
        LIMIT :limit
        """
        
        # Execute query using raw SQL approach to avoid parameter style conflicts
        engine = create_engine(db_url, future=True, pool_pre_ping=True)
        with engine.connect() as conn:
            # Use raw SQL with manual parameter substitution for vector operations
            final_query = base_query.replace(':query_embedding', f"'{query_embedding_str}'")
            final_query = final_query.replace(':similarity_threshold', str(similarity_threshold))
            final_query = final_query.replace(':limit', str(limit))
            if user_id:
                final_query = final_query.replace(':user_id', f"'{user_id}'")
            
            result = conn.execute(text(final_query))
            rows = result.fetchall()
        
        if not rows:
            return json.dumps({
                "query": query,
                "results": [],
                "total_found": 0
            })
        
        # Format results
        insights = []
        for row in rows:
            insights.append({
                "id": row[0],
                "session_id": row[1],
                "user_id": row[2],
                "insight_type": row[3],
                "insight_content": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "similarity_score": round(float(row[6]), 3)
            })
        
        return json.dumps({
            "query": query,
            "results": insights,
            "total_found": len(insights)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Semantic search failed: {str(e)}"})