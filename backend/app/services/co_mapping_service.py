import concurrent.futures
import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import logger
from app.models.course import Course
from app.models.course_outcome import CourseOutcome
from app.models.question import Question
from app.models.question_course_outcome import QuestionCourseOutcome
from app.models.question_paper import QuestionPaper
from app.schemas.co_mapping import (
    COMappingCandidate,
    QuestionCOMappingResult,
    GeminiCOMappingResponse,
)
from app.services.bloom_service import BloomService, BLOOM_LEVEL_MAP
from app.services.co_extraction_service import COExtractionService
from app.services.embedding_service import EmbeddingService


STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "can", "will", "just", "should", "now", "be", "have", "has", "had", "do",
    "does", "did", "are", "was", "were", "been", "being", "explain", "describe",
    "write", "short", "note", "notes", "following", "given", "with", "respect",
}


class COMappingService:
    """
    Production Hybrid Course Outcome (CO) Mapping Service.
    Combines:
    1. Dense Semantic Vector Cosine Similarity
    2. Domain Concept & Technical Keyword Overlap
    3. Bloom Cognitive Consistency Level Alignment
    4. Weighted Multi-Signal Aggregation
    5. Bounded Gemini LLM Fallback Verification
    """

    @classmethod
    def _extract_concept_tokens(cls, text: str) -> set:
        """Extracts cleaned normalized keywords/concepts excluding stopwords."""
        if not text:
            return set()
        words = re.findall(r"\b[a-zA-Z0-9_\-\+]{2,}\b", text.lower())
        return {w for w in words if w not in STOPWORDS and not w.isdigit()}

    @classmethod
    def _calculate_semantic_score(
        cls,
        q_emb: Optional[np.ndarray],
        co_emb: Optional[np.ndarray],
    ) -> float:
        """Calculates normalized cosine similarity between question and CO embeddings."""
        if q_emb is None or co_emb is None:
            return 0.0

        sim = float(np.dot(q_emb, co_emb))
        # Embeddings from MiniLM are L2 normalized; bound to [0.0, 1.0]
        return float(max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim)))

    @classmethod
    def _calculate_concept_score(cls, q_text: str, co_desc: str) -> float:
        """
        Calculates concept and technical keyword overlap score.
        Uses Jaccard overlap + subphrase substring matching.
        """
        q_tokens = cls._extract_concept_tokens(q_text)
        co_tokens = cls._extract_concept_tokens(co_desc)

        if not q_tokens or not co_tokens:
            return 0.0

        intersection = q_tokens.intersection(co_tokens)
        if not intersection:
            return 0.0

        # Overlap relative to the smaller set + Jaccard term
        overlap_coef = len(intersection) / min(len(q_tokens), len(co_tokens))
        jaccard = len(intersection) / len(q_tokens.union(co_tokens))
        base_score = 0.6 * overlap_coef + 0.4 * jaccard

        # Keyword matching bonus if 2+ domain terms match
        if len(intersection) >= 2:
            base_score = min(1.0, base_score + 0.15)

        return float(min(1.0, max(0.0, base_score)))

    @classmethod
    def _calculate_bloom_consistency(
        cls,
        question_bloom_level: Optional[str],
        co_desc: str,
    ) -> float:
        """
        Evaluates cognitive alignment between Question Bloom level and CO Bloom level.
        Exact match = 1.0, Adjacent level (diff=1) = 0.80, diff=2 = 0.55, diff>=3 = 0.30.
        """
        co_bloom = COExtractionService.estimate_bloom_level(co_desc)

        if not question_bloom_level or not co_bloom:
            return 0.70  # Neutral consistency score if either level is unknown

        q_lvl_num = BLOOM_LEVEL_MAP.get(question_bloom_level.upper())
        co_lvl_num = BLOOM_LEVEL_MAP.get(co_bloom.upper())

        if q_lvl_num is None or co_lvl_num is None:
            return 0.70

        diff = abs(q_lvl_num - co_lvl_num)
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.80
        elif diff == 2:
            return 0.55
        elif diff == 3:
            return 0.35
        else:
            return 0.20

    @classmethod
    def map_question(
        cls,
        question_text: str,
        course_outcomes: List[Union[CourseOutcome, Dict[str, Any]]],
        question_bloom_level: Optional[str] = None,
        question_id: Optional[int] = None,
        top_k: int = 3,
    ) -> QuestionCOMappingResult:
        """
        Maps a single question text against a list of candidate Course Outcomes.
        Returns a QuestionCOMappingResult containing ranked candidates and multi-factor scores.
        """
        if not question_text or not question_text.strip() or not course_outcomes:
            return QuestionCOMappingResult(
                question_id=question_id,
                question_text=question_text or "",
                question_bloom_level=question_bloom_level,
                primary_outcome=None,
                candidates=[],
                ai_confidence=0.0,
                llm_verified="skipped",
                is_mapped=False,
            )

        # 1. Infer Question Bloom Level if not provided
        if not question_bloom_level:
            try:
                bloom_res = BloomService.classify_question(question_text)
                question_bloom_level = bloom_res.primary_level
            except Exception as e:
                logger.warning(f"Error classifying question Bloom level for CO mapping: {e}")
                question_bloom_level = "L1"

        # 2. Compute Embeddings
        q_emb = EmbeddingService.get_embedding(question_text)

        w_sem = settings.CO_MAPPING_WEIGHT_SEMANTIC
        w_concept = settings.CO_MAPPING_WEIGHT_CONCEPT
        w_bloom = settings.CO_MAPPING_WEIGHT_BLOOM

        candidates: List[COMappingCandidate] = []

        for co in course_outcomes:
            co_id = co.id if hasattr(co, "id") else co.get("id", 0)
            co_code = co.code if hasattr(co, "code") else co.get("code", "")
            co_desc = co.description if hasattr(co, "description") else co.get("description", "")

            # A. Semantic Score
            co_emb = EmbeddingService.get_embedding(co_desc)
            sem_score = cls._calculate_semantic_score(q_emb, co_emb)

            # B. Concept Score
            concept_score = cls._calculate_concept_score(question_text, co_desc)

            # C. Bloom Consistency
            bloom_score = cls._calculate_bloom_consistency(question_bloom_level, co_desc)

            # D. Weighted Final Score
            final_score = (w_sem * sem_score) + (w_concept * concept_score) + (w_bloom * bloom_score)
            final_score = float(min(1.0, max(0.0, final_score)))

            candidates.append(
                COMappingCandidate(
                    course_outcome_id=co_id,
                    code=co_code,
                    description=co_desc,
                    semantic_score=round(sem_score, 4),
                    concept_score=round(concept_score, 4),
                    bloom_consistency_score=round(bloom_score, 4),
                    final_score=round(final_score, 4),
                    rank=1,
                )
            )

        # 3. Sort candidates by final score descending
        candidates.sort(key=lambda c: c.final_score, reverse=True)
        for idx, candidate in enumerate(candidates):
            candidate.rank = idx + 1

        top_candidates = candidates[:top_k]
        top_c = top_candidates[0] if top_candidates else None

        # 4. Confidence Calculation
        if len(candidates) == 1:
            confidence = candidates[0].final_score
        elif len(candidates) >= 2:
            margin = candidates[0].final_score - candidates[1].final_score
            confidence = float(min(0.98, max(0.25, candidates[0].final_score * 0.7 + margin * 0.3 + 0.10)))
        else:
            confidence = 0.0

        confidence = round(confidence, 4)
        is_mapped = bool(top_c and top_c.final_score >= settings.CO_MAPPING_MATCH_THRESHOLD)

        result = QuestionCOMappingResult(
            question_id=question_id,
            question_text=question_text,
            question_bloom_level=question_bloom_level,
            primary_outcome=top_c,
            candidates=top_candidates,
            ai_confidence=confidence,
            llm_verified="not_required" if confidence >= settings.CO_MAPPING_VERIFICATION_THRESHOLD else "pending",
            is_mapped=is_mapped,
        )

        # 5. Gemini LLM Fallback Verification if low confidence
        if confidence < settings.CO_MAPPING_VERIFICATION_THRESHOLD and settings.GEMINI_API_KEY:
            gemini_res = cls._verify_with_gemini(question_text, course_outcomes, result)
            if gemini_res:
                return gemini_res
            result.llm_verified = "skipped"

        return result

    @classmethod
    def _verify_with_gemini(
        cls,
        question_text: str,
        course_outcomes: List[Any],
        initial_result: QuestionCOMappingResult,
    ) -> Optional[QuestionCOMappingResult]:
        """
        Performs bounded fallback verification using Gemini SDK (`google-genai`)
        with a strict 10s timeout.
        """
        if not settings.GEMINI_API_KEY:
            return None

        co_list_text = "\n".join([
            f"- {getattr(co, 'code', co.get('code', ''))}: {getattr(co, 'description', co.get('description', ''))}"
            for co in course_outcomes
        ])

        top_code = initial_result.primary_outcome.code if initial_result.primary_outcome else "None"

        prompt = f"""
Act as an academic curriculum and examination specialist.
Map the following examination question to the most appropriate Course Outcome (CO).

Question:
"{question_text}"

Available Course Outcomes:
{co_list_text}

Initial Hybrid AI suggestion: {top_code}

Evaluate the alignment based on topic domain, technical concept, and cognitive operation.
Return ONLY a valid JSON object matching this structure:
{{
  "selected_co_code": "CO1",
  "confidence": 0.90,
  "is_valid_mapping": true,
  "reason": "Detailed academic justification for mapping this question to this CO."
}}
"""
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                response = future.result(timeout=10.0)

            if response and response.text:
                json_str = response.text.strip()
                if json_str.startswith("```"):
                    json_str = re.sub(r"^```[a-z]*\n|\n```$", "", json_str, flags=re.IGNORECASE)

                data = json.loads(json_str)
                validated = GeminiCOMappingResponse(**data)

                # Find candidate matching Gemini selection
                matched_candidate = next(
                    (c for c in initial_result.candidates if c.code.upper() == validated.selected_co_code.upper()),
                    None,
                )

                if matched_candidate and validated.is_valid_mapping:
                    initial_result.primary_outcome = matched_candidate
                    initial_result.ai_confidence = round(validated.confidence, 4)
                    initial_result.llm_verified = "verified"
                    initial_result.llm_reason = validated.reason
                    initial_result.is_mapped = True
                    return initial_result
                elif not validated.is_valid_mapping:
                    initial_result.llm_verified = "rejected"
                    initial_result.llm_reason = validated.reason
                    return initial_result

        except Exception as e:
            logger.warning(f"Gemini CO mapping fallback failed gracefully: {e}")

        return None

    @classmethod
    async def map_batch_questions(
        cls,
        questions: List[Union[Question, Dict[str, Any]]],
        course_outcomes: List[CourseOutcome],
        top_k: int = 3,
    ) -> List[QuestionCOMappingResult]:
        """Maps a list of questions against course outcomes."""
        results = []
        for q in questions:
            if isinstance(q, dict):
                q_id = q.get("id")
                q_text = q.get("original_text", "")
                q_bloom = q.get("bloom_level_code") or q.get("bloom_level")
            else:
                q_id = getattr(q, "id", None)
                q_text = getattr(q, "original_text", "")
                q_bloom = None
                if hasattr(q, "effective_bloom_level") and q.effective_bloom_level:
                    q_bloom = q.effective_bloom_level.level_code
                elif hasattr(q, "bloom_level_code"):
                    q_bloom = q.bloom_level_code

            res = cls.map_question(
                question_text=q_text,
                course_outcomes=course_outcomes,
                question_bloom_level=q_bloom,
                question_id=q_id,
                top_k=top_k,
            )
            results.append(res)
        return results

    @classmethod
    async def map_and_persist_question_paper(
        cls,
        db: AsyncSession,
        paper_id: int,
        course_id: Optional[int] = None,
        top_k: int = 1,
        threshold: float = 0.40,
    ) -> List[QuestionCourseOutcome]:
        """
        Maps all questions of a QuestionPaper to the outcomes of its associated Course
        and persists QuestionCourseOutcome records in the database.
        """
        paper_stmt = (
            select(QuestionPaper)
            .where(QuestionPaper.id == paper_id)
            .options(
                selectinload(QuestionPaper.questions).selectinload(Question.effective_bloom_level)
            )
        )
        paper = (await db.execute(paper_stmt)).scalar_one_or_none()
        if not paper:
            raise ValueError(f"QuestionPaper with ID {paper_id} not found.")

        target_course_id = course_id or paper.course_id
        if not target_course_id:
            raise ValueError(f"No Course associated with QuestionPaper {paper_id}.")

        # Update paper course_id if different
        if paper.course_id != target_course_id:
            paper.course_id = target_course_id

        # Fetch course outcomes
        cos_stmt = select(CourseOutcome).where(CourseOutcome.course_id == target_course_id).order_by(CourseOutcome.sort_order)
        course_outcomes = (await db.execute(cos_stmt)).scalars().all()

        if not course_outcomes:
            logger.warning(f"No CourseOutcomes found for Course ID {target_course_id}")
            return []

        # Map each question
        persisted_mappings: List[QuestionCourseOutcome] = []
        for question in paper.questions:
            bloom_lvl = question.effective_bloom_level.level_code if question.effective_bloom_level else None
            map_res = cls.map_question(
                question_text=question.original_text,
                course_outcomes=course_outcomes,
                question_bloom_level=bloom_lvl,
                question_id=question.id,
                top_k=top_k,
            )

            # Persist top_k outcomes if above threshold
            for candidate in map_res.candidates[:top_k]:
                if candidate.final_score >= threshold:
                    # Check if mapping already exists
                    existing_stmt = select(QuestionCourseOutcome).where(
                        QuestionCourseOutcome.question_id == question.id,
                        QuestionCourseOutcome.course_outcome_id == candidate.course_outcome_id,
                    )
                    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

                    if existing:
                        existing.semantic_score = candidate.semantic_score
                        existing.concept_score = candidate.concept_score
                        existing.bloom_consistency_score = candidate.bloom_consistency_score
                        existing.final_score = candidate.final_score
                        existing.ai_confidence = map_res.ai_confidence
                        existing.llm_verified = map_res.llm_verified
                        existing.llm_reason = map_res.llm_reason
                        persisted_mappings.append(existing)
                    else:
                        new_mapping = QuestionCourseOutcome(
                            question_id=question.id,
                            course_outcome_id=candidate.course_outcome_id,
                            semantic_score=candidate.semantic_score,
                            concept_score=candidate.concept_score,
                            bloom_consistency_score=candidate.bloom_consistency_score,
                            final_score=candidate.final_score,
                            ai_confidence=map_res.ai_confidence,
                            llm_verified=map_res.llm_verified,
                            llm_reason=map_res.llm_reason,
                            human_verified=False,
                            human_override=False,
                        )
                        db.add(new_mapping)
                        persisted_mappings.append(new_mapping)

        await db.commit()
        for m in persisted_mappings:
            await db.refresh(m)

        logger.info(
            f"Successfully mapped {len(persisted_mappings)} CO connections for Paper {paper_id} and Course {target_course_id}"
        )
        return persisted_mappings

    @classmethod
    async def map_and_persist_questions(
        cls,
        db: AsyncSession,
        question_ids: List[int],
        course_id: int,
        top_k: int = 1,
        threshold: float = 0.40,
    ) -> List[QuestionCourseOutcome]:
        """Maps specific questions by ID to a course's outcomes and persists them."""
        q_stmt = (
            select(Question)
            .where(Question.id.in_(question_ids))
            .options(selectinload(Question.effective_bloom_level))
        )
        questions = (await db.execute(q_stmt)).scalars().all()
        if not questions:
            return []

        cos_stmt = select(CourseOutcome).where(CourseOutcome.course_id == course_id).order_by(CourseOutcome.sort_order)
        course_outcomes = (await db.execute(cos_stmt)).scalars().all()
        if not course_outcomes:
            raise ValueError(f"No CourseOutcomes found for Course ID {course_id}")

        persisted: List[QuestionCourseOutcome] = []
        for question in questions:
            bloom_lvl = question.effective_bloom_level.level_code if question.effective_bloom_level else None
            map_res = cls.map_question(
                question_text=question.original_text,
                course_outcomes=course_outcomes,
                question_bloom_level=bloom_lvl,
                question_id=question.id,
                top_k=top_k,
            )

            for candidate in map_res.candidates[:top_k]:
                if candidate.final_score >= threshold:
                    existing_stmt = select(QuestionCourseOutcome).where(
                        QuestionCourseOutcome.question_id == question.id,
                        QuestionCourseOutcome.course_outcome_id == candidate.course_outcome_id,
                    )
                    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

                    if existing:
                        existing.semantic_score = candidate.semantic_score
                        existing.concept_score = candidate.concept_score
                        existing.bloom_consistency_score = candidate.bloom_consistency_score
                        existing.final_score = candidate.final_score
                        existing.ai_confidence = map_res.ai_confidence
                        existing.llm_verified = map_res.llm_verified
                        existing.llm_reason = map_res.llm_reason
                        persisted.append(existing)
                    else:
                        new_mapping = QuestionCourseOutcome(
                            question_id=question.id,
                            course_outcome_id=candidate.course_outcome_id,
                            semantic_score=candidate.semantic_score,
                            concept_score=candidate.concept_score,
                            bloom_consistency_score=candidate.bloom_consistency_score,
                            final_score=candidate.final_score,
                            ai_confidence=map_res.ai_confidence,
                            llm_verified=map_res.llm_verified,
                            llm_reason=map_res.llm_reason,
                            human_verified=False,
                            human_override=False,
                        )
                        db.add(new_mapping)
                        persisted.append(new_mapping)

        await db.commit()
        for m in persisted:
            await db.refresh(m)

        return persisted
