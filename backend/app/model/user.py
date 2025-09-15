# backend/app/model/user.py
import uuid
from enum import Enum
from sqlalchemy import Column, String, Boolean, Enum as SAEnum, DateTime, Integer, func
from app.db.database import Base

class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    staff = "staff"

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)

    full_name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)

    role = Column(SAEnum(UserRole, name="user_role"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    token_version = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
