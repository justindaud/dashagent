# backend/app/schemas/auth.py
from app.utils.trim import TrimmedModel

class LoginRequest(TrimmedModel):
    username: str
    password: str

class LoginResponse(TrimmedModel):
    user_id: str

class LogoutResponse(TrimmedModel):
    user_id: str