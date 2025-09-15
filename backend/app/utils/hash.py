# app/utils/hash.py
import bcrypt
from app.config.settings import settings

def hash_password(plain: str) -> str:
    peppered = (plain + settings.PASSWORD_PEPPER).encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_COST)
    return bcrypt.hashpw(peppered, salt).decode("utf-8")

def verify_password(plain: str, password_hash: str) -> bool:
    peppered = (plain + settings.PASSWORD_PEPPER).encode("utf-8")
    try:
        return bcrypt.checkpw(peppered, password_hash.encode("utf-8"))
    except Exception:
        return False