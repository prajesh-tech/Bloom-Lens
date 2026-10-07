import pytest
from types import SimpleNamespace
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.subject import Subject
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.services.performance_estimation_service import (
    compute_performance_estimate_core,
    extract_leaf_questions,
    PerformanceEstimationService,
)


def test_pure_all_l1_paper():
    """All-L1 paper has minimum difficulty D=0.10, yielding highest pass % and average marks."""
    questions = [
        {"id": 1, "marks": 10.0, "effective_bloom_level": "L1"},
        {"id": 2, "marks": 10.0, "effective_bloom_level": "L1"},
    ]
    res = compute_performance_estimate_core(paper_max_marks=20.0, questions=questions)
    assert res.reason is None
    # D = 0.10, pass_pct = 95 - 65*0.10 = 88.5, avg_pct = 80 - 50*0.10 = 75.0, avg_marks = 0.75 * 20 = 15.0
    assert res.estimated_pass_percentage == 88.5
    assert res.estimated_average_marks == 15.0


def test_pure_all_l6_paper():
    """All-L6 paper has maximum difficulty D=1.00, yielding lowest pass % and average marks."""
    questions = [
        {"id": 1, "marks": 50.0, "effective_bloom_level": "L6"},
        {"id": 2, "marks": 50.0, "effective_bloom_level": "L6"},
    ]
    res = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
    assert res.reason is None
    # D = 1.00, pass_pct = 95 - 65*1.0 = 30.0, avg_pct = 80 - 50*1.0 = 30.0, avg_marks = 0.30 * 100 = 30.0
    assert res.estimated_pass_percentage == 30.0
    assert res.estimated_average_marks == 30.0


def test_pure_balanced_l1_to_l6_paper():
    """Balanced paper with equal marks across L1-L6."""
    questions = [
        {"id": i, "marks": 10.0, "effective_bloom_level": f"L{i}"} for i in range(1, 7)
    ]
    res = compute_performance_estimate_core(paper_max_marks=60.0, questions=questions)
    assert res.reason is None
    # D = (0.10 + 0.25 + 0.45 + 0.65 + 0.85 + 1.00) / 6 = 3.30 / 6 = 0.55
    # pass_pct = 95 - 65*0.55 = 59.25 -> 59.2 (round half to even)
    # avg_pct = 80 - 50*0.55 = 52.5 -> 52.5% of 60 = 31.5
    assert res.estimated_pass_percentage == 59.2
    assert res.estimated_average_marks == 31.5


def test_marks_weighting_impact():
    """Different marks on the same Bloom levels produce different difficulty D."""
    # Case A: Heavy L5 (10 marks) and light L1 (2 marks)
    questions_a = [
        {"id": 1, "marks": 10.0, "effective_bloom_level": "L5"},
        {"id": 2, "marks": 2.0, "effective_bloom_level": "L1"},
    ]
    res_a = compute_performance_estimate_core(paper_max_marks=12.0, questions=questions_a)

    # Case B: Light L5 (2 marks) and heavy L1 (10 marks)
    questions_b = [
        {"id": 1, "marks": 2.0, "effective_bloom_level": "L5"},
        {"id": 2, "marks": 10.0, "effective_bloom_level": "L1"},
    ]
    res_b = compute_performance_estimate_core(paper_max_marks=12.0, questions=questions_b)

    assert res_a.estimated_pass_percentage is not None
    assert res_b.estimated_pass_percentage is not None
    # Case A is more difficult than Case B
    assert res_a.estimated_pass_percentage < res_b.estimated_pass_percentage
    assert res_a.estimated_average_marks < res_b.estimated_average_marks


def test_same_levels_different_marks_yields_different_d():
    """Testing that varying marks on the exact same levels changes the estimates."""
    q1 = [{"id": 1, "marks": 1.0, "effective_bloom_level": "L2"}, {"id": 2, "marks": 9.0, "effective_bloom_level": "L4"}]
    q2 = [{"id": 1, "marks": 9.0, "effective_bloom_level": "L2"}, {"id": 2, "marks": 1.0, "effective_bloom_level": "L4"}]

    res1 = compute_performance_estimate_core(paper_max_marks=10.0, questions=q1)
    res2 = compute_performance_estimate_core(paper_max_marks=10.0, questions=q2)

    assert res1.estimated_pass_percentage != res2.estimated_pass_percentage
    assert res1.estimated_average_marks != res2.estimated_average_marks


def test_effective_level_honors_human_override():
    """Human Bloom override takes precedence over AI level."""
    # Question with AI level L1, but human override L6
    q = SimpleNamespace(
        id=1,
        marks=10.0,
        parent_question_id=None,
        sub_questions=[],
        ai_bloom_level_id=1,
        human_bloom_level_id=6,
        effective_bloom_level_id=6,
        effective_bloom_level="L6",
    )
    res = compute_performance_estimate_core(paper_max_marks=10.0, questions=[q])
    # Expect D=1.00 (L6) instead of D=0.10 (L1)
    assert res.estimated_pass_percentage == 30.0
    assert res.estimated_average_marks == 3.0


