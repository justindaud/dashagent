# backend/app/repositories/session_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.model.session import AgentSession

def get_by_id_and_user(db: Session, session_id: str, user_id: str) -> Optional[AgentSession]:
    return (
        db.query(AgentSession)
        .filter(and_(AgentSession.session_id == session_id, AgentSession.user_id == user_id))
        .first()
    )

def exists_for_user(db: Session, session_id: str, user_id: str) -> bool:
    return (
        db.query(AgentSession.session_id)
        .filter(and_(AgentSession.session_id == session_id, AgentSession.user_id == user_id))
        .first()
        is not None
    )

def create_for_user(db: Session, *, session_id: str, user_id: str, title: Optional[str]) -> AgentSession:
    obj = AgentSession(session_id=session_id, user_id=user_id, title=title or None)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_for_user(db: Session, user_id: str) -> List[AgentSession]:
    q = (
        db.query(AgentSession)
        .filter(AgentSession.user_id == user_id)
        .order_by(AgentSession.created_at.desc())
    )
    return q.all()