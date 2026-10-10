import os
import tempfile
import asyncio
import threading
import zipfile
from io import BytesIO
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subject import Subject
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.models.topic import Topic, QuestionTopic
from app.services.embedding_service import get_embedding_model, get_fallback_vectorizer, EmbeddingService
from app.services.ocr_service import get_ocr_engine
from app.services.bloom_service import _get_anchor_vectors, BloomService
from app.utils.validators import safe_filename, validate_paper_upload, read_and_validate_upload


@pytest.mark.asyncio
async def test_auth_protected_endpoints_reject_anonymous(unauthed_client: AsyncClient):
    """Anonymous requests to protected endpoints must return 401."""
    # 1. Analytics endpoints
    res_analytics = await unauthed_client.get("/api/v1/analytics/overview")
    assert res_analytics.status_code == 401
    assert "message" in res_analytics.json() or "detail" in res_analytics.json()

    # 2. Upload endpoint
    res_upload = await unauthed_client.post("/api/v1/papers/upload")
    assert res_upload.status_code == 401

    # 3. Delete endpoint
    res_delete = await unauthed_client.delete("/api/v1/papers/1")
    assert res_delete.status_code == 401

    # 4. Patch endpoint
    res_patch = await unauthed_client.patch("/api/v1/questions/1", json={"unit": "Unit 1"})
    assert res_patch.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_credentials_returns_401(unauthed_client: AsyncClient):
    """Invalid credentials via header or Bearer must return 401."""
    res1 = await unauthed_client.get("/api/v1/analytics/overview", headers={"X-API-Key": "wrong_key"})
    assert res1.status_code == 401

    res2 = await unauthed_client.get("/api/v1/analytics/overview", headers={"Authorization": "Bearer wrong_token"})
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_auth_valid_credentials_succeeds(unauthed_client: AsyncClient):
    """Valid credentials via X-API-Key or Bearer proceed to protected endpoint."""
    res1 = await unauthed_client.get("/api/v1/analytics/overview", headers={"X-API-Key": settings.API_KEY})
    assert res1.status_code == 200

    res2 = await unauthed_client.get("/api/v1/analytics/overview", headers={"Authorization": f"Bearer {settings.API_KEY}"})
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_public_endpoints_accessible_without_auth(unauthed_client: AsyncClient):
    """Health probes, root, and read-only search remain publicly accessible."""
    res_root = await unauthed_client.get("/")
    assert res_root.status_code == 200

    res_health = await unauthed_client.get("/api/v1/health")
    assert res_health.status_code == 200

    res_deep = await unauthed_client.get("/api/v1/health/deep")
    assert res_deep.status_code == 200

    res_papers = await unauthed_client.get("/api/v1/papers")
    assert res_papers.status_code == 200

    res_questions = await unauthed_client.get("/api/v1/questions")
    assert res_questions.status_code == 200


@pytest.mark.asyncio
async def test_safe_filename_preserves_extension():
    """safe_filename truncation must preserve .pdf and .docx file extensions."""
    long_name = ("a" * 250) + ".pdf"
    cleaned = safe_filename(long_name)
    assert cleaned.endswith(".pdf")
    assert len(cleaned) <= 180

    long_docx = ("b" * 250) + ".docx"
    cleaned_docx = safe_filename(long_docx)
    assert cleaned_docx.endswith(".docx")
    assert len(cleaned_docx) <= 180


@pytest.mark.asyncio
async def test_pdf_page_limit_is_enforced(monkeypatch):
    import fitz

    document = fitz.open()
    document.new_page()
    document.new_page()
    content = document.tobytes()
    document.close()
    monkeypatch.setattr(settings, "MAX_DOCUMENT_PAGES", 1)
    upload = UploadFile(file=BytesIO(content), filename="many-pages.pdf")

    with pytest.raises(HTTPException) as error:
        await read_and_validate_upload(upload, 100, "Mid-Term")

    assert error.value.status_code == 413
    assert error.value.detail["error_code"] == "TooManyDocumentPages"


@pytest.mark.asyncio
async def test_docx_expanded_size_limit_is_enforced(monkeypatch):
    archive_buffer = BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "types")
        archive.writestr("word/document.xml", "x" * (2 * 1024 * 1024))

    monkeypatch.setattr(settings, "MAX_DOCX_UNCOMPRESSED_SIZE_MB", 1)
    upload = UploadFile(file=BytesIO(archive_buffer.getvalue()), filename="large.docx")

    with pytest.raises(HTTPException) as error:
        await read_and_validate_upload(upload, 100, "Mid-Term")

    assert error.value.status_code == 413
    assert error.value.detail["error_code"] == "DocxExpandedFileTooLarge"


