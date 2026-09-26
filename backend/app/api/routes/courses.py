import os
import tempfile
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, AuthenticatedUser
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseWithOutcomesResponse,
    CourseListResponse,
    CourseOutcomeCreate,
    CourseOutcomeResponse,
    CourseOutcomeListResponse,
    CourseBulkOutcomeRequest,
    COExtractTextRequest,
    COExtractedItem,
    COExtractionPreviewResponse,
    COImportConfirmRequest,
    COImportConfirmResponse,
)
from app.schemas.co_mapping import (
    QuestionCOMappingRequest,
    QuestionCOMappingResult,
    BatchCOPaperMappingRequest,
    BatchCOMappingResponse,
    QuestionCOMappingRecordResponse,
)
from app.services.course_service import CourseService
from app.services.co_extraction_service import COExtractionService
from app.services.co_mapping_service import COMappingService
from app.models.question_course_outcome import QuestionCourseOutcome
from app.models.course_outcome import CourseOutcome
from app.models.question import Question
from app.models.question_paper import QuestionPaper
from sqlalchemy import select
from sqlalchemy.orm import selectinload


router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=CourseListResponse)
async def list_courses(
    search: Optional[str] = Query(None, description="Search courses by code, name, or description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Lists courses with pagination and optional search filter."""
    skip = (page - 1) * limit
    items, total = await CourseService.get_courses(db, skip=skip, limit=limit, search=search)
    return CourseListResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Creates a new course (Auth required)."""
    course = await CourseService.create_course(db, data)
    return CourseResponse(
        id=course.id,
        course_code=course.course_code,
        course_name=course.course_name,
        description=course.description,
        created_at=course.created_at,
        updated_at=course.updated_at,
        outcomes_count=0,
    )


@router.get("/{course_id}", response_model=CourseWithOutcomesResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves a single course by ID including its course outcomes."""
    course = await CourseService.get_course_by_id(db, course_id, include_outcomes=True)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    return CourseWithOutcomesResponse(
        id=course.id,
        course_code=course.course_code,
        course_name=course.course_name,
        description=course.description,
        created_at=course.created_at,
        updated_at=course.updated_at,
        outcomes_count=len(course.outcomes) if course.outcomes else 0,
        outcomes=[CourseOutcomeResponse.model_validate(co) for co in (course.outcomes or [])],
    )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Updates a course by ID (Auth required)."""
    course = await CourseService.update_course(db, course_id, data)
    return CourseResponse(
        id=course.id,
        course_code=course.course_code,
        course_name=course.course_name,
        description=course.description,
        created_at=course.created_at,
        updated_at=course.updated_at,
        outcomes_count=len(course.outcomes) if course.outcomes else 0,
    )


@router.delete("/{course_id}", status_code=status.HTTP_200_OK)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Deletes a course and cascades deletion of its outcomes (Auth required)."""
    await CourseService.delete_course(db, course_id)
    return {"message": f"Course {course_id} deleted successfully."}


@router.get("/{course_id}/outcomes", response_model=CourseOutcomeListResponse)
async def get_course_outcomes(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Lists all outcomes for a specific course."""
    outcomes = await CourseService.get_course_outcomes(db, course_id)
    items = [CourseOutcomeResponse.model_validate(co) for co in outcomes]
    return CourseOutcomeListResponse(items=items, total=len(items))


@router.post("/{course_id}/outcomes", response_model=CourseOutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_course_outcome(
    course_id: int,
    data: CourseOutcomeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Adds a course outcome to a specific course (Auth required)."""
    co = await CourseService.create_course_outcome(db, course_id, data)
    return CourseOutcomeResponse.model_validate(co)


@router.put("/{course_id}/outcomes/bulk", response_model=CourseOutcomeListResponse)
async def bulk_update_course_outcomes(
    course_id: int,
    payload: CourseBulkOutcomeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Bulk replaces all outcomes for a specific course (Auth required)."""
    outcomes = await CourseService.bulk_create_or_replace_outcomes(db, course_id, payload.outcomes)
    items = [CourseOutcomeResponse.model_validate(co) for co in outcomes]
    return CourseOutcomeListResponse(items=items, total=len(items))


# ---------------- CO Import Flow (Preview & Confirmation) ---------------- #

@router.post("/{course_id}/outcomes/extract-preview/text", response_model=COExtractionPreviewResponse)
async def extract_preview_cos_from_text(
    course_id: int,
    payload: COExtractTextRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Extracts candidate Course Outcomes from raw syllabus text for review.
    Does NOT write or modify the database.
    """
    course = await CourseService.get_course_by_id(db, course_id, include_outcomes=False)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    raw_candidates = COExtractionService.extract_cos_from_text(payload.text)
    extracted_items = [COExtractedItem(**item) for item in raw_candidates]

    snippet = payload.text[:300] + "..." if len(payload.text) > 300 else payload.text

    return COExtractionPreviewResponse(
        course_id=course.id,
        course_code=course.course_code,
        extracted_outcomes=extracted_items,
        total_extracted=len(extracted_items),
        source_type="text",
        raw_text_snippet=snippet,
    )


@router.post("/{course_id}/outcomes/extract-preview/file", response_model=COExtractionPreviewResponse)
async def extract_preview_cos_from_file(
    course_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Extracts candidate Course Outcomes from an uploaded PDF, DOCX, or TXT syllabus document.
    Does NOT write or modify the database.
    """
    course = await CourseService.get_course_by_id(db, course_id, include_outcomes=False)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Supported formats: .pdf, .docx, .txt",
        )

    # Save to temp file
    temp_dir = tempfile.mkdtemp(prefix="co_import_")
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        content = await file.read()
        if not content or len(content) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        with open(temp_path, "wb") as f:
            f.write(content)

        raw_candidates = COExtractionService.extract_cos_from_file(temp_path)
        extracted_items = [COExtractedItem(**item) for item in raw_candidates]

        return COExtractionPreviewResponse(
            course_id=course.id,
            course_code=course.course_code,
            extracted_outcomes=extracted_items,
            total_extracted=len(extracted_items),
            source_type="file",
            raw_text_snippet=file.filename,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


@router.post("/{course_id}/outcomes/confirm-import", response_model=COImportConfirmResponse)
async def confirm_import_course_outcomes(
    course_id: int,
    payload: COImportConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Persists user-verified and edited Course Outcomes to the database.
    Supports mode='replace' or mode='append'.
    """
    saved_cos = await CourseService.import_confirmed_outcomes(
        db, course_id, payload.outcomes, mode=payload.mode
    )
    items = [CourseOutcomeResponse.model_validate(co) for co in saved_cos]

    msg = f"Successfully imported {len(items)} outcomes into course (mode={payload.mode})."
    return COImportConfirmResponse(
        course_id=course_id,
        mode=payload.mode,
        saved_outcomes=items,
        total_saved=len(items),
        message=msg,
    )


@router.post("/{course_id}/map-question", response_model=QuestionCOMappingResult)
async def map_single_question_to_course(
    course_id: int,
    payload: QuestionCOMappingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Dry-run maps a question text against course outcomes using the 5-stage Hybrid CO mapping engine.
    Does not persist to database.
    """
    course = await CourseService.get_course_by_id(db, course_id, include_outcomes=True)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    if not course.outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with ID {course_id} has no defined Course Outcomes to map against.",
        )

    result = COMappingService.map_question(
        question_text=payload.question_text,
        course_outcomes=course.outcomes,
        question_bloom_level=payload.bloom_level,
        top_k=3,
    )
    return result


@router.post("/{course_id}/map-paper/{paper_id}", response_model=BatchCOMappingResponse)
async def map_paper_questions_to_course(
    course_id: int,
    paper_id: int,
    payload: Optional[BatchCOPaperMappingRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Batch maps all questions of a QuestionPaper to Course Outcomes and persists QuestionCourseOutcome records.
    (Auth required).
    """
    course = await CourseService.get_course_by_id(db, course_id, include_outcomes=True)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    if not course.outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with ID {course_id} has no defined Course Outcomes.",
        )

    top_k = payload.top_k if payload else 1
    threshold = payload.threshold if (payload and payload.threshold is not None) else 0.40

    try:
        persisted = await COMappingService.map_and_persist_question_paper(
            db=db,
            paper_id=paper_id,
            course_id=course_id,
            top_k=top_k,
            threshold=threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Also map questions for response preview
    paper_stmt = (
        select(QuestionPaper)
        .where(QuestionPaper.id == paper_id)
        .options(selectinload(QuestionPaper.questions).selectinload(Question.effective_bloom_level))
    )
    paper = (await db.execute(paper_stmt)).scalar_one_or_none()
    questions = paper.questions if paper else []

    results = await COMappingService.map_batch_questions(questions, course.outcomes, top_k=top_k)

    return BatchCOMappingResponse(
        course_id=course_id,
        paper_id=paper_id,
        total_questions=len(questions),
        mapped_questions=len(persisted),
        results=results,
    )


@router.get("/{course_id}/mappings", response_model=List[QuestionCOMappingRecordResponse])
async def get_course_question_mappings(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves all persisted QuestionCourseOutcome mapping records for a course.
    """
    course = await CourseService.get_course_by_id(db, course_id, include_outcomes=False)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    stmt = (
        select(QuestionCourseOutcome)
        .join(CourseOutcome, QuestionCourseOutcome.course_outcome_id == CourseOutcome.id)
        .where(CourseOutcome.course_id == course_id)
        .order_by(QuestionCourseOutcome.id.asc())
    )
    records = (await db.execute(stmt)).scalars().all()

    # Load outcome codes
    cos_map = {co.id: co for co in (await db.execute(select(CourseOutcome).where(CourseOutcome.course_id == course_id))).scalars().all()}

    res = []
    for r in records:
        co = cos_map.get(r.course_outcome_id)
        res.append(
            QuestionCOMappingRecordResponse(
                id=r.id,
                question_id=r.question_id,
                course_outcome_id=r.course_outcome_id,
                course_outcome_code=co.code if co else None,
                course_outcome_description=co.description if co else None,
                semantic_score=r.semantic_score,
                concept_score=r.concept_score,
                bloom_consistency_score=r.bloom_consistency_score,
                final_score=r.final_score,
                ai_confidence=r.ai_confidence,
                llm_verified=r.llm_verified,
                llm_reason=r.llm_reason,
                human_verified=r.human_verified,
                human_override=r.human_override,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return res


