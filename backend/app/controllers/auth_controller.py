# backend/app/controllers/auth_controller.py
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from app.repositories import auth_repository as auth_repo
from app.utils.security import create_access_token, decode_token
from app.config.settings import settings
from app.model.user import User
from app.utils.hash import verify_password

def login_controller(db: Session, username: str, password: str) -> dict:
    user = auth_repo.get_user_by_username(db, username)
    if not user or not user.is_active or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or inactive user"
        )

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        token_version=user.token_version,
    )

    return {
        "message": "Logged in Successfully",
        "access_token": token,
        "user_id": str(user.id),
    }

def logout_controller(db: Session, request: Request, current_user: User) -> dict:
    raw = request.cookies.get(settings.COOKIE_NAME)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        payload = decode_token(raw)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    sub = payload.get("sub")
    if sub != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not belong to current user"
        )

    auth_repo.bump_token_version(db, current_user)
    return {
        "message": "Logged out Successfully",
        "user_id": str(current_user.id),
        "clear_cookie": True
    }