# backend/app/repositories/agent_repository.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

def create_run(db: Session, *, session_id: str, run_id: str, user_id: str):
    db.execute(
        text("""
            INSERT INTO agent_runs (session_id, run_id, user_id, status)
            VALUES (:sid, :rid, :uid, 'running')
        """),
        {"sid": session_id, "rid": run_id, "uid": user_id}
    )
    db.commit()

def mark_finished(db: Session, *, run_id: str, ok: bool, error: str | None = None):
    db.execute(
        text("""
            UPDATE agent_runs
               SET status = :st,
                   error = :err,
                   finished_at = :ts
             WHERE run_id = :rid
        """),
        {
            "st": ("succeeded" if ok else "failed"),
            "err": error,
            "ts": datetime.now(timezone.utc),
            "rid": run_id,
        }
    )
    db.commit()

def get_run(db: Session, *, run_id: str):
    row = db.execute(
        text("""
            SELECT session_id, run_id, user_id, status, error, started_at, finished_at
              FROM agent_runs
             WHERE run_id = :rid
        """),
        {"rid": run_id}
    ).mappings().first()
    return dict(row) if row else None


def list_messages_for_session(db: Session, *, session_id: str, run_id: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, session_id, run_id, message_data, created_at
        FROM agent_messages
        WHERE session_id = :sid
    """
    params = {"sid": session_id}

    if run_id:
        sql += " AND run_id = :rid"
        params["rid"] = run_id

    sql += " ORDER BY id ASC"
    if limit and limit > 0:
        sql += " LIMIT :limit"
        params["limit"] = limit

    rows = db.execute(text(sql), params).mappings().all()
    out: List[Dict[str, Any]] = []
    for r in rows:
        md = r["message_data"]
        if isinstance(md, str):
            import json
            try:
                md_parsed = json.loads(md)
            except Exception:
                md_parsed = {"text": md}
        else:
            md_parsed = md

        out.append({
            "id": int(r["id"]),
            "session_id": r["session_id"],
            "run_id": r.get("run_id"),
            "message": md_parsed,
            "created_at": r.get("created_at"),
        })
    return out