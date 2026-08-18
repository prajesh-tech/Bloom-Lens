import re
from typing import Tuple, Optional


class MarksService:
    """Service for extracting and normalizing question marks from text patterns."""

    @staticmethod
    def extract_marks(text: str) -> Tuple[Optional[float], str]:
        """
        Parses text for mark notations.
        Returns Tuple[extracted_marks_float, marks_confidence_str].
        Confidence: "high", "medium", "low", or None if no marks found.
        """
        if not text:
            return None, "low"

        # Pattern 1: Explicit mark suffix e.g., "5 marks", "[10 Marks]", "(5M)", "10-Marks"
        match = re.search(
            r"(?:\[|\(|\s|^)(\d+(?:\.\d+)?)\s*(?:-|–|\s)?(?:marks?|m)\b",
            text,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1)), "high"

        # Pattern 2: Multiplication notation e.g., "2 x 5", "2 × 5 marks", "3 * 4 = 12"
        match_mult = re.search(
            r"(\d+)\s*[xX×*]\s*(\d+(?:\.\d+)?)(?:\s*=\s*(\d+(?:\.\d+)?))?",
            text,
        )
        if match_mult:
            if match_mult.group(3):
                return float(match_mult.group(3)), "high"
            count = float(match_mult.group(1))
            val = float(match_mult.group(2))
            return count * val, "high"

        # Pattern 3: Addition notation e.g., "5+5", "5 + 5 marks"
        match_add = re.search(r"(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)", text)
        if match_add:
            val1 = float(match_add.group(1))
            val2 = float(match_add.group(2))
            return val1 + val2, "high"

        # Pattern 4: Standalone mark in brackets at end of question text e.g., "(10)" or "[5]"
        match_bracket = re.search(r"[\[\(](\d+(?:\.\d+)?)[\]\)]\s*$", text.strip())
        if match_bracket:
            return float(match_bracket.group(1)), "medium"

        return None, "low"
