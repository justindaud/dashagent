# backend/app/routers/agent_routes.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.middlewares.middleware import get_current_user
from app.model.user import User
from app.schemas.agent import PromptIn
from app.controllers import session_controller as ctl
from app.utils.response import success

router = APIRouter(tags=["Agent"])

@router.post("/api/sessions/{session_id}/run")
def send_prompt(
    session_id: str,
    payload: PromptIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = ctl.start_agent_controller(
        db,
        background_tasks=background_tasks,
        current_user=current_user,
        session_id=session_id,
        user_input=payload.user_input,
    )
    return success(message=result["message"], data={"session_id": result["session_id"], "user_id": result["user_id"], "role": result["role"]}, status_code=202)
