import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.models.bloom_level import BloomLevel
from app.services.analytics_service import AnalyticsService


@pytest.mark.asyncio
async def test_analytics_service(db_session: AsyncSession):
    # Setup test subject, paper, and questions
    subject = Subject(code="CS301", name="Database Systems")
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        examination_type="End-Semester",
        maximum_marks=100.0,
        original_filename="db_2024.pdf",
        stored_file_path="/tmp/db_2024.pdf",
        processing_status="COMPLETED",
    )
    db_session.add(paper)
    await db_session.flush()

    # Add Q1 (L1, 5 marks) and Q2 (L4, 15 marks)
    q1 = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="Define normalization.",
        normalized_text="define normalization",
        marks=5.0,
        effective_bloom_level_id=1,  # L1
        review_status="AUTO_CLASSIFIED",
    )
    q2 = Question(
        question_paper_id=paper.id,
        question_number="Q2",
        original_text="Compare 2NF and 3NF.",
        normalized_text="compare 2nf and 3nf",
        marks=15.0,
        effective_bloom_level_id=4,  # L4
        review_status="AUTO_CLASSIFIED",
    )
    db_session.add_all([q1, q2])
    await db_session.commit()

    # Test Overview
    overview = await AnalyticsService.get_overview(db_session)
    assert overview.papers_analyzed == 1
    assert overview.questions_analyzed == 2
    assert overview.total_relevant_marks == 20.0

    # Test Bloom Distributions
    bloom_analytics = await AnalyticsService.get_bloom_analytics(db_session)
    assert bloom_analytics.total_questions == 2
    assert bloom_analytics.total_marks == 20.0

    l1_item = next(d for d in bloom_analytics.distributions if d.bloom_level == "L1")
    l4_item = next(d for d in bloom_analytics.distributions if d.bloom_level == "L4")

    # Q-count: 50% L1, 50% L4
    assert l1_item.question_count_percentage == 50.0
    assert l4_item.question_count_percentage == 50.0

    # Marks-weighted: L1 = 5/20 = 25%, L4 = 15/20 = 75%
    assert l1_item.marks_percentage == 25.0
    assert l4_item.marks_percentage == 75.0
