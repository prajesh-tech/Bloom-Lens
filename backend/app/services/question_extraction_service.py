import re
from typing import List, Dict, Any, Optional, Tuple
from app.core.logging import logger
from app.services.marks_service import MarksService
from app.services.performance_estimation_service import extract_leaf_questions
from app.utils.text_cleaner import clean_text, normalize_question_text


class QuestionExtractionService:
    """
    Service for parsing question papers into structured main and sub-questions,
    extracting marks, detecting optional structures, and validating total paper marks.
    """

    MAIN_Q_PATTERN = re.compile(
        r"^(?:Q(?:uestion)?\s*[\.\:-]?\s*|Q)?(\d{1,2})\b[\.\:\)]?\s*",
        re.IGNORECASE,
    )
    SUB_Q_PATTERN = re.compile(
        r"^(?:\(?([a-z]|[ivxlcdm]+)\)?[\.\)]|\b([a-z])\))\s*",
        re.IGNORECASE,
    )
    FULL_QNUM_PATTERN = re.compile(
        r"^(Q?\d{1,2}(?:\s*[\(\.][a-z0-9]+[\)\.]?)*)[\.\:\s\-]+",
        re.IGNORECASE,
    )

    OPTIONAL_PATTERNS = [
        re.compile(r"answer\s+any\s+(\d+)\s+out\s+of\s+(\d+)", re.IGNORECASE),
        re.compile(r"attempt\s+any\s+(\d+)", re.IGNORECASE),
        re.compile(r"attempt\s+either\s+.*?\s+or\s+", re.IGNORECASE),
        re.compile(r"^\s*(?:---|\*\*\*)?\s*\(?OR\)?\s*(?:---|\*\*\*)?\s*$", re.IGNORECASE | re.MULTILINE),
    ]

    QUESTION_VERBS = {
        "differentiate", "list", "define", "how", "what", "write", "explain",
        "compare", "describe", "calculate", "discuss", "state", "illustrate",
        "evaluate", "design", "derive", "find", "show", "prove", "briefly",
        "give", "mention", "name", "outline", "summarize", "classify", "distinguish",
        "analyze", "compute", "determine"
    }

    CO_PO_PATTERN = re.compile(
        r"\[?\s*(CO-?\d+|PO-?\d+)(?:\s*[,&/]\s*(CO-?\d+|PO-?\d+))*\s*\]?",
        re.IGNORECASE,
    )

    @classmethod
    def extract_co_po_tags(cls, text: str) -> Optional[Dict[str, List[str]]]:
        """Extracts Course Outcomes (CO1, CO2) and Program Outcomes (PO1, PO4) from question text."""
        cos = sorted(list(set(re.findall(r"\bCO-?\d+\b", text, re.IGNORECASE))))
        pos = sorted(list(set(re.findall(r"\bPO-?\d+\b", text, re.IGNORECASE))))

        clean_cos = [c.upper().replace("-", "") for c in cos]
        clean_pos = [p.upper().replace("-", "") for p in pos]

        if clean_cos or clean_pos:
            return {
                "co": clean_cos,
                "po": clean_pos,
            }
        return None

    @classmethod
    def extract_questions(cls, full_text: str) -> List[Dict[str, Any]]:
        """
        Parses document full_text into structured question dictionary objects.
        Returns a list of parsed questions with parent-child links, CO-PO tags, and choice groups.
        """
        if not full_text:
            return []

        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
        raw_blocks: List[Dict[str, Any]] = []

        current_block: Optional[Dict[str, Any]] = None
        current_section_marks: Optional[float] = None
        current_choice_group: Optional[str] = None
        auto_q_counter = 1
        current_section = None
        has_numbering = any(cls.MAIN_Q_PATTERN.match(line) for line in lines)

        for line in lines:
            # Check for choice divider line e.g. "OR", "--- OR ---", "(OR)"
            if re.match(r"^(?:---|\*\*\*)?\s*\(?\s*OR\s*\)?\s*(?:---|\*\*\*)?$", line, re.IGNORECASE):
                if current_block:
                    parent_id = current_block["parent_number"] or current_block["question_number"]
                    current_choice_group = f"{parent_id}_OR_GROUP"
                    current_block["choice_group"] = current_choice_group
                continue

            section_match = re.match(r"^(PART|SECTION|GROUP)\s+[A-Z0-9]+", line, re.IGNORECASE)
            if section_match:
                current_section = section_match.group(0).upper()
                current_section_marks = None

            # Check section header with mark distribution.
            # Handles both:
            #   [5Q*2M=10 Marks]  → per-question value is group(1)
            #   [5*2=10 Marks]    → per-question value is group(2) (the second factor)
            sec_marks_match = re.search(
                r"\[?\s*\d+\s*Q\s*[*xX×]\s*(\d+(?:\.\d+)?)\s*M(?:arks)?",
                line,
                re.IGNORECASE,
            )
            if sec_marks_match:
                current_section_marks = float(sec_marks_match.group(1))
                continue

            # Fallback: plain "N*M=Total Marks" or "N×M=Total Marks" in section headers
            sec_marks_plain = re.search(
                r"\b(\d+)\s*[*xX×]\s*(\d+(?:\.\d+)?)\s*=\s*\d+(?:\.\d+)?\s*Marks?\b",
                line,
                re.IGNORECASE,
            )
            if sec_marks_plain:
                # The second factor is the per-question mark value
                current_section_marks = float(sec_marks_plain.group(2))
                continue

            # Check for header/section markers e.g. "PART A", "SECTION 1", "ALL THE BEST"
            if re.match(r"^(PART|SECTION|GROUP)\s+[A-Z0-9]+", line, re.IGNORECASE) or line.startswith("***"):
                continue

            if re.search(r"\b(all questions|carry equal marks|are compulsory|all sections|answer any|attempt any)\b", line, re.IGNORECASE):
                continue

            # Check if line starts a new main or sub question
            q_num_match, is_sub, parent_num = cls._match_question_number(line)

            # Fallback check for un-numbered questions (starts with question verb or has [CO..., PO...] outcome tag)
            if not q_num_match:
                first_word = line.split()[0].lower().rstrip(":,.()") if line.split() else ""
                has_co_po = bool(re.search(r"\[CO\d+,?\s*PO\d+\]", line, re.IGNORECASE))
                is_verb_start = first_word in cls.QUESTION_VERBS

                previous_line = current_block["raw_lines"][-1] if current_block and current_block["raw_lines"] else ""
                follows_marks = (MarksService.extract_marks(previous_line)[0] is not None and
                    bool(re.search(r"(?:\d+(?:\.\d+)?\s*(?:marks?|m)\s*[\])]?|\d+(?:\.\d+)?\s*[\])])\s*[.;]?\s*$", previous_line, re.IGNORECASE)))
                if (not has_numbering or follows_marks) and (is_verb_start or has_co_po) and not line.lower().startswith("note:") and not line.lower().startswith("answer the following"):
                    q_num_match = f"Q{auto_q_counter}"
                    is_sub = False
                    parent_num = None
                    auto_q_counter += 1

            if q_num_match:
                if current_block and current_block["raw_lines"]:
                    raw_blocks.append(current_block)

                current_block = {
                    "question_number": q_num_match,
                    "parent_number": parent_num,
                    "is_sub": is_sub,
                    "section_marks": current_section_marks,
                    "section": current_section,
                    "choice_group": current_choice_group,
                    "raw_lines": [line] if not re.match(r"^(?:Q|Question)?\s*\d{1,2}[\.\:\)]?\s*$", line, re.IGNORECASE) else [],
                }
                current_choice_group = None
                auto_q_counter = max(auto_q_counter, int(re.search(r"\d+", q_num_match).group()) + 1) if re.search(r"\d+", q_num_match) else auto_q_counter
            else:
                if current_block:
                    current_block["raw_lines"].append(line)

        if current_block and current_block["raw_lines"]:
            raw_blocks.append(current_block)

        # Post-process raw blocks into structured question nodes
        questions: List[Dict[str, Any]] = []
        last_main_q: Optional[str] = None

        for block in raw_blocks:
            full_q_text = clean_text(" ".join(block["raw_lines"]))
            if not full_q_text:
                continue

            marks, marks_conf = MarksService.extract_marks(full_q_text)
            if marks is None and block.get("section_marks") is not None:
                marks = block["section_marks"]
                marks_conf = "high"

            norm_text = normalize_question_text(full_q_text)
            co_mapping = cls.extract_co_po_tags(full_q_text)

            q_number = block["question_number"]
            parent_q = block["parent_number"]

            if not block["is_sub"]:
                last_main_q = q_number
            elif not parent_q and last_main_q:
                parent_q = last_main_q
                if not q_number.startswith(last_main_q):
                    q_number = f"{last_main_q}({q_number.strip('()')})"

            questions.append({
                "question_number": q_number,
                "parent_number": parent_q,
                "section": block.get("section"),
                "original_text": full_q_text,
                "normalized_text": norm_text,
                "marks": marks,
                "marks_confidence": marks_conf,
                "co_mapping": co_mapping,
                "choice_group": block.get("choice_group"),
                "extraction_confidence": 0.95 if marks else 0.80,
            })

        logger.info(f"Extracted {len(questions)} questions from document text.")
        return questions

    @classmethod
    def _match_question_number(cls, line: str) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Helper method to detect question number and parent relation from line prefix.
        Returns Tuple[q_number, is_sub_flag, parent_number].
        """
        # Match standalone number line e.g. "1.", "1", "Q1."
        m_alone = re.match(r"^(?:Q|Question)?\s*(\d{1,2})[\.\:\)]?\s*$", line, re.IGNORECASE)
        if m_alone:
            return f"Q{m_alone.group(1)}", False, None

        # Require a delimited label; never consume the first letter of prose.
        m_explicit = re.match(r"^(?:Question\s*|Q\.?\s*)?(\d+)\s*(?:\(([a-z]|[ivxlcdm]+)\)|([a-z])\))(?=\W|$)\s*", line, re.IGNORECASE)
        if m_explicit:
            main_n = f"Q{m_explicit.group(1)}"
            return f"{main_n}({(m_explicit.group(2) or m_explicit.group(3)).lower()})", True, main_n

        m_main = cls.MAIN_Q_PATTERN.match(line)
        if m_main:
            return f"Q{m_main.group(1)}", False, None

        # Match sub-question a), (b), i.
        m_sub = re.match(r"^(?:\(([a-z0-9]+)\)|([a-z0-9]+)[\)\.])\s+", line, re.IGNORECASE)
        if m_sub:
            sub_val = m_sub.group(1) or m_sub.group(2)
            if sub_val and len(sub_val) <= 3:
                return f"({sub_val.lower()})", True, None

        return None, False, None

    @classmethod
    def detect_optional_structure(cls, text: str) -> Dict[str, Any]:
        """Detects optional question patterns e.g., 'Answer any 4 out of 5'."""
        has_optional = False
        details = []

        for pattern in cls.OPTIONAL_PATTERNS:
            match = pattern.search(text)
            if match:
                has_optional = True
                details.append(match.group(0))

        rules = []
        section = None
        for line in text.splitlines():
            header = re.match(r"^(PART|SECTION|GROUP)\s+[A-Z0-9]+", line.strip(), re.IGNORECASE)
            if header:
                section = header.group(0).upper()
            match = re.search(r"(?:answer|attempt)\s+any\s+(\d+)\s+out\s+of\s+(\d+)", line, re.IGNORECASE)
            if match:
                rules.append({"section": section, "n": int(match.group(1)), "m": int(match.group(2))})
        return {
            "rules": rules,
            "has_optional_questions": has_optional,
            "detected_patterns": details,
        }

    @classmethod
    def validate_paper_marks(
        cls, maximum_marks: float, questions: List[Dict[str, Any]], full_text: str
    ) -> Dict[str, Any]:
        """
        Compares maximum_marks with sum of extracted marks across questions.
        Returns validation status, breakdown, and possible reasons for discrepancy.
        """
        optional_info = cls.detect_optional_structure(full_text)
        has_optional = optional_info["has_optional_questions"]

        # Sum marks of all questions (considering leaf sub-questions or parent questions without sub-questions)
        total_extracted_marks = 0.0
        missing_marks_count = 0

        for q in extract_leaf_questions(questions):
            if q.get("marks") is not None:
                total_extracted_marks += q["marks"]
            else:
                missing_marks_count += 1

        unresolved_optional = False
        if has_optional:
            rules = optional_info["rules"]
            unresolved_optional = not rules or len({r["section"] for r in rules}) != len(rules)
            for rule in rules:
                section_questions = [q for q in extract_leaf_questions(questions) if q.get("section") == rule["section"]]
                totals = {}
                for question in section_questions:
                    key = question.get("parent_number") or question["question_number"]
                    if question.get("marks") is None:
                        unresolved_optional = True
                        break
                    totals[key] = totals.get(key, 0) + question["marks"]
                if (len(totals) != rule["m"] or not 0 < rule["n"] <= rule["m"]
                        or len(set(totals.values())) != 1):
                    unresolved_optional = True
                else:
                    total_extracted_marks -= (rule["m"] - rule["n"]) * next(iter(totals.values()))

        reasons = []
        if missing_marks_count > 0:
            reasons.append("marks_extraction_error")

        if has_optional:
            reasons.append("optional_question_structure")

        status = "uncertain" if unresolved_optional or missing_marks_count else "valid"
        if abs(total_extracted_marks - maximum_marks) > 0.5:
            if missing_marks_count > 0 or has_optional:
                status = "uncertain"
            else:
                status = "mismatch"
                reasons.append("question_not_detected")

        return {
            "status": status,
            "maximum_marks": maximum_marks,
            "extracted_marks": total_extracted_marks,
            "missing_marks_count": missing_marks_count,
            "optional_question_flag": has_optional,
            "possible_reasons": reasons,
            "optional_details": optional_info,
            "question_sections": {q["question_number"]: q.get("section") for q in questions},
        }
