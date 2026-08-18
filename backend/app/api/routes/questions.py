from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, distinct, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.question import Question
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.models.topic import Topic, QuestionTopic
from app.models.bloom_level import BloomLevel
from app.models.question_similarity import QuestionSimilarity
from app.schemas.question import (
    QuestionResponse,
    QuestionListResponse,
    QuestionPatchSchema,
    QuestionSimilarityResponse,
)
from app.services.bloom_service import BLOOM_LEVEL_MAP, BLOOM_NAME_MAP
from app.utils.text_cleaner import sanitize_display_text

router = APIRouter(prefix="/questions", tags=["Questions"])


QUESTION_RESPONSE_OPTIONS = (
    selectinload(Question.ai_bloom_level),
    selectinload(Question.human_bloom_level),
    selectinload(Question.effective_bloom_level),
    selectinload(Question.question_topics).selectinload(QuestionTopic.topic),
    selectinload(Question.sub_questions).selectinload(Question.ai_bloom_level),
    selectinload(Question.sub_questions).selectinload(Question.human_bloom_level),
    selectinload(Question.sub_questions).selectinload(Question.effective_bloom_level),
    selectinload(Question.sub_questions).selectinload(Question.question_topics).selectinload(QuestionTopic.topic),
)


def _build_question_response(q: Question, include_children: bool = True) -> QuestionResponse:
    """Helper to convert Question database entity to QuestionResponse Pydantic schema."""
    primary_topic = None
    if q.question_topics and len(q.question_topics) > 0:
        qt = q.question_topics[0]
        if qt.topic:
            primary_topic = qt.topic.name

    sub_qs = [_build_question_response(sub, include_children=False) for sub in (q.sub_questions or [])] if include_children else []

    return QuestionResponse(
        id=q.id,
        question_paper_id=q.question_paper_id,
        parent_question_id=q.parent_question_id,
        question_number=q.question_number,
        original_text=q.original_text,
        normalized_text=q.normalized_text,
        marks=q.marks,
        marks_confidence=q.marks_confidence,
        ai_bloom_level=q.ai_bloom_level.code if q.ai_bloom_level else None,
        human_bloom_level=q.human_bloom_level.code if q.human_bloom_level else None,
        effective_bloom_level=q.effective_bloom_level.code if q.effective_bloom_level else None,
        bloom_confidence=q.bloom_confidence,
        bloom_explanation=q.bloom_explanation,
        ai_question_type=q.ai_question_type,
        human_question_type=q.human_question_type,
        question_type=q.question_type,
        unit=q.unit,
        topic=primary_topic,
        co_mapping=q.co_mapping,
        choice_group=q.choice_group,
        extraction_confidence=q.extraction_confidence,
        review_status=q.review_status,
        ai_analysis_metadata=q.ai_analysis_metadata,
        sub_questions=sub_qs,
    )


