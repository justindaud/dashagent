# backend/app/schemas/user.py
from pydantic import Field, ConfigDict
from typing import Optional
from app.utils.trim import TrimmedModel
from app.model.user import UserRole

class UserCreate(TrimmedModel):
    username: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)
    role: str = Field(min_length=1)

class UserUpdate(TrimmedModel):
    username: Optional[str] = Field(default=None, min_length=5, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8)
    confirm_password: Optional[str] = Field(default=None, min_length=8)
    full_name: Optional[str] = Field(default=None, min_length=1)
    role: Optional[str] = Field(default=None, min_length=1)
    is_active: Optional[bool] = None

class UserOut(TrimmedModel):
    id: str
    username: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
