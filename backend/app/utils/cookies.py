# app/utils/cookies.py
from datetime import datetime, timedelta, timezone
from fastapi.responses import Response
from app.config.settings import settings

def set_auth_cookie(resp: Response, token: str) -> None:
    max_age = settings.JWT_EXPIRATION_DAYS * 86400
    expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRATION_DAYS)
    resp.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=max_age,
        expires=expires,
    )

def clear_auth_cookie(resp: Response) -> None:
    resp.delete_cookie(key=settings.COOKIE_NAME, path="/")
