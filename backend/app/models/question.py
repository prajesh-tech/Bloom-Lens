from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_paper_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("question_papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_question_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True
    )

    question_number: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., Q1, Q1(a)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Marks details
    marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    marks_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # high, medium, low

    # Bloom Classification details (AI vs Human vs Effective)
    ai_bloom_level_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bloom_levels.id"), nullable=True
    )
    human_bloom_level_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bloom_levels.id"), nullable=True
    )
    effective_bloom_level_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bloom_levels.id"), nullable=True, index=True
    )
    bloom_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bloom_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Question Type details
    ai_question_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    human_question_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    question_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Effective question type

    # Metadata & Categorization
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    co_mapping: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"co": ["CO1"], "po": ["PO4"]}
    choice_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # e.g., Q3_OR_GROUP
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, default=1.0, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(50), default="AUTO_CLASSIFIED", nullable=False, index=True
    )  # AUTO_CLASSIFIED, REVIEWED, CORRECTED, FLAGGED
    ai_analysis_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Self-referential relationship for parent & sub-questions
    parent_question: Mapped[Optional["Question"]] = relationship(
        "Question", remote_side=[id], back_populates="sub_questions"
    )
    sub_questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="parent_question", cascade="all, delete-orphan"
    )

    # Relationships
    question_paper: Mapped["QuestionPaper"] = relationship("QuestionPaper", back_populates="questions")
    ai_bloom_level: Mapped[Optional["BloomLevel"]] = relationship(
        "BloomLevel", foreign_keys=[ai_bloom_level_id]
    )
    human_bloom_level: Mapped[Optional["BloomLevel"]] = relationship(
        "BloomLevel", foreign_keys=[human_bloom_level_id]
    )
    effective_bloom_level: Mapped[Optional["BloomLevel"]] = relationship(
        "BloomLevel", foreign_keys=[effective_bloom_level_id]
    )

    question_topics: Mapped[List["QuestionTopic"]] = relationship(
        "QuestionTopic", back_populates="question", cascade="all, delete-orphan"
    )

    similarities_source: Mapped[List["QuestionSimilarity"]] = relationship(
        "QuestionSimilarity",
        foreign_keys="[QuestionSimilarity.source_question_id]",
        back_populates="source_question",
        cascade="all, delete-orphan",
    )
    similarities_target: Mapped[List["QuestionSimilarity"]] = relationship(
        "QuestionSimilarity",
        foreign_keys="[QuestionSimilarity.target_question_id]",
        back_populates="target_question",
        cascade="all, delete-orphan",
    )
