import os
import asyncio
import time
from typing import List, Protocol
from fastapi import BackgroundTasks, status
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.core.errors import raise_api_error
from app.core.metrics import metrics
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.models.question import Question
from app.models.topic import Topic, QuestionTopic
from app.models.question_similarity import QuestionSimilarity
from app.services.document_service import DocumentService
from app.services.question_extraction_service import QuestionExtractionService
from app.services.topic_service import TopicService
from app.services.bloom_service import BloomService
from app.services.similarity_service import SimilarityService
from app.services.embedding_service import EmbeddingService, get_embedding_backend_metadata, embedding_backend_identity
import numpy as np
from app.utils.text_cleaner import extract_year_from_text, sanitize_display_text

async def remove_stored_file(path: str) -> None:
    try:
        await asyncio.to_thread(os.remove, path)
    except FileNotFoundError:
        pass
    except OSError:
        logger.warning("Stored file cleanup failed")


async def process_paper(paper_id: int) -> None:
    """Each database phase owns its session; no OCR/ML runs in a transaction."""
    analysis_started_at = time.perf_counter()
    file_path = None
    try:
        async with AsyncSessionLocal() as db:
            paper = await db.get(QuestionPaper, paper_id)
            if paper is None or paper.processing_status != "UPLOADED":
                return
            subject = await db.get(Subject, paper.subject_id)
            subject_name = subject.name
            subject_topics = list((await db.execute(select(Topic.name).where(Topic.subject_id == subject.id, Topic.is_managed.is_(True)))).scalars())
            maximum_marks = paper.maximum_marks
            file_path = paper.stored_file_path
            orig_filename = paper.original_filename
            year_date = paper.year_date
            paper.processing_status = "PROCESSING"
            await db.commit()
        # 5. Extract document text using threadpool
        analysis_started_at = time.perf_counter()
        doc_result = await asyncio.to_thread(DocumentService.process_document, file_path)
        full_text = sanitize_display_text(doc_result["full_text"])

        if not year_date:
            year_date = extract_year_from_text(full_text) or extract_year_from_text(orig_filename)

        # 6. Extract questions & marks using threadpool
        raw_questions = await asyncio.to_thread(QuestionExtractionService.extract_questions, full_text)
        if len(raw_questions) > settings.MAX_EXTRACTED_QUESTIONS:
            raise_api_error(
                getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                "TooManyExtractedQuestions",
                f"Document contains more than the maximum allowed {settings.MAX_EXTRACTED_QUESTIONS} questions.",
            )
        if not raw_questions:
            raise ValueError("No questions extracted")
        extraction_status = "SUCCESS"


        # 7. Validate Paper Marks
        val_info = QuestionExtractionService.validate_paper_marks(maximum_marks, raw_questions, full_text)
        if not settings.RETAIN_UPLOADED_FILES:
            await remove_stored_file(file_path)
        async with AsyncSessionLocal() as db:
            paper = await db.get(QuestionPaper, paper_id)
            if paper is None:
                return
            paper.processing_status = "ANALYZING"
            paper.extraction_status = extraction_status
            paper.year_date = year_date
            paper.validation_status = val_info["status"]
            paper.optional_question_flag = val_info["optional_question_flag"]
            paper.validation_metadata = val_info
            await db.commit()
        # 8. Fix 1: Parallelize per-question CPU work (Bloom + Topic + Unit).
        #    All classifiers are pure CPU functions — run them concurrently in worker threads.
        def _classify_question(q_text: str, subj_name: str):
            """Runs all CPU-bound classifiers for one question in a worker thread."""
            unit_val = TopicService.identify_unit(q_text)
            topic_name, topic_conf = TopicService.identify_topic(q_text, subj_name, subject_topics)
            q_type, _ = TopicService.classify_question_type(q_text)
            bloom_res = BloomService.classify_question(q_text)
            return unit_val, topic_name, topic_conf, q_type, bloom_res

        q_texts = [sanitize_display_text(q["original_text"]) for q in raw_questions]
        classification_limit = asyncio.Semaphore(settings.MAX_PARALLEL_QUESTION_CLASSIFICATIONS)

        async def classify_question(q_text: str):
            async with classification_limit:
                return await asyncio.to_thread(_classify_question, q_text, subject_name)

        classification_results = await asyncio.gather(
            *(classify_question(q_text) for q_text in q_texts)
        )

        async with AsyncSessionLocal() as db:
            paper = await db.get(QuestionPaper, paper_id)
            if paper is None:
                return
            subject = await db.get(Subject, paper.subject_id)
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

            await db.commit()
        # Snapshot the same-subject corpus, then close the session before embedding.
        async with AsyncSessionLocal() as db:
            corpus = list((await db.execute(select(Question).join(QuestionPaper).where(
                Question.question_paper_id != paper_id, QuestionPaper.subject_id == paper.subject_id,
                QuestionPaper.processing_status == "COMPLETED"))).scalars())
        new_vectors = await asyncio.to_thread(EmbeddingService.get_embeddings_batch, [q.original_text for q in created_questions])
        metadata = get_embedding_backend_metadata()
        backend = embedding_backend_identity(metadata)
        missing = [q for q in corpus if q.embedding_vector is None]
        historical_vectors = await asyncio.to_thread(EmbeddingService.get_embeddings_batch, [q.original_text for q in missing]) if missing else []
        if embedding_backend_identity(get_embedding_backend_metadata()) != backend:
            # A model failure changed vector space while backfilling: regenerate this batch consistently.
            new_vectors = await asyncio.to_thread(EmbeddingService.get_embeddings_batch, [q.original_text for q in created_questions])
            historical_vectors = await asyncio.to_thread(EmbeddingService.get_embeddings_batch, [q.original_text for q in missing]) if missing else []
            metadata = get_embedding_backend_metadata()
            backend = embedding_backend_identity(metadata)
        backfill = {q.id: vector for q, vector in zip(missing, historical_vectors) if vector is not None}
        corpus_data = []
        for question in corpus:
            if question.id in backfill:
                vector = backfill[question.id]
            elif question.embedding_backend == backend:
                vector = np.asarray(question.embedding_vector, dtype=np.float32)
            else:
                vector = None  # Exact text remains comparable; semantic vectors do not.
            corpus_data.append(({"id": question.id, "question_number": question.question_number,
                "original_text": question.original_text, "normalized_text": question.normalized_text,
                "embedding_backend": backend if question.id in backfill else question.embedding_backend}, vector))
        index = await asyncio.to_thread(SimilarityService.build_index, corpus_data, backend)
        similarity_records = []
        for question, vector in zip(created_questions, new_vectors):
            if vector is None:
                continue
            matches = await asyncio.to_thread(index.search, question.original_text, vector)
            similarity_records.extend(QuestionSimilarity(source_question_id=question.id,
                target_question_id=match["question_id"], similarity_score=match["similarity_score"],
                similarity_type=match["similarity_type"], classification=match["classification"])
                for match in matches)
        async with AsyncSessionLocal() as db:
            for question, vector in zip(created_questions, new_vectors):
                entity = await db.get(Question, question.id)
                if entity is not None and vector is not None:
                    entity.embedding_vector = vector.tolist()
                    entity.embedding_backend = backend
                    entity.embedding_metadata = metadata
                    entity.ai_analysis_metadata = {**(entity.ai_analysis_metadata or {}),
                        "embedding_backend": metadata, "confidence_kind": "uncalibrated_score"}
            for question_id, vector in backfill.items():
                entity = await db.get(Question, question_id)
                if entity is not None:
                    entity.embedding_vector, entity.embedding_backend, entity.embedding_metadata = vector.tolist(), backend, metadata
            await db.commit()

        async with AsyncSessionLocal() as db:
            paper = await db.get(QuestionPaper, paper_id)
            if paper is None:
                return
            if similarity_records:
                db.add_all(similarity_records)
            paper.processing_status = "COMPLETED"
            paper.error_message = None
            await db.commit()
        metrics.record_upload(time.perf_counter() - analysis_started_at, time.perf_counter() - analysis_started_at)
    except Exception:
        logger.error("Paper processing failed", extra={"paper_id": paper_id})
        async with AsyncSessionLocal() as db:
            paper = await db.get(QuestionPaper, paper_id)
            if paper is not None:
                await db.execute(delete(Question).where(Question.question_paper_id == paper_id))
                paper.processing_status = "FAILED"
                if paper.extraction_status == "PENDING":
                    paper.extraction_status = "FAILED"
                paper.error_message = "Document processing failed. Please review the file or contact an administrator."
                await db.commit()
        if file_path:
            await remove_stored_file(file_path)


class PaperDispatcher(Protocol):
    def enqueue(self, tasks: BackgroundTasks, paper_id: int) -> None: ...


class BackgroundPaperDispatcher:
    def enqueue(self, tasks: BackgroundTasks, paper_id: int) -> None:
        tasks.add_task(process_paper, paper_id)


dispatcher: PaperDispatcher = BackgroundPaperDispatcher()


async def fail_interrupted_jobs() -> None:
    from sqlalchemy import update
    async with AsyncSessionLocal() as db:
        await db.execute(update(QuestionPaper).where(QuestionPaper.processing_status.in_(
            ["UPLOADED", "PROCESSING", "ANALYZING"])).values(
                processing_status="FAILED", error_message="Processing interrupted by server restart; upload again after deleting this paper."))
        await db.commit()
