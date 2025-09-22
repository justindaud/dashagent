# backend/app/routers/agent_routes.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.middlewares.middleware import get_current_user
from app.model.user import User
from app.schemas.agent import PromptIn
from app.controllers import agent_controller as atl
from app.utils.response import success

router = APIRouter(tags=["Agent"])

@router.post("/api/sessions/{session_id}/run")
async def send_prompt(
    session_id: str,
    payload: PromptIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await atl.start_agent_controller(
        db=db,
        current_user=current_user,
        session_id=session_id,
        user_input=payload.user_input,
    )
    return success(message=data["message"], data=[data], status_code=200)

@router.get("/api/sessions/{session_id}/messages")
def list_session_messages_compact(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = atl.list_session_messages_compact_controller(
        db=db,
        current_user=current_user,
        session_id=session_id,
    )
    return success(message="Session messages fetched", data=data, status_code=200)