def test_no_double_counting_of_parent_and_sub_question_marks():
    """
    Parent questions with sub-questions are container units;
    only leaf sub-questions are counted.
    """
    parent = SimpleNamespace(
        id=1,
        marks=20.0,
        parent_question_id=None,
        effective_bloom_level="L1",
        sub_questions=[SimpleNamespace(id=2), SimpleNamespace(id=3)],
    )
    child1 = SimpleNamespace(
        id=2,
        marks=10.0,
        parent_question_id=1,
        effective_bloom_level="L6",
        sub_questions=[],
    )
    child2 = SimpleNamespace(
        id=3,
        marks=10.0,
        parent_question_id=1,
        effective_bloom_level="L6",
        sub_questions=[],
    )
    leafs = extract_leaf_questions([parent, child1, child2])
    assert len(leafs) == 2
    assert parent not in leafs

    res = compute_performance_estimate_core(paper_max_marks=20.0, questions=[parent, child1, child2])
    # Both leaf questions are L6 -> D = 1.00
    assert res.estimated_pass_percentage == 30.0
    assert res.estimated_average_marks == 6.0  # 30% of 20 = 6.0


def test_missing_or_invalid_bloom_level_handling():
    """Question with missing/invalid Bloom level is excluded."""
    # 10 questions: 9 with valid Bloom (10 marks each), 1 with missing Bloom (10 marks). Total 100 max marks.
    questions = [
        {"id": i, "marks": 10.0, "effective_bloom_level": "L2"} for i in range(1, 10)
    ]
    questions.append({"id": 10, "marks": 10.0, "effective_bloom_level": None})

    # 10 marks excluded out of 100 = 10% <= 20% default threshold -> available
    res = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
    assert res.reason is None
    assert res.estimated_pass_percentage is not None


def test_missing_or_invalid_marks_handling():
    """Questions with None, zero, negative, or NaN marks are excluded from valid scoring."""
    questions = [
        {"id": 1, "marks": 45.0, "effective_bloom_level": "L2"},
        {"id": 2, "marks": 45.0, "effective_bloom_level": "L2"},
        {"id": 3, "marks": None, "effective_bloom_level": "L2"},
        {"id": 4, "marks": -5.0, "effective_bloom_level": "L2"},
        {"id": 5, "marks": 0.0, "effective_bloom_level": "L2"},
        {"id": 6, "marks": float("nan"), "effective_bloom_level": "L2"},
    ]
    # Valid marks = 90. 10 marks gap from max_marks 100 = 10% <= 20% -> available
    res = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
    assert res.reason is None
    assert res.estimated_pass_percentage is not None


def test_zero_negative_none_max_marks_unavailable():
    """Zero, negative, or None paper maximum marks returns invalid_max_marks."""
    questions = [{"id": 1, "marks": 10.0, "effective_bloom_level": "L1"}]

    res_none = compute_performance_estimate_core(paper_max_marks=None, questions=questions)
    assert res_none.reason == "invalid_max_marks"
    assert res_none.estimated_pass_percentage is None

    res_zero = compute_performance_estimate_core(paper_max_marks=0.0, questions=questions)
    assert res_zero.reason == "invalid_max_marks"

    res_neg = compute_performance_estimate_core(paper_max_marks=-50.0, questions=questions)
    assert res_neg.reason == "invalid_max_marks"


def test_exclusion_threshold_exceeded_returns_unavailable():
    """When excluded marks exceed configurable threshold (default 20%), returns too_many_excluded."""
    # 100 mark paper: 70 marks valid, 30 marks with missing Bloom level (30% > 20%)
    questions = [
        {"id": 1, "marks": 70.0, "effective_bloom_level": "L1"},
        {"id": 2, "marks": 30.0, "effective_bloom_level": None},
    ]
    res = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
    assert res.reason == "too_many_excluded"
    assert res.estimated_pass_percentage is None
    assert res.estimated_average_marks is None


def test_no_valid_questions_returns_unavailable():
    """When all questions are excluded, returns no_valid_questions."""
    questions = [
        {"id": 1, "marks": 10.0, "effective_bloom_level": "INVALID"},
        {"id": 2, "marks": None, "effective_bloom_level": "L2"},
    ]
    res = compute_performance_estimate_core(paper_max_marks=50.0, questions=questions)
    assert res.reason == "no_valid_questions"
    assert res.estimated_pass_percentage is None


