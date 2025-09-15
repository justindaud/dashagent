# app/utils/session_id.py
import uuid
from datetime import datetime

def generate_session_id(user_id: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short = str(uuid.uuid4())[:8]
    return f"user_{user_id}_session_{ts}_{short}"
