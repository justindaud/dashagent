# backend/app/model/session.py
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Index
from app.db.database import Base

class AgentSession(Base):
    __tablename__ = "agent_sessions"

    session_id = Column(String(128), primary_key=True, nullable=False)
    user_id    = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)

    title      = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class AgentSessionPrealloc(Base):
    __tablename__ = "agent_session_prealloc"

    session_id  = Column(String, primary_key=True, index=True)
    user_id     = Column(String, index=True, nullable=False)
    is_active   = Column(Boolean, nullable=False, server_default="false")
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)

Index("idx_prealloc_user", AgentSessionPrealloc.user_id)
Index("idx_prealloc_is_active", AgentSessionPrealloc.is_active)