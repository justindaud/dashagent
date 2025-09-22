# backend/app/controllers/agent_controller.py
import uuid
from collections import defaultdict
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories import session_repository as srepo
from app.model.user import User
from agentv2.agent import DashboardAgent
from app.repositories import agent_repository as runrepo

async def start_agent_controller(db: Session, *, current_user: User, session_id: str, user_input: str) -> dict:
    user_id   = str(current_user.user_id)
    user_role = current_user.role.value

    sess = srepo.get_by_id_and_user(db, session_id=session_id, user_id=user_id)

    if not sess:
        prealloc = srepo.get_prealloc_by_user(db, session_id=session_id, user_id=user_id)
        if not prealloc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or not owned by you")

        if prealloc.get("is_active"):
            raise HTTPException(status_code=409, detail="Session already consumed")

        try:
            srepo.create_for_user(db, session_id=session_id, user_id=user_id, title=None)
        except IntegrityError:
            db.rollback()
            again = srepo.get_by_id_and_user(db, session_id=session_id, user_id=user_id)
            if not again:
                raise
        srepo.mark_consumed(db, session_id=session_id)
    else:
        try:
            srepo.touch_last_used(db, session_id)
        except Exception:
            pass

    run_id = uuid.uuid4().hex
    runrepo.create_run(db, session_id=session_id, run_id=run_id, user_id=user_id)

    try:
        result = await DashboardAgent.run_and_collect(
            session_id=session_id,
            user_id=user_id,
            user_input=user_input,
            user_role=user_role,
            run_id=run_id,
        )
        runrepo.mark_finished(db, run_id=run_id, ok=True)
    except Exception as e:
        runrepo.mark_finished(db, run_id=run_id, ok=False, error=str(e))
        raise

    run_row = runrepo.get_run(db, run_id=run_id)
    return {
        "message": "Agent finished",
        "session_id": result["session_id"],
        "user_id": result["user_id"],
        "role": result["role"],
        "run_id": result["run_id"],
        "messages": result["messages"],
        "run": run_row,
    }

_SEED_SKIP_SUBSTRINGS = [
    "Anda akan membaca keseluruhan",
    "baca keseluruhan percakapan",
    "you will read the entire",
    "read the conversation",
    "experience agent",
]

def _is_seedish_user_prompt(text: str) -> bool:
    t = (text or "").strip()
    low = t.lower()
    if any(s.lower() in low for s in _SEED_SKIP_SUBSTRINGS):
        return True
    if len(t) <= 80 and t.endswith("..."):
        return True
    return False

def _extract_user_prompt(msg_obj: dict) -> Optional[str]:
    if not isinstance(msg_obj, dict):
        return None
    role = msg_obj.get("role")
    content = msg_obj.get("content")
    if role == "user" and isinstance(content, str) and content.strip():
        if _is_seedish_user_prompt(content):
            return None
        return content
    return None

def _looks_like_insights_payload(txt: str) -> bool:
    if not isinstance(txt, str):
        return False
    s = txt.strip()
    if not s:
        return False
    if s.startswith("{"):
        low = s.lower()
        if '"insights"' in low or '"patterns"' in low or '"preferences"' in low:
            return True
    low = s.lower()
    return ('"insights"' in low and '"patterns"' in low) or ('"preferences"' in low)

def _extract_assistant_output_text(msg_obj: dict) -> Optional[str]:
    if not isinstance(msg_obj, dict):
        return None
    content = msg_obj.get("content")
    if not isinstance(content, list):
        return None

    chosen = None
    for part in content:
        if isinstance(part, dict) and part.get("type") == "output_text":
            txt = part.get("text")
            if isinstance(txt, str) and txt.strip():
                if _looks_like_insights_payload(txt):
                    continue
                chosen = txt
    return chosen


def list_session_messages_compact_controller(db: Session, *, current_user: User, session_id: str) -> dict:
    user_id = str(current_user.user_id)

    sess = srepo.get_by_id_and_user(db, session_id=session_id, user_id=user_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found or not owned by you")

    rows = runrepo.list_messages_for_session(db, session_id=session_id, run_id=None, limit=None)

    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        rid = r.get("run_id") or "(no-run)"
        groups[rid].append(r)

    runs_out_unsorted: List[Dict[str, Any]] = []

    for rid, msgs in groups.items():
        msgs.sort(key=lambda m: int(m["id"]))

        prompt_item = None
        prompt_content = None

        for item in msgs:
            up = _extract_user_prompt(item.get("message"))
            if up:
                prompt_item = item
                prompt_content = up
                break

        if prompt_item is None:
            for item in msgs:
                mo = item.get("message")
                if isinstance(mo, dict) and mo.get("role") == "user":
                    raw = mo.get("content")
                    if isinstance(raw, str) and raw.strip():
                        low = raw.lower()
                        looks_like_prompt = (
                            low.startswith("user prompt:") or
                            low.startswith("prompt:") or
                            "intent:" in low or
                            "step-by-step" in low
                        )
                        if looks_like_prompt and not _is_seedish_user_prompt(raw):
                            prompt_item = item
                            prompt_content = raw
                            break

        output_item = None
        output_content = None
        for item in reversed(msgs):
            at = _extract_assistant_output_text(item.get("message"))
            if at:
                output_item = item
                output_content = at
                break

        compact_msgs: List[Dict[str, Any]] = []

        if prompt_item and isinstance(prompt_content, str) and prompt_content.strip():
            compact_msgs.append({
                "id": prompt_item["id"],
                "session_id": prompt_item["session_id"],
                "kind": "user_prompt",
                "content": prompt_content,
                "created_at": prompt_item.get("created_at"),
            })

        if output_item and isinstance(output_content, str) and output_content.strip():
            compact_msgs.append({
                "id": output_item["id"],
                "session_id": output_item["session_id"],
                "kind": "assistant_output",
                "content": output_content,
                "created_at": output_item.get("created_at"),
            })

        if not compact_msgs:
            continue

        order_key = int(msgs[0]["id"]) if msgs else 10**18

        runs_out_unsorted.append({
            "run_id": None if rid == "(no-run)" else rid,
            "messages": compact_msgs,
            "_order_key": order_key,
        })

    runs_out = sorted(runs_out_unsorted, key=lambda x: x["_order_key"])
    for r in runs_out:
        r.pop("_order_key", None)

    return {
        "session_id": session_id,
        "runs": runs_out,
    }
