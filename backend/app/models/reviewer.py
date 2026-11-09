from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Reviewer(Base):
    __tablename__ = 'reviewers'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default='instructor', nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ReviewerSession(Base):
    __tablename__ = 'reviewer_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('reviewers.id', ondelete='CASCADE'), nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuestionRevision(Base):
    __tablename__ = 'question_revisions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey('questions.id', ondelete='SET NULL'), nullable=True, index=True)
    acting_user: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    old_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    new_value: Mapped[dict] = mapped_column(JSON, nullable=False)
