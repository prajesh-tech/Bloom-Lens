from typing import List, Optional
from fastapi import BackgroundTasks, APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user, AuthenticatedUser
from app.core.errors import raise_api_error
from app.core.upload_limits import upload_limiter
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.schemas.paper import PaperResponse, PaperStatusResponse, PaperListResponse, PerformanceEstimateResponse
from app.services.performance_estimation_service import PerformanceEstimationService
from app.services.paper_processing_service import dispatcher, remove_stored_file
from app.utils.validators import store_and_validate_upload, SUPPORTED_EXAM_TYPES

router = APIRouter(prefix="/papers", tags=["Question Papers"], dependencies=[Depends(get_current_user)])


@router.get("/exam-types", response_model=List[str])
async def get_exam_types(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Canonical examination types accepted by upload validation."""
    return SUPPORTED_EXAM_TYPES


@router.post("/upload", response_model=PaperResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_question_paper(
    background_tasks: BackgroundTasks,
    subject_code: str = Form(...),
    subject_name: str = Form(...),
    examination_type: str = Form(...),
    maximum_marks: float = Form(...),
    year_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    upload_limiter.check(current_user.user_id)
    orig_filename, file_path, file_hash = await store_and_validate_upload(file, maximum_marks, examination_type)
    try:
        code = subject_code.strip().upper()
        if not code or not subject_name.strip():
            raise_api_error(400, "InvalidSubject", "Subject code and name are required.")
        subject = (await db.execute(select(Subject).where(Subject.code == code))).scalar_one_or_none()
        if subject is None:
            try:
                async with db.begin_nested():
                    subject = Subject(code=code, name=subject_name.strip())
                    db.add(subject)
                    await db.flush()
            except IntegrityError:
                subject = (await db.execute(select(Subject).where(Subject.code == code))).scalar_one()
        paper = QuestionPaper(subject_id=subject.id, examination_type=examination_type.strip(),
            maximum_marks=maximum_marks, original_filename=orig_filename, stored_file_path=file_path,
            file_hash=file_hash, year_date=year_date.strip() if year_date else None, processing_status="UPLOADED")
        db.add(paper)
        subject_id, subject_code, subject_name = subject.id, subject.code, subject.name
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise_api_error(409, "DuplicatePaper", "This file has already been uploaded for this subject.")
        response = PaperResponse.model_validate(paper)
        response.subject_id = subject_id
        response.subject_code = subject_code
        response.subject_name = subject_name
        response.status_url = f"{settings.API_V1_STR}/papers/{paper.id}/status"
        dispatcher.enqueue(background_tasks, paper.id)
        return response
    except Exception:
        await db.rollback()
        await remove_stored_file(file_path)
        raise


@router.get("", response_model=PaperListResponse)
async def list_question_papers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lists question papers with pagination metadata."""
    offset = (page - 1) * limit
    total_stmt = select(func.count(QuestionPaper.id))
    total = (await db.execute(total_stmt)).scalar() or 0

    query = (
        select(QuestionPaper)
        .options(selectinload(QuestionPaper.subject), selectinload(QuestionPaper.questions))
        .order_by(QuestionPaper.upload_timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    papers = result.scalars().all()

    items = [
        PaperResponse(
            id=p.id,
            subject_id=p.subject_id,
            subject_code=p.subject.code if p.subject else None,
            subject_name=p.subject.name if p.subject else None,
            examination_type=p.examination_type,
            maximum_marks=p.maximum_marks,
            original_filename=p.original_filename,
            upload_timestamp=p.upload_timestamp,
            year_date=p.year_date,
            processing_status=p.processing_status,
            extraction_status=p.extraction_status,
            validation_status=p.validation_status,
            optional_question_flag=p.optional_question_flag,
            validation_metadata=p.validation_metadata,
            total_questions=len(p.questions),
        )
        for p in papers
    ]

    return PaperListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_question_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Fetches single question paper details by ID."""
    stmt = (
        select(QuestionPaper)
        .options(selectinload(QuestionPaper.subject), selectinload(QuestionPaper.questions))
        .where(QuestionPaper.id == paper_id)
    )
    paper = (await db.execute(stmt)).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question paper {paper_id} not found.")

    return PaperResponse(
        id=paper.id,
        subject_id=paper.subject_id,
        subject_code=paper.subject.code if paper.subject else None,
        subject_name=paper.subject.name if paper.subject else None,
        examination_type=paper.examination_type,
        maximum_marks=paper.maximum_marks,
        original_filename=paper.original_filename,
        upload_timestamp=paper.upload_timestamp,
        year_date=paper.year_date,
        processing_status=paper.processing_status,
        extraction_status=paper.extraction_status,
        validation_status=paper.validation_status,
        optional_question_flag=paper.optional_question_flag,
        validation_metadata=paper.validation_metadata,
        total_questions=len(paper.questions),
    )


@router.get("/{paper_id}/status", response_model=PaperStatusResponse)
async def get_paper_status(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint for polling paper processing and mark validation status."""
    stmt = select(QuestionPaper).where(QuestionPaper.id == paper_id)
    paper = (await db.execute(stmt)).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question paper {paper_id} not found.")

    return PaperStatusResponse(
        paper_id=paper.id,
        processing_status=paper.processing_status,
        extraction_status=paper.extraction_status,
        validation_status=paper.validation_status,
        optional_question_flag=paper.optional_question_flag,
        validation_metadata=paper.validation_metadata,
        error_message=paper.error_message,
        message=paper.error_message or f"Paper is currently {paper.processing_status}.",
    )


@router.get("/{paper_id}/performance-estimate", response_model=PerformanceEstimateResponse)
async def get_performance_estimate(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Computes heuristic estimated student performance for an analyzed question paper."""
    estimate = await PerformanceEstimationService.get_estimate_for_paper(db, paper_id)
    if estimate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question paper {paper_id} not found.")

    return estimate


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Deletes a question paper and cascade-removes its questions, topics, similarities, and uploaded file."""
    stmt = select(QuestionPaper).where(QuestionPaper.id == paper_id)
    paper = (await db.execute(stmt)).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question paper {paper_id} not found.")

    file_path = paper.stored_file_path
    await db.delete(paper)
    await db.commit()
    if file_path:
        await remove_stored_file(file_path)
    return None
