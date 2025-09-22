# backend/app/controllers/session_controller.py
from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.repositories import session_repository as srepo
from app.utils.session_id import generate_session_id
from app.model.session import AgentSession
from app.model.user import User
from agentv2.agent import DashboardAgent

def create_session_controller(db: Session, *, user_id: str) -> AgentSession:
    for _ in range(5):
        sid = generate_session_id(user_id)
        if not srepo.exists_for_user(db, sid, user_id):
            break
    else:
        raise HTTPException(status_code=500, detail="Failed to generate session id")

    predicted_title = srepo.predict_next_default_title(db, user_id=user_id)
    return AgentSession(session_id=sid, user_id=user_id, title=predicted_title)

def list_my_sessions_controller(db: Session, *, user_id: str):
    return srepo.list_for_user(db, user_id)

def get_my_session_controller(db: Session, *, user_id: str, session_id: str) -> AgentSession:
    sess = srepo.get_by_id_and_user(db, session_id, user_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return sess

def start_agent_controller(db: Session, *, background_tasks: BackgroundTasks, current_user: User, session_id: str, user_input: str) -> dict:
    user_id = str(current_user.user_id)
    user_role = current_user.role.value

    existing = srepo.get_by_id(db, session_id)
    if existing and existing.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    sess = srepo.ensure_exists_on_run(db, session_id=session_id, user_id=user_id)

    background_tasks.add_task(DashboardAgent.run_background, session_id, user_id, user_input, user_role)
    return {"message": "Agent started", "session_id": sess.session_id, "user_id": user_id, "role": user_role}

def update_title_controller(
    db: Session, *, current_user: User, session_id: str, new_title: str
) -> AgentSession:
    user_id = str(current_user.user_id)
    sess = srepo.update_title(db, session_id=session_id, user_id=user_id, new_title=new_title)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess
