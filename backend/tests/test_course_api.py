import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_course_crud_api_flow(client: AsyncClient, unauthed_client: AsyncClient):
    # 1. Test unauthenticated course creation is rejected
    unauth_resp = await unauthed_client.post(
        "/api/v1/courses",
        json={"course_code": "CS101", "course_name": "Intro to CS"},
    )
    assert unauth_resp.status_code == 401

    # 2. Test course creation
    create_resp = await client.post(
        "/api/v1/courses",
        json={
            "course_code": "CS101",
            "course_name": "Introduction to Computer Science",
            "description": "Foundational programming and algorithmic thinking",
        },
    )
    assert create_resp.status_code == 201
    course_data = create_resp.json()
    course_id = course_data["id"]
    assert course_data["course_code"] == "CS101"
    assert course_data["course_name"] == "Introduction to Computer Science"
    assert course_data["outcomes_count"] == 0

    # 3. Test duplicate course_code returns 409 Conflict
    dup_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "cs101", "course_name": "Duplicate Code Test"},
    )
    assert dup_resp.status_code == 409

    # 4. Test validation error for empty whitespace
    val_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "   ", "course_name": "Invalid Course"},
    )
    assert val_resp.status_code == 422

    # 5. Test get course by ID
    get_resp = await client.get(f"/api/v1/courses/{course_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["course_code"] == "CS101"
    assert get_resp.json()["outcomes"] == []

    # 6. Test update course
    update_resp = await client.put(
        f"/api/v1/courses/{course_id}",
        json={"course_name": "Intro to CS (Updated)", "description": "Updated syllabus"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["course_name"] == "Intro to CS (Updated)"

    # 7. Test search and pagination
    list_resp = await client.get("/api/v1/courses?search=Intro&page=1&limit=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert len(list_resp.json()["items"]) == 1
    assert list_resp.json()["items"][0]["course_code"] == "CS101"


@pytest.mark.asyncio
async def test_course_outcomes_api_flow(client: AsyncClient):
    # 1. Create a Course
    course_resp = await client.post(
        "/api/v1/courses",
        json={
            "course_code": "CS201",
            "course_name": "Data Structures",
            "description": "Linear and hierarchical data structures",
        },
    )
    assert course_resp.status_code == 201
    course_id = course_resp.json()["id"]

    # 2. Add Course Outcomes
    co1_resp = await client.post(
        f"/api/v1/courses/{course_id}/outcomes",
        json={
            "code": "CO1",
            "description": "Understand arrays, linked lists, and stacks",
            "sort_order": 1,
        },
    )
    assert co1_resp.status_code == 201
    co1_id = co1_resp.json()["id"]
    assert co1_resp.json()["code"] == "CO1"

    co2_resp = await client.post(
        f"/api/v1/courses/{course_id}/outcomes",
        json={
            "code": "CO2",
            "description": "Implement tree and graph traversal algorithms",
            "sort_order": 2,
        },
    )
    assert co2_resp.status_code == 201
    co2_id = co2_resp.json()["id"]

    # 3. Duplicate CO in same course returns 409
    dup_co_resp = await client.post(
        f"/api/v1/courses/{course_id}/outcomes",
        json={"code": "co1", "description": "Duplicate outcome"},
    )
    assert dup_co_resp.status_code == 409

    # 4. List outcomes for course
    list_co_resp = await client.get(f"/api/v1/courses/{course_id}/outcomes")
    assert list_co_resp.status_code == 200
    assert list_co_resp.json()["total"] == 2
    assert [item["code"] for item in list_co_resp.json()["items"]] == ["CO1", "CO2"]

    # 5. Get course detail includes outcomes
    course_detail_resp = await client.get(f"/api/v1/courses/{course_id}")
    assert course_detail_resp.status_code == 200
    assert course_detail_resp.json()["outcomes_count"] == 2
    assert len(course_detail_resp.json()["outcomes"]) == 2

    # 6. Update single outcome
    update_co_resp = await client.put(
        f"/api/v1/course-outcomes/{co1_id}",
        json={"description": "Understand arrays, linked lists, stacks, and queues (Updated)"},
    )
    assert update_co_resp.status_code == 200
    assert "queues" in update_co_resp.json()["description"]

    # 7. Get single outcome by ID
    get_co_resp = await client.get(f"/api/v1/course-outcomes/{co1_id}")
    assert get_co_resp.status_code == 200
    assert get_co_resp.json()["id"] == co1_id

    # 8. Delete single outcome
    del_co_resp = await client.delete(f"/api/v1/course-outcomes/{co2_id}")
    assert del_co_resp.status_code == 200

    # Verify deleted outcome returns 404
    get_del_resp = await client.get(f"/api/v1/course-outcomes/{co2_id}")
    assert get_del_resp.status_code == 404


@pytest.mark.asyncio
async def test_bulk_outcomes_and_cascade_delete(client: AsyncClient):
    # 1. Create Course
    course_resp = await client.post(
        "/api/v1/courses",
        json={"course_code": "CS305", "course_name": "Software Engineering"},
    )
    assert course_resp.status_code == 201
    course_id = course_resp.json()["id"]

    # 2. Bulk replace outcomes
    bulk_resp = await client.put(
        f"/api/v1/courses/{course_id}/outcomes/bulk",
        json={
            "outcomes": [
                {"code": "CO1", "description": "Software development lifecycles", "sort_order": 1},
                {"code": "CO2", "description": "Agile methodologies and Scrum", "sort_order": 2},
                {"code": "CO3", "description": "Software testing and CI/CD pipelines", "sort_order": 3},
            ]
        },
    )
    assert bulk_resp.status_code == 200
    assert bulk_resp.json()["total"] == 3

    # 3. Bulk replace with duplicate codes in request payload returns 400
    bad_bulk_resp = await client.put(
        f"/api/v1/courses/{course_id}/outcomes/bulk",
        json={
            "outcomes": [
                {"code": "CO1", "description": "First"},
                {"code": "CO1", "description": "Duplicate code"},
            ]
        },
    )
    assert bad_bulk_resp.status_code == 400

    # 4. Delete Course cascades and cleans up outcomes
    del_course_resp = await client.delete(f"/api/v1/courses/{course_id}")
    assert del_course_resp.status_code == 200

    # Confirm course is 404
    get_course_resp = await client.get(f"/api/v1/courses/{course_id}")
    assert get_course_resp.status_code == 404
