# backend/app/schemas/profile.py
from typing import Optional
from pydantic import Field
from app.utils.trim import TrimmedModel

class ProfileUpdate(TrimmedModel):
    username: Optional[str] = Field(default=None, min_length=5, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8)
    confirm_password: Optional[str] = None
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)