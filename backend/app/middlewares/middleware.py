# app/middlewares/middleware.py
from fastapi import Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.config.settings import settings
from app.db.database import get_db
from app.utils.security import decode_token, create_access_token 
from app.utils.cookies import set_auth_cookie
from app.model.user import User, UserRole
from app.repositories.user_repository import get_user_by_id

def get_current_user(request: Request, response: Response, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    tver_claim = payload.get("tver")

    if not user_id or tver_claim is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        token_version = int(tver_claim)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
    if token_version != int(user.token_version or 0):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalidated. Please login again.")
    
    exp_timestamp = payload.get("exp")
    current_timestamp = datetime.now(timezone.utc).timestamp()
    
    time_left = exp_timestamp - current_timestamp
    
    total_duration_seconds = settings.JWT_EXPIRATION_DAYS * 86400
    threshold = total_duration_seconds / 2 

    if time_left < threshold:
        new_token = create_access_token(
            subject=str(user.user_id),
            role=user.role.value if hasattr(user.role, 'value') else str(user.role),
            token_version=user.token_version
        )
        
        set_auth_cookie(response, new_token)
        
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user

def require_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")
    return current_user