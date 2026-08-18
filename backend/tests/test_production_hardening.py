from io import BytesIO
import pytest
from httpx import AsyncClient
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bloom_level import BloomLevel
from app.models.question import Question
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.models.topic import QuestionTopic, Topic
from app.utils.validators import read_and_validate_upload


def _upload_file(name: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        filename=name,
        file=BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.asyncio
async def test_invalid_upload_extension_rejected():
    upload = _upload_file("paper.txt", b"hello", "text/plain")
    with pytest.raises(Exception) as exc:
        await read_and_validate_upload(upload, 10, "Mid-Term")
    assert exc.value.status_code == 415
    assert exc.value.detail["error_code"] == "UnsupportedFileExtension"


@pytest.mark.asyncio
async def test_invalid_upload_mime_rejected():
    upload = _upload_file("paper.pdf", b"%PDF-1.4\n", "text/plain")
    with pytest.raises(Exception) as exc:
        await read_and_validate_upload(upload, 10, "Mid-Term")
    assert exc.value.status_code == 415
    assert exc.value.detail["error_code"] == "UnsupportedMimeType"


@pytest.mark.asyncio
async def test_invalid_pdf_signature_rejected():
    upload = _upload_file("paper.pdf", b"not actually a pdf", "application/pdf")
    with pytest.raises(Exception) as exc:
        await read_and_validate_upload(upload, 10, "Mid-Term")
    assert exc.value.status_code == 415
    assert exc.value.detail["error_code"] == "InvalidFileSignature"


@pytest.mark.asyncio
async def test_empty_upload_rejected():
    upload = _upload_file("paper.pdf", b"", "application/pdf")
    with pytest.raises(Exception) as exc:
        await read_and_validate_upload(upload, 10, "Mid-Term")
    assert exc.value.status_code == 400
    assert exc.value.detail["error_code"] == "EmptyUpload"


@pytest.mark.asyncio
async def test_pagination_validation_returns_consistent_error(client: AsyncClient):
    response = await client.get("/api/v1/questions?page=0&limit=101")
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "ValidationError"
    assert data["status_code"] == 422
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_question_hierarchy_serialization_avoids_missing_greenlet(
    client: AsyncClient, db_session: AsyncSession
):
    subject = Subject(code="CS777", name="Async Systems")
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type="End-Semester",
        maximum_marks=20.0,
        original_filename="async.pdf",
        stored_file_path="/tmp/async.pdf",
        processing_status="COMPLETED",
    )
    db_session.add(paper)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, name="SQLAlchemy Async")
    db_session.add(topic)
    await db_session.flush()

    parent = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="Explain async ORM loading.",
        normalized_text="explain async orm loading",
        marks=10.0,
        ai_bloom_level_id=2,
        effective_bloom_level_id=2,
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add(parent)
    await db_session.flush()

    child = Question(
        question_paper_id=paper.id,
        parent_question_id=parent.id,
        question_number="Q1(a)",
        original_text="Compare lazy and eager loading.",
        normalized_text="compare lazy and eager loading",
        marks=5.0,
        ai_bloom_level_id=4,
        effective_bloom_level_id=4,
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add(child)
    await db_session.flush()
    db_session.add(QuestionTopic(question_id=child.id, topic_id=topic.id, confidence=1.0))
    await db_session.commit()

    list_response = await client.get("/api/v1/questions")
    assert list_response.status_code == 200
    item = list_response.json()["items"][0]
    assert item["sub_questions"][0]["ai_bloom_level"] == "L4"
    assert item["sub_questions"][0]["topic"] == "SQLAlchemy Async"

    detail_response = await client.get(f"/api/v1/questions/{parent.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["sub_questions"][0]["effective_bloom_level"] == "L4"
