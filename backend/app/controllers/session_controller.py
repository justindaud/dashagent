# backend/app/controllers/session_controller.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict

from app.utils.session_id import generate_session_id
from app.model.session import AgentSession
from app.repositories import session_repository as srepo
from app.model.user import User

def create_session_controller(db: Session, *, user_id: str) -> Dict[str, str]:
    for _ in range(5):
        sid = generate_session_id(user_id)
        if not srepo.get_by_id(db, sid) and not srepo.get_prealloc(db, session_id=sid):
            srepo.create_prealloc(db, session_id=sid, user_id=user_id)
            break
    else:
        raise HTTPException(status_code=500, detail="Failed to generate session id")

    predicted_title = srepo.predict_next_default_title(db, user_id=user_id)
    return {"session_id": sid, "title_suggestion": predicted_title}

def list_my_sessions_controller(db: Session, *, user_id: str):
    return srepo.list_for_user(db, user_id)

def get_my_session_controller(db: Session, *, user_id: str, session_id: str) -> AgentSession:
    sess = srepo.get_by_id_and_user(db, session_id, user_id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return sess

def update_title_controller(db: Session, *, current_user: User, session_id: str, new_title: str) -> AgentSession:
    user_id = str(current_user.user_id)
    sess = srepo.update_title(db, session_id=session_id, user_id=user_id, new_title=new_title)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess
