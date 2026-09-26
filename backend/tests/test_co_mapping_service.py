import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.course_outcome import CourseOutcome
from app.models.question import Question
from app.models.question_course_outcome import QuestionCourseOutcome
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.models.bloom_level import BloomLevel
from app.services.co_mapping_service import COMappingService
from app.core.config import settings


def test_co_mapping_concept_and_bloom_consistency():
    # 1. Test Concept Score
    q_text = "Normalize the following relation into Third Normal Form (3NF) and identify functional dependencies."
    co1_desc = "Apply database normalization techniques including 1NF, 2NF, 3NF, and functional dependencies."
    co2_desc = "Design balanced binary search trees and analyze traversal algorithms."

    score1 = COMappingService._calculate_concept_score(q_text, co1_desc)
    score2 = COMappingService._calculate_concept_score(q_text, co2_desc)

    assert score1 > 0.4
    assert score1 > score2

    # 2. Test Bloom Consistency Score
    # Exact match: L3 vs L3 ("apply") -> 1.0
    bloom_exact = COMappingService._calculate_bloom_consistency("L3", co1_desc)
    assert bloom_exact >= 0.8

    # Adjacent: L2 vs L3 -> 0.8
    bloom_adj = COMappingService._calculate_bloom_consistency("L2", co1_desc)
    assert bloom_adj >= 0.75

    # Large gap: L6 vs L1 -> 0.20
    bloom_far = COMappingService._calculate_bloom_consistency("L6", "Define the basic terminology.")
    assert bloom_far <= 0.35


def test_co_mapping_service_map_question():
    mock_outcomes = [
        {"id": 1, "code": "CO1", "description": "Explain normalization and relational database concepts."},
        {"id": 2, "code": "CO2", "description": "Construct SQL queries for complex joins and subqueries."},
        {"id": 3, "code": "CO3", "description": "Implement balanced binary search trees and graph traversal algorithms."},
    ]

    # Test question matching CO1
    q1 = "Explain 2NF and 3NF database normalization with examples."
    res1 = COMappingService.map_question(q1, mock_outcomes, question_bloom_level="L2")

    assert res1.primary_outcome is not None
    assert res1.primary_outcome.code == "CO1"
    assert res1.primary_outcome.rank == 1
    assert res1.primary_outcome.semantic_score > 0.0
    assert len(res1.candidates) == 3
    assert res1.is_mapped is True

    # Test question matching CO3
    q3 = "Implement Dijkstra's shortest path algorithm on the given directed graph."
    res3 = COMappingService.map_question(q3, mock_outcomes, question_bloom_level="L3")

    assert res3.primary_outcome is not None
    assert res3.primary_outcome.code == "CO3"
    assert res3.is_mapped is True

    # Test empty question edge case
    res_empty = COMappingService.map_question("", mock_outcomes)
    assert res_empty.primary_outcome is None
    assert res_empty.is_mapped is False


def test_co_mapping_gemini_fallback():
    mock_outcomes = [
        {"id": 1, "code": "CO1", "description": "Describe advanced network security protocols."},
        {"id": 2, "code": "CO2", "description": "Evaluate cryptographic key exchange mechanisms."},
    ]
    q_text = "Compare Diffie-Hellman key exchange with RSA public key infrastructure."

    # Test when Gemini verifies successfully
    mock_gemini_response = MagicMock()
    mock_gemini_response.text = """
    {
      "selected_co_code": "CO2",
      "confidence": 0.95,
      "is_valid_mapping": true,
      "reason": "The question directly evaluates cryptographic key exchange mechanisms."
    }
    """

    with patch("app.core.config.settings.GEMINI_API_KEY", "test-mock-key"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_gemini_response
            mock_client_cls.return_value = mock_client

            result = COMappingService.map_question(
                q_text, mock_outcomes, question_bloom_level="L4"
            )
            # Should have candidate results
            assert result.primary_outcome is not None


@pytest.mark.asyncio
async def test_co_mapping_api_routes(client: AsyncClient, unauthed_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Course and Outcomes
    course_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "CS302", "course_name": "Database Management Systems"},
    )
    assert course_resp.status_code == 201
    course_id = course_resp.json()["id"]

    await client.post(
        f"/api/v1/courses/{course_id}/outcomes",
        json={"code": "CO1", "description": "Explain normalization concepts and functional dependencies.", "sort_order": 1},
    )
    await client.post(
        f"/api/v1/courses/{course_id}/outcomes",
        json={"code": "CO2", "description": "Construct SQL queries and transactions.", "sort_order": 2},
    )

    # 2. Test Dry-Run Map Question API
    dry_run_resp = await client.post(
        f"/api/v1/courses/{course_id}/map-question",
        json={
            "question_text": "Explain Boyce-Codd Normal Form (BCNF) with suitable relational schema.",
            "bloom_level": "L2",
        },
    )
    assert dry_run_resp.status_code == 200
    dry_run_data = dry_run_resp.json()
    assert dry_run_data["primary_outcome"]["code"] == "CO1"
    assert len(dry_run_data["candidates"]) == 2

    # 3. Create Subject, Paper, and Questions in DB
    subj = Subject(code="CS302", name="Database Systems")
    db_session.add(subj)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subj.id,
        course_id=course_id,
        examination_type="End-Semester",
        maximum_marks=50.0,
        original_filename="sample_db_exam.pdf",
        stored_file_path="/tmp/sample_db_exam.pdf",
        processing_status="COMPLETED",
        extraction_status="SUCCESS",
        validation_status="VALIDATED",
    )
    db_session.add(paper)
    await db_session.flush()

    q1 = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="Explain 1NF, 2NF, and 3NF normalization with example tables.",
        normalized_text="explain 1nf 2nf and 3nf normalization with example tables",
        marks=10.0,
        review_status="AUTO_CLASSIFIED",
    )
    q2 = Question(
        question_paper_id=paper.id,
        question_number="Q2",
        original_text="Write SQL query using INNER JOIN and GROUP BY on student table.",
        normalized_text="write sql query using inner join and group by on student table",
        marks=10.0,
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add_all([q1, q2])
    await db_session.commit()

    # 4. Test Unauthenticated Map Paper is Rejected
    unauth_map = await unauthed_client.post(
        f"/api/v1/courses/{course_id}/map-paper/{paper.id}",
        json={"top_k": 1, "threshold": 0.30},
    )
    assert unauth_map.status_code == 401

    # 5. Batch Map Paper API (Auth)
    map_paper_resp = await client.post(
        f"/api/v1/courses/{course_id}/map-paper/{paper.id}",
        json={"top_k": 1, "threshold": 0.30},
    )
    assert map_paper_resp.status_code == 200
    batch_data = map_paper_resp.json()
    assert batch_data["total_questions"] == 2
    assert batch_data["mapped_questions"] >= 2

    # 6. Retrieve Course Question Mappings
    mappings_resp = await client.get(f"/api/v1/courses/{course_id}/mappings")
    assert mappings_resp.status_code == 200
    mappings = mappings_resp.json()
    assert len(mappings) >= 2
    assert all(m["course_outcome_code"] in ["CO1", "CO2"] for m in mappings)
    assert all(m["final_score"] > 0 for m in mappings)
