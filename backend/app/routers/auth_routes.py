# backend/app/routers/auth_routes.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.controllers import auth_controller as auth_ctl
from app.db.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from app.schemas.response import ApiResponse
from app.middlewares.middleware import get_current_user
from app.model.user import User
from app.utils.response import success
from app.utils.cookies import set_auth_cookie, clear_auth_cookie

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    result = auth_ctl.login_controller(db, payload.username, payload.password)
    resp = success(message=result["message"], data=LoginResponse(user_id=result["user_id"]), status_code=200)
    set_auth_cookie(resp, result["access_token"])
    return resp

@router.post("/logout")
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = auth_ctl.logout_controller(db, request, current_user)
    resp = success(message=result["message"], data=LogoutResponse(user_id=result["user_id"]), status_code=200)
    if result.get("clear_cookie"):
        clear_auth_cookie(resp)
    return resp
