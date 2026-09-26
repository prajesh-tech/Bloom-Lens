from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class QuestionCourseOutcome(Base):
    __tablename__ = "question_course_outcomes"
    __table_args__ = (
        UniqueConstraint("question_id", "course_outcome_id", name="uq_question_co_mapping"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_outcome_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("course_outcomes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Scoring details
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    concept_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bloom_consistency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ai_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Verification status
    llm_verified: Mapped[str] = mapped_column(
        String(50), default="skipped", nullable=False
    )  # "verified", "rejected", "skipped", "unavailable"
    llm_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    human_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="course_outcomes")
    course_outcome: Mapped["CourseOutcome"] = relationship("CourseOutcome", back_populates="question_mappings")
