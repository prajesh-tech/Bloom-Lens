import os
import tempfile
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subject import Subject
from app.models.question_paper import QuestionPaper
from app.models.question import Question


@pytest.mark.asyncio
async def test_paper_upload_api(client: AsyncClient):
    """Tests POST /api/v1/papers/upload."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        # Create a small valid PDF using PyMuPDF
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Q1. Define database normalization. [5 Marks]")
        doc.save(tmp.name)
        doc.close()
        pdf_path = tmp.name

    try:
        with open(pdf_path, "rb") as f:
            response = await client.post(
                "/api/v1/papers/upload",
                data={
                    "subject_code": "CS301",
                    "subject_name": "Database Systems",
                    "examination_type": "Mid-Term",
                    "maximum_marks": 10.0,
                    "year_date": "2024",
                },
                files={"file": ("test_paper.pdf", f, "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["subject_code"] == "CS301"
        assert data["examination_type"] == "Mid-Term"
        assert data["maximum_marks"] == 10.0
        assert data["processing_status"] == "COMPLETED"
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@pytest.mark.asyncio
async def test_list_papers_and_questions_api(client: AsyncClient, db_session: AsyncSession):
    """Tests GET /api/v1/papers and GET /api/v1/questions search and pagination."""
    # Seed DB data
    subject = Subject(code="CS101", name="Intro to CS")
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type="End-Semester",
        maximum_marks=50.0,
        original_filename="cs101.pdf",
        stored_file_path="/tmp/cs101.pdf",
        processing_status="COMPLETED",
    )
    db_session.add(paper)
    await db_session.flush()

    q1 = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="Define recursion with an example.",
        normalized_text="define recursion with an example",
        marks=5.0,
        effective_bloom_level_id=1,  # L1
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add(q1)
    await db_session.commit()

    # 1. Test List Papers
    res_papers = await client.get("/api/v1/papers?page=1&limit=10")
    assert res_papers.status_code == 200
    p_data = res_papers.json()
    assert p_data["total"] >= 1
    assert p_data["items"][0]["subject_code"] == "CS101"

    # 2. Test Search & Filter Questions
    res_q = await client.get("/api/v1/questions?bloom_level=L1")
    assert res_q.status_code == 200
    q_data = res_q.json()
    assert q_data["total"] >= 1
    assert "recursion" in q_data["items"][0]["original_text"]


@pytest.mark.asyncio
async def test_human_override_question_api(client: AsyncClient, db_session: AsyncSession):
    """Tests PATCH /api/v1/questions/{id} for human-in-the-loop overrides."""
    subject = Subject(code="CS202", name="Algorithms")
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type="Mid-Term",
        maximum_marks=20.0,
        original_filename="algo.pdf",
        stored_file_path="/tmp/algo.pdf",
        processing_status="COMPLETED",
    )
    db_session.add(paper)
    await db_session.flush()

    q = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="Analyze merge sort time complexity.",
        normalized_text="analyze merge sort time complexity",
        marks=10.0,
        ai_bloom_level_id=4,  # L4
        effective_bloom_level_id=4,
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add(q)
    await db_session.commit()

    # Override Bloom level to L5 (Evaluate) and set human topic
    patch_payload = {
        "bloom_level": "L5",
        "topic_name": "Sorting Algorithms",
        "unit": "Unit 2",
    }

    res_patch = await client.patch(f"/api/v1/questions/{q.id}", json=patch_payload)
    assert res_patch.status_code == 200
    patched_data = res_patch.json()

    assert patched_data["ai_bloom_level"] == "L4"  # Original AI prediction preserved!
    assert patched_data["human_bloom_level"] == "L5"
    assert patched_data["effective_bloom_level"] == "L5"
    assert patched_data["unit"] == "Unit 2"
    assert patched_data["topic"] == "Sorting Algorithms"
    assert patched_data["review_status"] == "CORRECTED"
