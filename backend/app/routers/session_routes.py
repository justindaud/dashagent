# backend/app/routers/session_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.middlewares.middleware import get_current_user
from app.model.user import User
from app.schemas.session import SessionCreate, SessionOut
from app.controllers import session_controller as ctl
from app.utils.response import success

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

@router.post("/")
def create_session(payload: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sess = ctl.create_session_controller(db, user_id=str(current_user.user_id), title=payload.title)
    return success(message="Session created successfully", data=SessionOut.model_validate(sess), status_code=201)

@router.get("/")
def list_my_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = [
        SessionOut.model_validate(s)
        for s in ctl.list_my_sessions_controller(db, user_id=str(current_user.user_id))
    ]
    return success(message="Sessions list fetched successfully", data=items, status_code=200)

@router.get("/{session_id}")
def get_my_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sess = ctl.get_my_session_controller(db, user_id=str(current_user.user_id), session_id=session_id)
    return success(message="Session detail fetched successfully", data=SessionOut.model_validate(sess), status_code=200)
