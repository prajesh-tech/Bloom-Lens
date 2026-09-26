from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CourseOutcome(Base):
    __tablename__ = "course_outcomes"
    __table_args__ = (
        UniqueConstraint("course_id", "code", name="uq_course_outcome_course_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # e.g., CO1, CO2
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    course: Mapped["Course"] = relationship("Course", back_populates="outcomes")
    question_mappings: Mapped[List["QuestionCourseOutcome"]] = relationship(
        "QuestionCourseOutcome", back_populates="course_outcome", cascade="all, delete-orphan"
    )
