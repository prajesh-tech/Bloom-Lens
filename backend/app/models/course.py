from app.models.question_paper import QuestionPaper
from app.models.course_outcome import CourseOutcome
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    course_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    outcomes: Mapped[List["CourseOutcome"]] = relationship(
        "CourseOutcome", back_populates="course", cascade="all, delete-orphan", order_by="CourseOutcome.sort_order"
    )
    question_papers: Mapped[List["QuestionPaper"]] = relationship(
        "QuestionPaper", back_populates="course"
    )