def test_paper_not_completed_returns_unavailable():
    """If paper processing is not completed, returns paper_not_completed."""
    questions = [{"id": 1, "marks": 10.0, "effective_bloom_level": "L1"}]
    res = compute_performance_estimate_core(paper_max_marks=10.0, questions=questions, is_completed=False)
    assert res.reason == "paper_not_completed"
    assert res.estimated_pass_percentage is None


def test_determinism_identical_repeat_calls():
    """Estimator is strictly deterministic: repeated calls produce identical results."""
    questions = [
        {"id": 1, "marks": 25.0, "effective_bloom_level": "L2"},
        {"id": 2, "marks": 25.0, "effective_bloom_level": "L4"},
        {"id": 3, "marks": 50.0, "effective_bloom_level": "L5"},
    ]
    res1 = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
    res2 = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
    assert res1.model_dump() == res2.model_dump()


def test_bounds_pass_pct_and_average_marks():
    """Estimated pass % must stay within [0, 100] and average marks <= max marks."""
    for level in ["L1", "L2", "L3", "L4", "L5", "L6"]:
        questions = [{"id": 1, "marks": 100.0, "effective_bloom_level": level}]
        res = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
        assert 0.0 <= res.estimated_pass_percentage <= 100.0
        assert 0.0 <= res.estimated_average_marks <= 100.0


def test_monotonicity():
    """Higher difficulty D never yields higher pass % or average marks."""
    previous_pass = 100.0
    previous_avg = 100.0
    for level in ["L1", "L2", "L3", "L4", "L5", "L6"]:
        questions = [{"id": 1, "marks": 100.0, "effective_bloom_level": level}]
        res = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
        assert res.estimated_pass_percentage <= previous_pass
        assert res.estimated_average_marks <= previous_avg
        previous_pass = res.estimated_pass_percentage
        previous_avg = res.estimated_average_marks


def test_settings_override_changes_output():
    """Custom settings configuration modifies output without requiring code changes."""
    questions = [{"id": 1, "marks": 100.0, "effective_bloom_level": "L1"}]
    custom_cfg = Settings(
        ESTIMATE_PASS_PCT_INTERCEPT=90.0,
        ESTIMATE_PASS_PCT_SLOPE=50.0,
    )
    res_default = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions)
    res_custom = compute_performance_estimate_core(paper_max_marks=100.0, questions=questions, config=custom_cfg)

    # D = 0.10. Default pass = 95 - 65*0.1 = 88.5. Custom pass = 90 - 50*0.1 = 85.0
    assert res_default.estimated_pass_percentage == 88.5
    assert res_custom.estimated_pass_percentage == 85.0


# ---------------------------------------------------------------------------
# API Route Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_performance_estimate_api_success(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/papers/{id}/performance-estimate returns 200 with estimates."""
    subject = Subject(code="PE101", name="Performance Engineering")
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type="End-Semester",
        maximum_marks=50.0,
        original_filename="perf_paper.pdf",
        stored_file_path="/tmp/perf_paper.pdf",
        processing_status="COMPLETED",
    )
    db_session.add(paper)
    await db_session.flush()

    q1 = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="Define queueing theory.",
        normalized_text="define queueing theory",
        marks=25.0,
        effective_bloom_level_id=1,  # L1
        review_status="AUTO_CLASSIFIED",
    )
    q2 = Question(
        question_paper_id=paper.id,
        question_number="Q2",
        original_text="Design an asynchronous worker pool.",
        normalized_text="design an asynchronous worker pool",
        marks=25.0,
        effective_bloom_level_id=6,  # L6
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add_all([q1, q2])
    await db_session.commit()

    resp = await client.get(f"/api/v1/papers/{paper.id}/performance-estimate")
    assert resp.status_code == 200
    data = resp.json()
    assert "estimated_pass_percentage" in data
    assert "estimated_average_marks" in data
    assert data["estimated_pass_percentage"] is not None
    assert data["estimated_average_marks"] is not None
    assert data["reason"] is None


@pytest.mark.asyncio
async def test_get_performance_estimate_api_unavailable(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/papers/{id}/performance-estimate returns 200 with unavailable reason when status not complete."""
    subject = Subject(code="PE102", name="Operating Systems")
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type="Mid-Term",
        maximum_marks=50.0,
        original_filename="os_proc.pdf",
        stored_file_path="/tmp/os_proc.pdf",
        processing_status="PROCESSING",  # Not completed
    )
    db_session.add(paper)
    await db_session.commit()

    resp = await client.get(f"/api/v1/papers/{paper.id}/performance-estimate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["estimated_pass_percentage"] is None
    assert data["estimated_average_marks"] is None
    assert data["reason"] == "paper_not_completed"


@pytest.mark.asyncio
async def test_get_performance_estimate_api_404(client: AsyncClient):
    """GET /api/v1/papers/{id}/performance-estimate returns 404 for non-existent paper."""
    resp = await client.get("/api/v1/papers/999999/performance-estimate")
    assert resp.status_code == 404
