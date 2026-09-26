from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class QuestionPaper(Base):
    __tablename__ = "question_papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    examination_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Mid-Term, End-Semester, Internal, etc.
    maximum_marks: Mapped[float] = mapped_column(Float, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    year_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "2024", "May 2023"

    # Processing & Validation Statuses
    processing_status: Mapped[str] = mapped_column(
        String(50), default="UPLOADED", nullable=False, index=True
    )  # UPLOADED, PROCESSING, EXTRACTED, ANALYZING, COMPLETED, REVIEW_REQUIRED, FAILED
    extraction_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(50), default="NOT_VALIDATED", nullable=False)
    optional_question_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

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
    subject: Mapped["Subject"] = relationship("Subject", back_populates="question_papers")
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="question_papers")
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="question_paper", cascade="all, delete-orphan"
    )
