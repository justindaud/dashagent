# backend/app/models.py
from __future__ import annotations
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    Integer, String, Text, TIMESTAMP, ForeignKey, Index, text as sqltext, Boolean
)
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=sqltext("now()"), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=sqltext("now()"), nullable=False)


class AgentSessionPrealloc(Base):
    __tablename__ = "agent_session_prealloc"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sqltext("false"))
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=sqltext("now()"), nullable=False)
    consumed_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


Index("idx_prealloc_user", AgentSessionPrealloc.user_id)
Index("idx_prealloc_is_active", AgentSessionPrealloc.is_active)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(128), ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=sqltext("'running'"))
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=sqltext("now()"))
    finished_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(128), ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_runs.run_id", ondelete="SET NULL"), nullable=True, index=True)
    message_data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=sqltext("now()"))


class SessionInsight(Base):
    __tablename__ = "session_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(128), ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    insight_content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=sqltext("CURRENT_TIMESTAMP"), nullable=False)
