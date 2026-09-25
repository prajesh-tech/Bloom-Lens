import os
import uuid
import asyncio
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user, AuthenticatedUser
from app.core.logging import logger
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.models.question import Question
from app.models.topic import Topic, QuestionTopic
from app.models.question_similarity import QuestionSimilarity
from app.models.bloom_level import BloomLevel
from app.schemas.paper import PaperResponse, PaperStatusResponse, PaperListResponse
from app.schemas.question import QuestionResponse
from app.services.document_service import DocumentService
from app.services.question_extraction_service import QuestionExtractionService
from app.services.topic_service import TopicService
from app.services.bloom_service import BloomService, BLOOM_LEVEL_MAP
from app.services.similarity_service import SimilarityService
from app.services.embedding_service import EmbeddingService
from app.core.errors import raise_api_error
from app.core.metrics import metrics
from app.utils.validators import read_and_validate_upload, SUPPORTED_EXAM_TYPES, safe_upload_path
from app.utils.text_cleaner import extract_year_from_text, normalize_question_text, sanitize_display_text

router = APIRouter(prefix="/papers", tags=["Question Papers"])


@router.post("/upload", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
async def upload_question_paper(
    subject_code: str = Form(..., description="Subject code e.g. CS301"),
    subject_name: str = Form(..., description="Subject name e.g. Database Systems"),
    examination_type: str = Form(..., description="Exam type e.g. Mid-Term, End-Semester"),
    maximum_marks: float = Form(..., description="Maximum paper marks > 0"),
    year_date: Optional[str] = Form(None, description="Year or Date e.g. 2024"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Uploads, parses, and analyzes a PDF or DOCX question paper."""
    # 1. Validation
    upload_started_at = time.perf_counter()
    orig_filename, ext, content = await read_and_validate_upload(file, maximum_marks, examination_type)

    # 2. Ensure UPLOAD_DIR exists
    unique_filename = f"{uuid.uuid4().hex}_{orig_filename}"
    file_path = safe_upload_path(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 3. Find or Create Subject safely
    subj_code_clean = subject_code.strip().upper()
    subj_stmt = select(Subject).where(Subject.code == subj_code_clean)
    subj_res = await db.execute(subj_stmt)
    subject = subj_res.scalar_one_or_none()

    if not subject:
        try:
            async with db.begin_nested():
                subject = Subject(code=subj_code_clean, name=subject_name.strip())
                db.add(subject)
                await db.flush()
        except IntegrityError:
            subj_res = await db.execute(subj_stmt)
            subject = subj_res.scalar_one_or_none()

    # 4. Create QuestionPaper record
    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type=examination_type.strip(),
        maximum_marks=maximum_marks,
        original_filename=orig_filename,
        stored_file_path=file_path,
        year_date=year_date.strip() if year_date else None,
        processing_status="PROCESSING",
        extraction_status="PENDING",
        validation_status="NOT_VALIDATED",
    )
    db.add(paper)
    await db.flush()

    try:
        # 5. Extract document text using threadpool
        analysis_started_at = time.perf_counter()
        doc_result = await asyncio.to_thread(DocumentService.process_document, file_path)
        full_text = sanitize_display_text(doc_result["full_text"])

        if not paper.year_date:
            paper.year_date = extract_year_from_text(full_text) or extract_year_from_text(orig_filename)

        # 6. Extract questions & marks using threadpool
        raw_questions = await asyncio.to_thread(QuestionExtractionService.extract_questions, full_text)
        paper.extraction_status = "SUCCESS" if raw_questions else "FAILED"
        paper.processing_status = "ANALYZING"

        # 7. Validate Paper Marks
        val_info = QuestionExtractionService.validate_paper_marks(maximum_marks, raw_questions, full_text)
        paper.validation_status = val_info["status"]
        paper.optional_question_flag = val_info["optional_question_flag"]
        paper.validation_metadata = val_info

        # 8. Fix 1: Parallelize per-question CPU work (Bloom + Topic + Unit).
        #    All classifiers are pure CPU functions — run them concurrently in worker threads.
        def _classify_question(q_text: str, subj_name: str):
            """Runs all CPU-bound classifiers for one question in a worker thread."""
            unit_val = TopicService.identify_unit(q_text)
            topic_name, topic_conf = TopicService.identify_topic(q_text, subj_name)
            q_type, _ = TopicService.classify_question_type(q_text)
            bloom_res = BloomService.classify_question(q_text)
            return unit_val, topic_name, topic_conf, q_type, bloom_res

        q_texts = [sanitize_display_text(q["original_text"]) for q in raw_questions]
        classification_results = await asyncio.gather(*[
            asyncio.to_thread(_classify_question, q_text, subject.name)
            for q_text in q_texts
        ])

        # Fix 4: Pre-load ALL existing topics for this subject into a local dict.
        #        Eliminates the N×(SELECT + optional INSERT + flush) pattern from the loop.
        existing_topics_res = await db.execute(
            select(Topic).where(Topic.subject_id == subject.id)
        )
        topic_cache: dict[str, Topic] = {
            t.name: t for t in existing_topics_res.scalars().all()
        }

        # 9. Build Question entities.
        #    Fix 3: Batch main questions with a single flush; only flush again when
        #           a sub-question needs its parent's DB id.
        q_parent_map: dict = {}
        main_q_entries: List[tuple] = []   # (q_num, entity, topic_name, topic_conf)
        sub_q_entries: List[tuple] = []    # (q_dict, entity, topic_name, topic_conf)

        for q_dict, q_text, classify_res in zip(raw_questions, q_texts, classification_results):
            unit_val, topic_name, topic_conf, q_type, bloom_res = classify_res
            q_num = q_dict["question_number"]
            is_sub = bool(q_dict.get("parent_number"))

            entity = Question(
                question_paper_id=paper.id,
                parent_question_id=None,  # resolved for sub-questions after first flush
                question_number=q_num,
                original_text=q_text,
                normalized_text=q_dict["normalized_text"],
                marks=q_dict["marks"],
                marks_confidence=q_dict["marks_confidence"],
                co_mapping=q_dict.get("co_mapping"),
                choice_group=q_dict.get("choice_group"),
                ai_bloom_level_id=bloom_res.bloom_level_id,
                effective_bloom_level_id=bloom_res.bloom_level_id,
                bloom_confidence=bloom_res.confidence,
                bloom_explanation=bloom_res.explanation,
                ai_question_type=q_type,
                question_type=q_type,
                unit=unit_val,
                extraction_confidence=q_dict["extraction_confidence"],
                review_status="AUTO_CLASSIFIED",
                ai_analysis_metadata={
                    "classifier_source": bloom_res.classifier_source,
                    "gemini_verification_status": bloom_res.gemini_verification_status,
                    "detected_verbs": bloom_res.detected_verbs,
                    "cognitive_operation": bloom_res.cognitive_operation,
                    "component_scores": bloom_res.component_scores,
                    "candidate_scores": bloom_res.candidate_scores,
                },
            )

            if not is_sub:
                db.add(entity)
                main_q_entries.append((q_num, entity, topic_name, topic_conf))
            else:
                sub_q_entries.append((q_dict, entity, topic_name, topic_conf))

        # Single flush for all main questions → gives them DB ids
        await db.flush()
        for q_num, entity, _t, _c in main_q_entries:
            q_parent_map[q_num] = entity

        # Resolve parent ids and add sub-questions
        for q_dict, entity, topic_name, topic_conf in sub_q_entries:
            parent_num = q_dict.get("parent_number")
            if parent_num and parent_num in q_parent_map:
                entity.parent_question_id = q_parent_map[parent_num].id
            db.add(entity)
            q_parent_map[q_dict["question_number"]] = entity

        if sub_q_entries:
            await db.flush()

        created_questions: List[Question] = (
            [e for _, e, _, _ in main_q_entries]
            + [e for _, e, _, _ in sub_q_entries]
        )
        all_topic_info = (
            [(e, t, c) for _, e, t, c in main_q_entries]
            + [(e, t, c) for _, e, t, c in sub_q_entries]
        )

        # Fix 4: Topic linking — use cache, create new topics in bulk, single flush if needed
        new_topic_links: List[QuestionTopic] = []
        needs_flush = False
        for entity, topic_name, topic_conf in all_topic_info:
            if not topic_name:
                continue
            if topic_name not in topic_cache:
                new_topic = Topic(subject_id=subject.id, name=topic_name)
                db.add(new_topic)
                topic_cache[topic_name] = new_topic
                needs_flush = True

        if needs_flush:
            await db.flush()  # One flush for all newly created topics

        for entity, topic_name, topic_conf in all_topic_info:
            if not topic_name:
                continue
            topic_obj = topic_cache[topic_name]
            new_topic_links.append(
                QuestionTopic(question_id=entity.id, topic_id=topic_obj.id, confidence=topic_conf)
            )

        if new_topic_links:
            db.add_all(new_topic_links)

        # 10. Similarity Engine.
        #     Fix 2: Embed the entire historical corpus in ONE batched call before the loop.
        #     Reuse pre-built vectors for every new question — eliminates O(N²) embeddings.
        corpus_stmt = select(Question).where(Question.question_paper_id != paper.id)
        corpus_res = await db.execute(corpus_stmt)
        corpus_questions_raw = [
            {
                "id": q.id,
                "question_number": q.question_number,
                "original_text": q.original_text,
                "normalized_text": q.normalized_text,
            }
            for q in corpus_res.scalars().all()
        ]

        if corpus_questions_raw:
            corpus_texts = [q["original_text"] for q in corpus_questions_raw]
            corpus_vecs = await asyncio.to_thread(
                EmbeddingService.get_embeddings_batch, corpus_texts
            )
            # Drop any questions whose embedding failed
            corpus_data = [
                (q, vec)
                for q, vec in zip(corpus_questions_raw, corpus_vecs)
                if vec is not None
            ]

            # Embed all new questions in a single batched call too
            new_q_texts = [q.original_text for q in created_questions]
            new_q_vecs = await asyncio.to_thread(
                EmbeddingService.get_embeddings_batch, new_q_texts
            )

            similarity_records: List[QuestionSimilarity] = []
            for new_q, new_q_vec in zip(created_questions, new_q_vecs):
                if new_q_vec is None:
                    continue
                similarities = await asyncio.to_thread(
                    SimilarityService.find_similar_questions_prebuilt,
                    new_q.original_text,
                    new_q_vec,
                    corpus_data,
                )
                for sim in similarities:
                    similarity_records.append(
                        QuestionSimilarity(
                            source_question_id=new_q.id,
                            target_question_id=sim["question_id"],
                            similarity_score=sim["similarity_score"],
                            similarity_type=sim["similarity_type"],
                            classification=sim["classification"],
                        )
                    )
            if similarity_records:
                db.add_all(similarity_records)

        paper.processing_status = "COMPLETED"
        await db.commit()
        await db.refresh(paper)
        metrics.record_upload(time.perf_counter() - upload_started_at, time.perf_counter() - analysis_started_at)

        return PaperResponse(
            id=paper.id,
            subject_id=subject.id,
            subject_code=subject.code,
            subject_name=subject.name,
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
            total_questions=len(created_questions),
        )

    except Exception as e:
        logger.error(f"Failed processing question paper upload: {e}")
        await db.rollback()
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as rm_err:
                logger.warning(f"Failed to delete orphaned upload file {file_path}: {rm_err}")
        raise_api_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "PaperProcessingFailed",
            "An error occurred while processing the question paper.",
        )


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
        message=f"Paper is currently {paper.processing_status}.",
    )


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

    # Remove stored physical file if exists
    if paper.stored_file_path and os.path.exists(paper.stored_file_path):
        try:
            os.remove(paper.stored_file_path)
        except Exception as e:
            logger.warning(f"Could not remove stored file {paper.stored_file_path}: {e}")

    await db.delete(paper)
    await db.commit()
    return None
