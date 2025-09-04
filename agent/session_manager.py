import asyncio
import uuid
from datetime import datetime
from typing import Optional
from agents import SQLiteSession, Runner

def generate_session_id(user_id: Optional[str] = None) -> str:
    """Generate automatic session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_uuid = str(uuid.uuid4())[:8]
    
    if user_id:
        return f"user_{user_id}_session_{timestamp}_{session_uuid}"
    else:
        return f"session_{timestamp}_{session_uuid}"

async def run_with_session(
    orchestrator,
    user_input: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> str:
    """Run agent with session management using SQLiteSession"""
    
    # Auto-generate session ID if not provided
    if not session_id:
        session_id = generate_session_id(user_id)
    
    # Create SQLite session (simpler, no database setup needed)
    session = SQLiteSession(
        session_id=session_id,
        db_path="dashagent_sessions.db"
    )
    
    try:
        # Run agent with session
        result = await Runner.run(
            orchestrator,
            user_input,
            session=session
        )
        
        return result.content
        
    except Exception as e:
        print(f"Error running agent: {e}")
        return f"Error: {str(e)}"

# Test function
async def test_session():
    """Test session functionality"""
    from agents_team.orchestrator import orchestrator
    
    # Test auto-generated session
    result = await run_with_session(
        orchestrator,
        "Test auto session",
        user_id="user_123"
    )
    print(f"Auto session result: {result}")

if __name__ == "__main__":
    asyncio.run(test_session())
