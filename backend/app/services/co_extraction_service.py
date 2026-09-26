import os
import re
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.services.document_service import DocumentService


class COExtractionService:
    """
    Extracts candidate Course Outcomes from syllabus documents (PDF, DOCX, TXT)
    or raw text blocks without modifying the database.
    """

    # Primary CO line patterns: e.g. "CO1: ...", "CO-2 - ...", "Course Outcome 3: ...", "CO.4. ..."
    CO_EXPLICIT_PATTERN = re.compile(
        r"^(?:(?:Course\s+Outcome|Learning\s+Outcome|Outcome)\s*[-_.]?\s*(\d+)|CO\s*[-_.]?\s*(\d+))\s*[:.\-–—\t ]\s*(.+)$",
        re.IGNORECASE,
    )

    # Secondary pattern where code is on its own or separated by tab/colon
    CO_CODE_ONLY_PATTERN = re.compile(r"^(?:CO\s*(\d+)|Course\s+Outcome\s*(\d+))$", re.IGNORECASE)

    # Keywords to detect a Course Outcomes section in unstructured syllabus documents
    CO_SECTION_HEADER_PATTERN = re.compile(
        r"(?:course\s+outcomes|course\s+learning\s+outcomes|learning\s+outcomes|expected\s+outcomes|c\.o\.s|c\.o\.)\s*[:\-]?",
        re.IGNORECASE,
    )

    # Bloom action verb cues for suggestion
    BLOOM_VERB_MAP = {
        "L1": ["define", "list", "recall", "state", "name", "identify", "mention", "label", "recognize"],
        "L2": ["explain", "describe", "discuss", "understand", "summarize", "classify", "interpret", "illustrate", "express"],
        "L3": ["apply", "demonstrate", "solve", "implement", "calculate", "compute", "execute", "use", "construct"],
        "L4": ["analyze", "examine", "compare", "contrast", "distinguish", "differentiate", "categorize", "investigate"],
        "L5": ["evaluate", "assess", "justify", "judge", "critique", "verify", "recommend", "rate", "appraise"],
        "L6": ["design", "develop", "formulate", "create", "compose", "plan", "synthesize", "generate", "build"],
    }

    @classmethod
    def estimate_bloom_level(cls, text: str) -> Optional[str]:
        """Infers likely Bloom cognitive level from the primary action verbs in the CO text."""
        words = [w.strip(".,;:()[]{}").lower() for w in text.split()[:8]]
        for word in words:
            for level, verbs in cls.BLOOM_VERB_MAP.items():
                if word in verbs:
                    return level
        return None

    @classmethod
    def clean_description(cls, desc: str) -> str:
        """Cleans and sanitizes extracted outcome description."""
        cleaned = desc.strip()
        # Remove markdown bold/italics
        cleaned = re.sub(r"[*_]{1,3}", "", cleaned)
        # Remove trailing bloom indicators like (L2), [Bloom Level: Apply], (Cognitive Level: Understand)
        cleaned = re.sub(r"\s*[\(\[]\s*(?:Bloom(?:'s)?\s*Level|Cognitive\s*Level|Level|BL|CL|L[1-6])\s*[:\-–]?\s*[^\]\)]*[\)\]]", "", cleaned, flags=re.IGNORECASE)
        # Strip leading punctuation/bullets
        cleaned = re.sub(r"^[\-–—:.)\]\s]+", "", cleaned)
        return cleaned.strip()

    @classmethod
    def extract_cos_from_text(cls, text: str) -> List[Dict[str, Any]]:
        """
        Parses raw text and extracts structured candidate Course Outcomes.
        """
        if not text or not text.strip():
            return []

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        extracted: Dict[str, Dict[str, Any]] = {}
        in_co_section = False
        section_counter = 1

        for i, line in enumerate(lines):
            # 1. Check if entering a Course Outcomes section header
            if cls.CO_SECTION_HEADER_PATTERN.search(line):
                in_co_section = True
                continue

            # Check if entering another major section (e.g., "Syllabus:", "References:", "Unit 1:")
            if in_co_section and re.match(r"^(?:Unit\s+\d+|Module\s+\d+|References|Textbooks|Syllabus|Evaluation Scheme)\s*[:\-]", line, re.IGNORECASE):
                in_co_section = False

            # 2. Match explicit CO line (e.g. "CO1: Explain algorithmic complexity")
            explicit_match = cls.CO_EXPLICIT_PATTERN.match(line)
            if explicit_match:
                num = explicit_match.group(1) or explicit_match.group(2)
                raw_desc = explicit_match.group(3)
                code = f"CO{int(num)}"
                clean_desc = cls.clean_description(raw_desc)
                if len(clean_desc) > 3:
                    extracted[code] = {
                        "code": code,
                        "description": clean_desc,
                        "sort_order": int(num),
                        "confidence": 0.95,
                        "suggested_bloom_level": cls.estimate_bloom_level(clean_desc),
                    }
                continue

            # 3. Match code-only line with description on next line
            code_only_match = cls.CO_CODE_ONLY_PATTERN.match(line)
            if code_only_match and i + 1 < len(lines):
                num = code_only_match.group(1) or code_only_match.group(2)
                next_line = lines[i + 1]
                if not cls.CO_CODE_ONLY_PATTERN.match(next_line) and not cls.CO_EXPLICIT_PATTERN.match(next_line):
                    code = f"CO{int(num)}"
                    clean_desc = cls.clean_description(next_line)
                    if len(clean_desc) > 3:
                        extracted[code] = {
                            "code": code,
                            "description": clean_desc,
                            "sort_order": int(num),
                            "confidence": 0.90,
                            "suggested_bloom_level": cls.estimate_bloom_level(clean_desc),
                        }
                    continue

            # 4. If inside a detected CO section, match numbered list items (e.g. "1. Design...", "a) Understand...")
            if in_co_section:
                numbered_match = re.match(r"^(?:(\d+)[\.\)]\s*|[\-\*\u2022]\s*)(.+)$", line)
                if numbered_match:
                    num_str = numbered_match.group(1)
                    raw_desc = numbered_match.group(2)
                    num = int(num_str) if num_str else section_counter
                    code = f"CO{num}"
                    clean_desc = cls.clean_description(raw_desc)
                    if len(clean_desc) > 5 and code not in extracted:
                        extracted[code] = {
                            "code": code,
                            "description": clean_desc,
                            "sort_order": num,
                            "confidence": 0.85,
                            "suggested_bloom_level": cls.estimate_bloom_level(clean_desc),
                        }
                        section_counter = num + 1

        # Sort by sort_order
        result_list = sorted(extracted.values(), key=lambda x: x["sort_order"])
        logger.info(f"Extracted {len(result_list)} candidate COs from text")
        return result_list

    @classmethod
    def extract_cos_from_file(cls, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF, DOCX, or TXT file and parses candidate Course Outcomes.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
        elif ext in [".pdf", ".docx"]:
            doc_result = DocumentService.process_document(file_path)
            full_text = doc_result.get("full_text", "")
        else:
            raise ValueError(f"Unsupported file type '{ext}' for CO extraction. Supported: .pdf, .docx, .txt")

        return cls.extract_cos_from_text(full_text)
