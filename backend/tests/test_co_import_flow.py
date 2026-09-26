import io
import pytest
from httpx import AsyncClient
from app.services.co_extraction_service import COExtractionService


def test_co_extraction_service_logic():
    syllabus_sample = """
    CS301 - Data Structures and Algorithms
    
    Course Outcomes:
    CO1: Define abstract data types and algorithmic complexity. (Bloom Level: L1)
    CO2 - Explain operations on linked lists, stacks, and queues. [L2]
    CO3: Apply sorting and searching algorithms on large datasets.
    CO4: Analyze worst-case and average-case time complexities of graph traversals.
    CO5: Evaluate the efficiency of balanced search trees.
    CO6: Design and develop efficient memory-optimized cache algorithms.
    
    Unit 1: Introduction
    ...
    """

    outcomes = COExtractionService.extract_cos_from_text(syllabus_sample)
    assert len(outcomes) == 6

    # Verify CO1
    assert outcomes[0]["code"] == "CO1"
    assert "Define abstract data types" in outcomes[0]["description"]
    assert "(Bloom Level: L1)" not in outcomes[0]["description"]
    assert outcomes[0]["suggested_bloom_level"] == "L1"

    # Verify CO2
    assert outcomes[1]["code"] == "CO2"
    assert "Explain operations on linked lists" in outcomes[1]["description"]
    assert "[L2]" not in outcomes[1]["description"]
    assert outcomes[1]["suggested_bloom_level"] == "L2"

    # Verify CO6
    assert outcomes[5]["code"] == "CO6"
    assert "Design and develop efficient" in outcomes[5]["description"]
    assert outcomes[5]["suggested_bloom_level"] == "L6"


def test_co_extraction_section_without_explicit_prefix():
    text_sample = """
    Learning Outcomes:
    1. Understand the fundamental components of database management systems.
    2. Construct SQL queries for relational data manipulation.
    3. Design normalized entity-relationship database schemas.
    
    References:
    - Korth and Silberschatz
    """

    outcomes = COExtractionService.extract_cos_from_text(text_sample)
    assert len(outcomes) == 3
    assert outcomes[0]["code"] == "CO1"
    assert "Understand the fundamental" in outcomes[0]["description"]
    assert outcomes[1]["code"] == "CO2"
    assert "Construct SQL queries" in outcomes[1]["description"]
    assert outcomes[2]["code"] == "CO3"
    assert "Design normalized" in outcomes[2]["description"]


@pytest.mark.asyncio
async def test_co_import_api_flow(client: AsyncClient, unauthed_client: AsyncClient):
    # 1. Create a Course
    course_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "CS401", "course_name": "Artificial Intelligence"},
    )
    assert course_resp.status_code == 201
    course_id = course_resp.json()["id"]

    # 2. Test Preview from Text (No DB write)
    text_payload = {
        "text": (
            "Course Outcomes:\n"
            "CO1: Explain state-space search and heuristic strategies.\n"
            "CO2: Apply minimax algorithm with alpha-beta pruning in game trees.\n"
            "CO3: Design neural network architectures for classification."
        )
    }
    preview_resp = await client.post(
        f"/api/v1/courses/{course_id}/outcomes/extract-preview/text",
        json=text_payload,
    )
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["total_extracted"] == 3
    assert len(preview_data["extracted_outcomes"]) == 3
    assert preview_data["extracted_outcomes"][0]["code"] == "CO1"

    # Verify DB has NOT been written yet
    get_course_resp = await client.get(f"/api/v1/courses/{course_id}")
    assert len(get_course_resp.json()["outcomes"]) == 0

    # 3. Test Preview from File Upload (No DB write)
    dummy_file_content = (
        "Course Learning Outcomes:\n"
        "CO1: Describe knowledge representation formalisms.\n"
        "CO2: Implement probabilistic reasoning using Bayesian networks."
    ).encode("utf-8")

    files = {"file": ("syllabus.txt", io.BytesIO(dummy_file_content), "text/plain")}
    file_preview_resp = await client.post(
        f"/api/v1/courses/{course_id}/outcomes/extract-preview/file",
        files=files,
    )
    assert file_preview_resp.status_code == 200
    file_preview_data = file_preview_resp.json()
    assert file_preview_data["total_extracted"] == 2
    assert file_preview_data["source_type"] == "file"

    # 4. Test Unauthenticated Confirm Import is Rejected
    unauth_confirm = await unauthed_client.post(
        f"/api/v1/courses/{course_id}/outcomes/confirm-import",
        json={
            "mode": "replace",
            "outcomes": [
                {"code": "CO1", "description": "Explain state space search", "sort_order": 1},
            ],
        },
    )
    assert unauth_confirm.status_code == 401

    # 5. Confirm and Save (Mode: Replace)
    confirm_resp = await client.post(
        f"/api/v1/courses/{course_id}/outcomes/confirm-import",
        json={
            "mode": "replace",
            "outcomes": [
                {"code": "CO1", "description": "Explain state space search", "sort_order": 1},
                {"code": "CO2", "description": "Apply heuristic algorithms", "sort_order": 2},
            ],
        },
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["total_saved"] == 2
    assert confirm_resp.json()["mode"] == "replace"

    # Verify Outcomes are in DB
    saved_cos = (await client.get(f"/api/v1/courses/{course_id}/outcomes")).json()
    assert saved_cos["total"] == 2
    assert [item["code"] for item in saved_cos["items"]] == ["CO1", "CO2"]

    # 6. Confirm and Save (Mode: Append / Merge)
    append_resp = await client.post(
        f"/api/v1/courses/{course_id}/outcomes/confirm-import",
        json={
            "mode": "append",
            "outcomes": [
                {"code": "CO2", "description": "Apply heuristic algorithms (Updated)", "sort_order": 2},
                {"code": "CO3", "description": "Design neural networks", "sort_order": 3},
            ],
        },
    )
    assert append_resp.status_code == 200
    assert append_resp.json()["total_saved"] == 2

    # Verify Merged state in DB (CO1 unchanged, CO2 updated, CO3 added)
    final_cos = (await client.get(f"/api/v1/courses/{course_id}/outcomes")).json()
    assert final_cos["total"] == 3
    assert [item["code"] for item in final_cos["items"]] == ["CO1", "CO2", "CO3"]
    co2_item = next(item for item in final_cos["items"] if item["code"] == "CO2")
    assert "(Updated)" in co2_item["description"]
