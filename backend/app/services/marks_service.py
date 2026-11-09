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

        # Arithmetic is meaningful only in explicitly marked allocation notation.
        candidates = []
        patterns = [
            (r"[\[(](\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)\s*marks?[\])]", "sum", "high"),
            (r"^answer\s+the\s+following\s+questions\s+(\d+)\s*[x×*]\s*(\d+)\s*=\s*(\d+)(?=\s*$|\s*marks?\b)", "total", "high"),
            (r"(?:^|[\s[(])(\d+(?:\.\d+)?)\s*(?:[-–]\s*)?marks?\b", "single", "high"),
            (r"[\[(](\d+(?:\.\d+)?)\s*M[\])]", "single", "high"),
            (r"[\[(](\d+(?:\.\d+)?)[\])]\s*$", "single", "medium"),
        ]
        for pattern, operation, confidence in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                values = [float(value) for value in match.groups()]
                value = sum(values) if operation == "sum" else values[-1]
                candidates.append((match.end(), -match.start(), value, confidence))
        if candidates:
            _, _, value, confidence = max(candidates)
            return value, confidence
        return None, "low"
