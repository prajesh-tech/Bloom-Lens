from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BloomLevel(Base):
    __tablename__ = "bloom_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)  # L1 - L6
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # Remember, Understand, Apply...
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[dict] = mapped_column(JSON, nullable=True)  # List of verbs/action words
