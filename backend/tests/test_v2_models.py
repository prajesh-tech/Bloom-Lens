import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.course import Course
from app.models.course_outcome import CourseOutcome
from app.models.question_course_outcome import QuestionCourseOutcome
from app.models.question import Question
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject


@pytest.mark.asyncio
async def test_course_crud_and_uniqueness(db_session):
    # 1. Create Course
    course = Course(
        course_code="CS301",
        course_name="Data Structures and Algorithms",
        description="Core computer science course"
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    assert course.id is not None
    assert course.course_code == "CS301"

    # 2. Duplicate course_code should raise IntegrityError
    duplicate_course = Course(
        course_code="CS301",
        course_name="Duplicate Course",
    )
    db_session.add(duplicate_course)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_course_outcome_constraints_and_cascade(db_session):
    # 1. Create Course
    course = Course(
        course_code="CS302",
        course_name="Database Systems",
        description="Relational and NoSQL DBs"
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    # 2. Add Outcomes
    co1 = CourseOutcome(
        course_id=course.id,
        code="CO1",
        description="Understand relational database models",
        sort_order=1
    )
    co2 = CourseOutcome(
        course_id=course.id,
        code="CO2",
        description="Design normalized database schemas",
        sort_order=2
    )
    db_session.add_all([co1, co2])
    await db_session.commit()

    course_id = course.id

    # 3. Duplicate CO code in same course should raise IntegrityError
    duplicate_co = CourseOutcome(
        course_id=course_id,
        code="CO1",
        description="Duplicate outcome code",
        sort_order=3
    )
    db_session.add(duplicate_co)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # 4. Check cascade deletion of outcomes when course is deleted
    stmt = select(CourseOutcome).where(CourseOutcome.course_id == course_id)
    outcomes = (await db_session.execute(stmt)).scalars().all()
    assert len(outcomes) == 2

    # Re-fetch course to delete in new transaction
    course_to_del = (await db_session.execute(select(Course).where(Course.id == course_id))).scalar_one()
    await db_session.delete(course_to_del)
    await db_session.commit()

    outcomes_after = (await db_session.execute(stmt)).scalars().all()
    assert len(outcomes_after) == 0


@pytest.mark.asyncio
async def test_question_course_outcome_mapping(db_session):
    # Setup Subject and Course
    subject = Subject(code="SUB-CS303", name="Operating Systems")
    course = Course(course_code="CS303", course_name="Operating Systems")
    db_session.add_all([subject, course])
    await db_session.commit()
    await db_session.refresh(subject)
    await db_session.refresh(course)

    co1 = CourseOutcome(
        course_id=course.id,
        code="CO1",
        description="Analyze CPU scheduling algorithms",
        sort_order=1
    )
    db_session.add(co1)
    await db_session.commit()
    await db_session.refresh(co1)

    paper = QuestionPaper(
        subject_id=subject.id,
        course_id=course.id,
        examination_type="Mid-Term",
        maximum_marks=50.0,
        original_filename="os_mid.pdf",
        stored_file_path="uploads/os_mid.pdf",
    )
    db_session.add(paper)
    await db_session.commit()
    await db_session.refresh(paper)

    question = Question(
        question_paper_id=paper.id,
        question_number="Q1",
        original_text="Explain Round Robin scheduling algorithm with a neat timing diagram.",
        normalized_text="explain round robin scheduling algorithm with a neat timing diagram",
        marks=10.0,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Add QuestionCourseOutcome
    mapping = QuestionCourseOutcome(
        question_id=question.id,
        course_outcome_id=co1.id,
        semantic_score=0.88,
        concept_score=0.92,
        bloom_consistency_score=0.85,
        final_score=0.886,
        ai_confidence=0.89,
        llm_verified="verified",
        llm_reason="Matches CPU scheduling concepts in CO1",
        human_verified=False,
    )
    db_session.add(mapping)
    await db_session.commit()
    await db_session.refresh(mapping)

    assert mapping.id is not None
    assert mapping.final_score == 0.886
    assert mapping.course_outcome.code == "CO1"
    assert mapping.question.question_number == "Q1"

    # Test duplicate mapping constraint
    dup_mapping = QuestionCourseOutcome(
        question_id=question.id,
        course_outcome_id=co1.id,
        semantic_score=0.5,
        concept_score=0.5,
        bloom_consistency_score=0.5,
        final_score=0.5,
        ai_confidence=0.5,
    )
    db_session.add(dup_mapping)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