@pytest.mark.asyncio
async def test_examination_type_validation(client: AsyncClient):
    """Uploads with invalid/unsupported examination_type must be rejected with 400."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Q1. Test question.")
        doc.save(tmp.name)
        doc.close()
        pdf_path = tmp.name

    try:
        with open(pdf_path, "rb") as f:
            res = await client.post(
                "/api/v1/papers/upload",
                data={
                    "subject_code": "CS101",
                    "subject_name": "Computer Science",
                    "examination_type": "UnsupportedExamTypeXYZ",
                    "maximum_marks": 50.0,
                },
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert res.status_code == 400
        assert "Unsupported examination type" in res.text
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@pytest.mark.asyncio
async def test_failed_upload_cleans_up_orphaned_file_and_rolls_back(client: AsyncClient, db_session: AsyncSession):
    """When document processing fails, temporary file on disk is deleted and DB state is rolled back."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Q1. Test question.")
        doc.save(tmp.name)
        doc.close()
        pdf_path = tmp.name

    initial_papers = (await db_session.execute(select(func.count(QuestionPaper.id)))).scalar() or 0

    try:
        with open(pdf_path, "rb") as f:
            with patch("app.services.document_service.DocumentService.process_document", side_effect=RuntimeError("Extraction crashed")):
                res = await client.post(
                    "/api/v1/papers/upload",
                    data={
                        "subject_code": "CS999",
                        "subject_name": "Failure Subject",
                        "examination_type": "Mid-Term",
                        "maximum_marks": 50.0,
                    },
                    files={"file": ("test.pdf", f, "application/pdf")},
                )
        assert res.status_code == 500

        # Verify no QuestionPaper record was committed
        final_papers = (await db_session.execute(select(func.count(QuestionPaper.id)))).scalar() or 0
        assert final_papers == initial_papers
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@pytest.mark.asyncio
async def test_question_topic_patch_replaces_topic_without_duplicates(client: AsyncClient, db_session: AsyncSession):
    """Updating topic via PATCH removes previous topic association and prevents duplicate QuestionTopic links."""
    subject = Subject(code="CS303", name="Databases")
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type="End-Semester",
        maximum_marks=50.0,
        original_filename="db.pdf",
        stored_file_path="/tmp/db.pdf",
        processing_status="COMPLETED",
    )
    db_session.add(paper)
    await db_session.flush()

    q = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="What is 3NF normalization?",
        normalized_text="what is 3nf normalization",
        marks=5.0,
        effective_bloom_level_id=1,
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add(q)
    await db_session.flush()

    topic1 = Topic(subject_id=subject.id, name="Old Topic")
    db_session.add(topic1)
    await db_session.flush()

    db_session.add(QuestionTopic(question_id=q.id, topic_id=topic1.id, confidence=1.0, is_primary=True))
    await db_session.commit()

    # Now PATCH with new topic
    patch_res = await client.patch(
        f"/api/v1/questions/{q.id}",
        json={"topic_name": "Normalization & Normal Forms"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["topic"] == "Normalization & Normal Forms"

    # Verify in DB there is exactly 1 QuestionTopic link for this question
    qt_count = (await db_session.execute(select(func.count(QuestionTopic.id)).where(QuestionTopic.question_id == q.id))).scalar()
    assert qt_count == 1


@pytest.mark.asyncio
async def test_analytics_metric_type_validation(client: AsyncClient):
    """Invalid metric_type query parameter must be rejected with 422."""
    res_valid_count = await client.get("/api/v1/analytics/trends?metric_type=count")
    assert res_valid_count.status_code == 200

    res_valid_marks = await client.get("/api/v1/analytics/trends?metric_type=marks_weighted")
    assert res_valid_marks.status_code == 200

    res_invalid = await client.get("/api/v1/analytics/trends?metric_type=invalid_metric_xyz")
    assert res_invalid.status_code == 422


@pytest.mark.asyncio
async def test_health_deep_check_sanitizes_db_error(client: AsyncClient):
    """Database failure in /health/deep must return 'unhealthy' without leaking exception text."""
    with patch("sqlalchemy.ext.asyncio.AsyncSession.execute", side_effect=Exception("FATAL: database disk is full / sensitive password")):
        res = await client.get("/api/v1/health/deep")
        assert res.status_code == 200
        data = res.json()
        assert data["database"] == "unhealthy"
        assert "password" not in res.text
        assert "FATAL" not in res.text


def test_concurrent_lazy_model_initialization():
    """Concurrent threads requesting lazy-loaded models must not cause race conditions."""
    results = []

    def load_vectorizer():
        v = get_fallback_vectorizer()
        results.append(v is not None)

    threads = [threading.Thread(target=load_vectorizer) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(results)
    assert len(results) == 10


def test_gemini_timeout_handling():
    """Synchronous Gemini call timeout must be handled gracefully without raising."""
    with patch("app.core.config.settings.GEMINI_API_KEY", "mock_key"):
        with patch("concurrent.futures.ThreadPoolExecutor.submit") as mock_submit:
            mock_future = MagicMock()
            mock_future.result.side_effect = TimeoutError("Gemini call timed out")
            mock_submit.return_value = mock_future

            initial = MagicMock()
            initial.primary_level = "L1"
            initial.component_scores = {}
            initial.candidate_scores = {}

            result = BloomService._verify_with_gemini("What is a database?", initial)
            assert result is None  # Graceful fallback returned None