@router.get("", response_model=QuestionListResponse)
async def search_and_filter_questions(
    subject: Optional[str] = Query(None, description="Subject code or name"),
    examination_type: Optional[str] = Query(None, description="Exam type"),
    paper: Optional[int] = Query(None, description="Question paper ID"),
    bloom_level: Optional[str] = Query(None, description="Bloom level code e.g. L1, L4"),
    topic: Optional[str] = Query(None, description="Topic name"),
    unit: Optional[str] = Query(None, description="Unit e.g. Unit 1"),
    marks: Optional[float] = Query(None, description="Exact marks"),
    question_type: Optional[str] = Query(None, description="Question type"),
    year_date: Optional[str] = Query(None, description="Year or date"),
    question_text: Optional[str] = Query(None, description="Question text search string"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Database-level paginated search and filtering endpoint for historical questions."""
    query = (
        select(Question)
        .options(*QUESTION_RESPONSE_OPTIONS)
        .join(QuestionPaper)
        .where(Question.parent_question_id.is_(None))  # Fetch top-level main questions
    )

    if paper:
        query = query.where(Question.question_paper_id == paper)

    if examination_type:
        query = query.where(QuestionPaper.examination_type.ilike(f"%{examination_type}%"))

    if year_date:
        query = query.where(QuestionPaper.year_date.ilike(f"%{year_date}%"))

    if subject:
        query = query.join(Subject, QuestionPaper.subject_id == Subject.id).where(
            or_(Subject.code.ilike(f"%{subject}%"), Subject.name.ilike(f"%{subject}%"))
        )

    if bloom_level:
        query = query.join(BloomLevel, Question.effective_bloom_level_id == BloomLevel.id).where(
            BloomLevel.code.ilike(bloom_level.strip())
        )

    if unit:
        query = query.where(Question.unit.ilike(f"%{unit}%"))

    if marks is not None:
        query = query.where(Question.marks == marks)

    if question_type:
        query = query.where(Question.question_type.ilike(f"%{question_type}%"))

    if question_text:
        query = query.where(Question.original_text.ilike(f"%{question_text}%"))

    if topic:
        query = query.join(QuestionTopic).join(Topic).where(Topic.name.ilike(f"%{topic}%"))

    # Count total
    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(Question.id.asc()).offset(offset).limit(limit)

    results = (await db.execute(query)).scalars().all()
    items = [_build_question_response(q) for q in results]

    return QuestionListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question_detail(question_id: int, db: AsyncSession = Depends(get_db)):
    """Fetches detailed question record by ID."""
    stmt = (
        select(Question)
        .options(*QUESTION_RESPONSE_OPTIONS)
        .where(Question.id == question_id)
    )
    q = (await db.execute(stmt)).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found.")

    return _build_question_response(q)


@router.patch("/{question_id}", response_model=QuestionResponse)
async def override_question(
    question_id: int,
    patch: QuestionPatchSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Human-in-the-Loop review and override endpoint.
    Allows manual corrections for text, marks, topic, unit, bloom level, and question type.
    Preserves original AI prediction while updating effective fields.
    """
    stmt = (
        select(Question)
        .options(*QUESTION_RESPONSE_OPTIONS, selectinload(Question.question_paper))
        .where(Question.id == question_id)
    )
    q = (await db.execute(stmt)).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found.")

    is_corrected = False

    if patch.question_text is not None and patch.question_text != q.original_text:
        q.original_text = sanitize_display_text(patch.question_text)
        is_corrected = True

    if patch.marks is not None:
        q.marks = patch.marks
        q.marks_confidence = "high"
        is_corrected = True

    if patch.unit is not None:
        q.unit = patch.unit
        is_corrected = True

    if patch.question_type is not None:
        q.human_question_type = patch.question_type
        q.question_type = patch.question_type
        is_corrected = True

    if patch.bloom_level is not None:
        lvl_code = patch.bloom_level.strip().upper()
        if lvl_code in BLOOM_LEVEL_MAP:
            bl_id = BLOOM_LEVEL_MAP[lvl_code]
            q.human_bloom_level_id = bl_id
            q.effective_bloom_level_id = bl_id
            is_corrected = True
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Bloom level code '{patch.bloom_level}'. Must be one of L1-L6.",
            )

    if patch.topic_name is not None:
        subj_id = q.question_paper.subject_id if q.question_paper else None
        if subj_id:
            top_stmt = select(Topic).where(Topic.subject_id == subj_id, Topic.name == patch.topic_name)
            top_res = await db.execute(top_stmt)
            topic = top_res.scalar_one_or_none()
            if not topic:
                topic = Topic(subject_id=subj_id, name=patch.topic_name)
                db.add(topic)
                await db.flush()

            # Remove existing primary topic association and reassign
            db.add(QuestionTopic(question_id=q.id, topic_id=topic.id, confidence=1.0, is_primary=True))
            is_corrected = True

    if is_corrected:
        q.review_status = "CORRECTED"

    await db.commit()
    await db.refresh(q)

    # Re-query with loaded relations
    updated_q = (await db.execute(stmt)).scalar_one()
    return _build_question_response(updated_q)
