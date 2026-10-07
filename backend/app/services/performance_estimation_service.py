import math
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.schemas.paper import PerformanceEstimateResponse


BLOOM_CODE_TO_LEVEL: Dict[str, int] = {
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
    "L5": 5,
    "L6": 6,
    "REMEMBER": 1,
    "UNDERSTAND": 2,
    "APPLY": 3,
    "ANALYZE": 4,
    "EVALUATE": 5,
    "CREATE": 6,
}


def parse_bloom_level_index(level_val: Any) -> Optional[int]:
    """
    Parses a bloom level indicator into an integer index 1..6.
    Accepts integer (1..6), code string ('L1'..'L6'), or name ('Remember'..'Create').
    Returns None if missing or invalid.
    """
    if level_val is None:
        return None
    if isinstance(level_val, int):
        return level_val if 1 <= level_val <= 6 else None
    if isinstance(level_val, str):
        cleaned = level_val.strip().upper()
        if cleaned in BLOOM_CODE_TO_LEVEL:
            return BLOOM_CODE_TO_LEVEL[cleaned]
        # Check prefix e.g. "L1: REMEMBER"
        for code, idx in BLOOM_CODE_TO_LEVEL.items():
            if cleaned.startswith(code):
                return idx
    # Check BloomLevel ORM object
    if hasattr(level_val, "code") and level_val.code:
        return parse_bloom_level_index(level_val.code)
    if hasattr(level_val, "id") and isinstance(level_val.id, int):
        return parse_bloom_level_index(level_val.id)
    return None


def is_valid_numeric_marks(marks: Any) -> bool:
    """Checks whether marks is a valid positive finite numeric value."""
    if marks is None:
        return False
    if isinstance(marks, (int, float)):
        return not (math.isnan(marks) or math.isinf(marks) or marks <= 0)
    try:
        val = float(marks)
        return not (math.isnan(val) or math.isinf(val) or val <= 0)
    except (ValueError, TypeError):
        return False


def get_bloom_weight_for_level(level_idx: int, config: Any = None) -> float:
    """Returns the difficulty weight for bloom level 1..6 from config."""
    cfg = config or settings
    weight_map = {
        1: cfg.ESTIMATE_BLOOM_WEIGHT_L1,
        2: cfg.ESTIMATE_BLOOM_WEIGHT_L2,
        3: cfg.ESTIMATE_BLOOM_WEIGHT_L3,
        4: cfg.ESTIMATE_BLOOM_WEIGHT_L4,
        5: cfg.ESTIMATE_BLOOM_WEIGHT_L5,
        6: cfg.ESTIMATE_BLOOM_WEIGHT_L6,
    }
    return weight_map.get(level_idx, 0.0)


def extract_leaf_questions(questions: List[Any]) -> List[Any]:
    """
    Filters a list of questions to leaf-level scoring units.
    A question is a parent container (not a leaf) if other questions reference it
    as parent_question_id or if its sub_questions collection is populated.
    This prevents double-counting marks of parent containers and sub-questions.
    Uses parent_question_id and avoids triggering SQLAlchemy lazy-loading.
    """
    # 1. Collect all parent IDs referenced in questions
    parent_ids = set()
    for q in questions:
        parent_id = getattr(q, "parent_question_id", None) if not isinstance(q, dict) else q.get("parent_question_id")
        if parent_id is not None:
            parent_ids.add(parent_id)

    leaf_questions = []
    for q in questions:
        q_id = getattr(q, "id", None) if not isinstance(q, dict) else q.get("id")
        if q_id is not None and q_id in parent_ids:
            # This question is referenced as a parent by another question
            continue

        # Check sub_questions only if already loaded (avoids SQLAlchemy MissingGreenlet)
        if isinstance(q, dict):
            if q.get("sub_questions"):
                continue
        elif hasattr(q, "__dict__"):
            sub_qs = q.__dict__.get("sub_questions")
            if sub_qs:
                continue

        leaf_questions.append(q)

    return leaf_questions


