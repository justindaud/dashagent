# backend/app/repositories/session_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from app.model.session import AgentSession

def get_by_id_and_user(db: Session, session_id: str, user_id: str) -> Optional[AgentSession]:
    return (
        db.query(AgentSession)
        .filter(and_(AgentSession.session_id == session_id, AgentSession.user_id == user_id))
        .first()
    )

def get_by_id(db: Session, session_id: str) -> Optional[AgentSession]:
    return db.query(AgentSession).filter(AgentSession.session_id == session_id).first()

def exists_for_user(db: Session, session_id: str, user_id: str) -> bool:
    return (
        db.query(AgentSession.session_id)
        .filter(and_(AgentSession.session_id == session_id, AgentSession.user_id == user_id))
        .first()
        is not None
    )

def _default_title_for_user(db: Session, user_id: str) -> str:
    total = (
        db.query(AgentSession)
        .filter(AgentSession.user_id == user_id)
        .count()
    )
    return f"New chat {total + 1}"

def create_for_user(db: Session, *, session_id: str, user_id: str, title: Optional[str]) -> AgentSession:
    obj = AgentSession(session_id=session_id, user_id=user_id, title=title or _default_title_for_user(db, user_id))
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

def ensure_exists_on_run(db: Session, *, session_id: str, user_id: str) -> AgentSession:
    found = get_by_id_and_user(db, session_id, user_id)
    if found:
        return found
    try:
        return create_for_user(db, session_id=session_id, user_id=user_id, title=None)
    except IntegrityError:
        db.rollback()
        again = get_by_id_and_user(db, session_id, user_id)
        if again:
            return again
        raise

def update_title(db: Session, *, session_id: str, user_id: str, new_title: str) -> AgentSession:
    sess = get_by_id_and_user(db, session_id, user_id)
    if not sess:
        return None
    sess.title = new_title.strip()
    db.commit()
    db.refresh(sess)
    return sess

def predict_next_default_title(db: Session, *, user_id: str) -> str:
    return _default_title_for_user(db, user_id)
