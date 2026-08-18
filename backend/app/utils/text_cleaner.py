import re
import string
from typing import Optional


def clean_text(text: str) -> str:
    """Removes extra whitespace and non-printable characters."""
    if not text:
        return ""
    # Replace non-breaking spaces and invalid chars
    cleaned = text.replace("\xa0", " ").replace("\r", "\n")
    # Normalize multiple newlines/spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


def sanitize_display_text(text: str, max_length: int = 20000) -> str:
    """Removes control characters from user/OCR text before storage or rendering."""
    if not text:
        return ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return cleaned[:max_length].strip()


def normalize_question_text(text: str) -> str:
    """
    Normalizes question text for exact matching and vector embedding calculation.
    Converts to lowercase, removes punctuation and redundant spacing.
    """
    if not text:
        return ""
    text_lower = text.lower().strip()
    # Remove leading question numbers e.g. "Q1(a)", "1.", "a)"
    text_lower = re.sub(r"^(q\d+\s*\(?[a-z\d]?\)?|\d+[\.\)]|\([a-z\d]+\))\s*", "", text_lower)
    # Remove punctuation
    translator = str.maketrans("", "", string.punctuation)
    clean = text_lower.translate(translator)
    # Collapse whitespace
    return re.sub(r"\s+", " ", clean).strip()


def extract_year_from_text(text: str) -> Optional[str]:
    """Attempts to extract examination year or date string from document text or filename."""
    if not text:
        return None
    # Match patterns like "May 2024", "Nov-2023", "2023-2024", "2024"
    match = re.search(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-_,]+(20\d{2})\b",
        text,
        re.IGNORECASE,
    )
    if match:
        return f"{match.group(1).capitalize()} {match.group(2)}"

    match_year = re.search(r"\b(20[12]\d)\b", text)
    if match_year:
        return match_year.group(1)

    return None