def compute_performance_estimate_core(
    paper_max_marks: Optional[float],
    questions: List[Any],
    config: Any = None,
    is_completed: bool = True,
) -> PerformanceEstimateResponse:
    """
    Pure deterministic core function to compute heuristic performance estimates.
    No I/O, no randomness, no persistent state mutations.

    Returns:
        PerformanceEstimateResponse with estimated_pass_percentage and
        estimated_average_marks, or unavailable with a short reason code.
    """
    cfg = config or settings

    # Check 1: Paper processing status must be complete
    if not is_completed:
        return PerformanceEstimateResponse(
            estimated_pass_percentage=None,
            estimated_average_marks=None,
            reason="paper_not_completed",
        )

    # Check 2: Maximum paper marks must be positive numeric and finite
    if paper_max_marks is None or not is_valid_numeric_marks(paper_max_marks):
        return PerformanceEstimateResponse(
            estimated_pass_percentage=None,
            estimated_average_marks=None,
            reason="invalid_max_marks",
        )

    max_marks_float = float(paper_max_marks)

    # Extract leaf scoring units
    leaf_qs = extract_leaf_questions(questions)
    if not leaf_qs:
        return PerformanceEstimateResponse(
            estimated_pass_percentage=None,
            estimated_average_marks=None,
            reason="no_valid_questions",
        )

    # Classify valid vs excluded leaf questions
    valid_questions = []
    excluded_with_marks_sum = 0.0
    missing_marks_count = 0

    for q in leaf_qs:
        # Resolve marks
        raw_marks = getattr(q, "marks", None) if not isinstance(q, dict) else q.get("marks")
        marks_valid = is_valid_numeric_marks(raw_marks)

        # Resolve effective bloom level
        raw_bloom = getattr(q, "effective_bloom_level", None) if not isinstance(q, dict) else q.get("effective_bloom_level")
        if raw_bloom is None:
            # Fall back to effective_bloom_level_id, human_bloom_level, ai_bloom_level
            raw_bloom = (
                getattr(q, "effective_bloom_level_id", None)
                if not isinstance(q, dict)
                else q.get("effective_bloom_level_id")
            )
            if raw_bloom is None:
                raw_bloom = (
                    getattr(q, "human_bloom_level_id", None)
                    if not isinstance(q, dict)
                    else q.get("human_bloom_level_id")
                )
            if raw_bloom is None:
                raw_bloom = (
                    getattr(q, "ai_bloom_level_id", None)
                    if not isinstance(q, dict)
                    else q.get("ai_bloom_level_id")
                )
            if raw_bloom is None:
                raw_bloom = (
                    getattr(q, "ai_bloom_level", None)
                    if not isinstance(q, dict)
                    else q.get("ai_bloom_level")
                )

        bloom_idx = parse_bloom_level_index(raw_bloom)

        if marks_valid and bloom_idx is not None:
            valid_questions.append((float(raw_marks), bloom_idx))
        else:
            if marks_valid:
                excluded_with_marks_sum += float(raw_marks)
            else:
                missing_marks_count += 1

    if not valid_questions:
        return PerformanceEstimateResponse(
            estimated_pass_percentage=None,
            estimated_average_marks=None,
            reason="no_valid_questions",
        )

    valid_marks_sum = sum(m for m, _ in valid_questions)

    # Check 3: Excluded marks threshold policy
    # If questions have missing marks, consider the unallocated marks from paper_max_marks
    if missing_marks_count > 0:
        unallocated_gap = max(0.0, max_marks_float - valid_marks_sum)
        total_excluded_marks = max(excluded_with_marks_sum, unallocated_gap)
    else:
        total_excluded_marks = excluded_with_marks_sum

    marks_basis = max(max_marks_float, valid_marks_sum + total_excluded_marks)
    max_excluded_ratio = getattr(cfg, "ESTIMATE_MAX_EXCLUDED_MARKS_RATIO", 0.20)

    if marks_basis > 0 and (total_excluded_marks / marks_basis) > max_excluded_ratio:
        return PerformanceEstimateResponse(
            estimated_pass_percentage=None,
            estimated_average_marks=None,
            reason="too_many_excluded",
        )

    # Calculate Paper Difficulty D
    total_weighted = sum(m * get_bloom_weight_for_level(b_idx, cfg) for m, b_idx in valid_questions)
    d_difficulty = total_weighted / valid_marks_sum

    # Linear clamped mappings
    pass_intercept = getattr(cfg, "ESTIMATE_PASS_PCT_INTERCEPT", 95.0)
    pass_slope = getattr(cfg, "ESTIMATE_PASS_PCT_SLOPE", 65.0)
    avg_intercept = getattr(cfg, "ESTIMATE_AVG_PCT_INTERCEPT", 80.0)
    avg_slope = getattr(cfg, "ESTIMATE_AVG_PCT_SLOPE", 50.0)

    raw_pass_pct = pass_intercept - pass_slope * d_difficulty
    clamped_pass_pct = max(0.0, min(100.0, raw_pass_pct))

    raw_avg_pct = avg_intercept - avg_slope * d_difficulty
    clamped_avg_pct = max(0.0, min(100.0, raw_avg_pct))

    raw_avg_marks = (clamped_avg_pct / 100.0) * max_marks_float
    clamped_avg_marks = max(0.0, min(max_marks_float, raw_avg_marks))

    # Round to 1 decimal place at output only
    final_pass_pct = round(clamped_pass_pct, 1)
    final_avg_marks = round(clamped_avg_marks, 1)

    return PerformanceEstimateResponse(
        estimated_pass_percentage=final_pass_pct,
        estimated_average_marks=final_avg_marks,
        reason=None,
    )


class PerformanceEstimationService:
    """
    Service for calculating heuristic estimated student performance for analyzed question papers.
    Read-only: does not commit or persist estimates to the database.
    """

    @classmethod
    async def get_estimate_for_paper(
        cls,
        db: AsyncSession,
        paper_id: int,
    ) -> Optional[PerformanceEstimateResponse]:
        """
        Loads the paper and its questions via SQLAlchemy async, and computes the estimate.
        Returns None if paper does not exist (allowing route to return 404).
        """
        stmt = (
            select(QuestionPaper)
            .options(
                selectinload(QuestionPaper.questions).selectinload(Question.effective_bloom_level),
                selectinload(QuestionPaper.questions).selectinload(Question.human_bloom_level),
                selectinload(QuestionPaper.questions).selectinload(Question.ai_bloom_level),
            )
            .where(QuestionPaper.id == paper_id)
        )
        paper = (await db.execute(stmt)).scalar_one_or_none()
        if not paper:
            return None

        is_completed = (paper.processing_status == "COMPLETED")
        return compute_performance_estimate_core(
            paper_max_marks=paper.maximum_marks,
            questions=paper.questions,
            config=settings,
            is_completed=is_completed,
        )
