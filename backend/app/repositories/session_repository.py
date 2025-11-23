# app/repositories/session_repository.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

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

def create_prealloc(db: Session, *, session_id: str, user_id: str) -> Dict[str, Any]:
    db.execute(
        text("""
            INSERT INTO agent_session_prealloc (session_id, user_id, is_active)
            VALUES (:sid, :uid, FALSE)
        """),
        {"sid": session_id, "uid": user_id},
    )
    db.commit()
    return {"session_id": session_id, "user_id": user_id}

def get_prealloc(db: Session, *, session_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text("""
            SELECT session_id, user_id, is_active, created_at, consumed_at
            FROM agent_session_prealloc
            WHERE session_id = :sid
            LIMIT 1
        """),
        {"sid": session_id},
    ).mappings().first()
    return dict(row) if row else None

def get_prealloc_by_user(db: Session, *, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text("""
            SELECT session_id, user_id, is_active, created_at, consumed_at
            FROM agent_session_prealloc
            WHERE session_id = :sid AND user_id = :uid
            LIMIT 1
        """),
        {"sid": session_id, "uid": user_id},
    ).mappings().first()
    return dict(row) if row else None

def mark_consumed(db: Session, *, session_id: str) -> None:
    db.execute(
        text("""
            UPDATE agent_session_prealloc
               SET is_active = TRUE,
                   consumed_at = NOW()
             WHERE session_id = :sid
        """),
        {"sid": session_id},
    )
    db.commit()

def touch_last_used(db: Session, session_id: str) -> None:
    db.execute(text("UPDATE agent_sessions SET updated_at = NOW() WHERE session_id = :sid"), {"sid": session_id})
    db.commit()

def cleanup_preallocs(db: Session, *, ttl_unconsumed_minutes: int, ttl_consumed_minutes: int) -> Dict[str, int]:
    res1 = db.execute(
        text("""
            WITH del AS (
                DELETE FROM agent_session_prealloc
                 WHERE is_active = FALSE
                   AND created_at < (NOW() AT TIME ZONE 'utc') - (:ttl_unconsumed || ' minutes')::interval
                RETURNING 1
            )
            SELECT COUNT(*) AS n FROM del
        """),
        {"ttl_unconsumed": ttl_unconsumed_minutes},
    ).mappings().first()
    deleted_unconsumed = int(res1["n"]) if res1 and res1["n"] is not None else 0

    res2 = db.execute(
        text("""
            WITH del AS (
                DELETE FROM agent_session_prealloc
                 WHERE is_active = TRUE
                   AND consumed_at IS NOT NULL
                   AND consumed_at < (NOW() AT TIME ZONE 'utc') - (:ttl_consumed || ' minutes')::interval
                RETURNING 1
            )
            SELECT COUNT(*) AS n FROM del
        """),
        {"ttl_consumed": ttl_consumed_minutes},
    ).mappings().first()
    deleted_consumed = int(res2["n"]) if res2 and res2["n"] is not None else 0

    db.commit()
    return {
        "deleted_unconsumed": deleted_unconsumed,
        "deleted_consumed": deleted_consumed,
        "deleted_total": deleted_unconsumed + deleted_consumed,
    }