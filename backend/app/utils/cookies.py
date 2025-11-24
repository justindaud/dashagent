# app/utils/cookies.py
from datetime import datetime, timedelta, timezone
from fastapi.responses import Response
from app.config.settings import settings

def _normalized_samesite(value: str) -> str:
    v = (value or "").lower()
    if v not in {"lax", "none", "strict"}:
        return "lax"
    return v

def set_auth_cookie(resp: Response, token: str) -> None:
    max_age = settings.JWT_EXPIRATION_DAYS * 86400
    expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRATION_DAYS)

    samesite = _normalized_samesite(settings.COOKIE_SAMESITE)
    secure = settings.COOKIE_SECURE

    if samesite == "none":
        secure = True

    resp.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=samesite,
        secure=secure,
        path=settings.COOKIE_PATH,
        max_age=max_age,
        expires=expires,
        domain=settings.COOKIE_DOMAIN,
    )

def clear_auth_cookie(resp: Response) -> None:
    resp.delete_cookie(
        key=settings.COOKIE_NAME,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
    )
