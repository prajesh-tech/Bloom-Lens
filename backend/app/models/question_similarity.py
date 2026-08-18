from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Float, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class QuestionSimilarity(Base):
    __tablename__ = "question_similarities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    similarity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # exact_repeat, semantic_repeat
    classification: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # exact_repeat, potentially_repeated, different
    similarity_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    source_question: Mapped["Question"] = relationship(
        "Question", foreign_keys=[source_question_id], back_populates="similarities_source"
    )
    target_question: Mapped["Question"] = relationship(
        "Question", foreign_keys=[target_question_id], back_populates="similarities_target"
    )
