# app/utils/security.py
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from app.config.settings import settings

def create_access_token(subject: str, role: str, token_version: int, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        "sub": subject,
        "role": role,
        "tver": token_version,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
