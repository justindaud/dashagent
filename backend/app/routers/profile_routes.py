# backend/app/routers/profile_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers import profile_controller as profile_ctl
from app.middlewares.middleware import get_current_user
from app.model.user import User
from app.utils.response import success
from app.db.database import get_db
from app.utils.cookies import clear_auth_cookie
from app.schemas.profile import ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["Profile"])

@router.get("/")
def profile(current_user: User = Depends(get_current_user)):
    prof = profile_ctl.profile_controller(current_user)
    return success(message="Profile Fetched Successfully", data=prof, status_code=200)

@router.put("/")
def update_profile( payload: ProfileUpdate,  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = profile_ctl.update_profile_controller(
        db,
        current_user,
        username=payload.username,
        password=payload.password,
        confirm_password=payload.confirm_password,
        full_name=payload.full_name,
    )
    resp = success(
        message=result["message"],
        data={"id": result["id"]},
        status_code=200
    )
    if result.get("bumped"):
        clear_auth_cookie(resp) 
    return resp
