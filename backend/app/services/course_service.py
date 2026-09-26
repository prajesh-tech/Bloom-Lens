from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course
from app.models.course_outcome import CourseOutcome
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseOutcomeCreate,
    CourseOutcomeUpdate,
    CourseBulkOutcomeItem,
)
from app.core.logging import logger


class CourseService:
    """Service layer handling Course and CourseOutcome business logic and database interactions."""

    @staticmethod
    async def get_courses(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """
        Retrieves paginated courses with outcome count in an optimized single query.
        """
        # Subquery for outcome counts per course to prevent N+1
        outcome_count_subq = (
            select(
                CourseOutcome.course_id,
                func.count(CourseOutcome.id).label("outcomes_count"),
            )
            .group_by(CourseOutcome.course_id)
            .subquery()
        )

        query = (
            select(
                Course,
                func.coalesce(outcome_count_subq.c.outcomes_count, 0).label("outcomes_count"),
            )
            .outerjoin(outcome_count_subq, Course.id == outcome_count_subq.c.course_id)
        )

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Course.course_code.ilike(search_term),
                    Course.course_name.ilike(search_term),
                    Course.description.ilike(search_term),
                )
            )

        # Count total
        count_stmt = select(func.count(Course.id))
        if search:
            search_term = f"%{search.strip()}%"
            count_stmt = count_stmt.where(
                or_(
                    Course.course_code.ilike(search_term),
                    Course.course_name.ilike(search_term),
                    Course.description.ilike(search_term),
                )
            )
        total = (await db.execute(count_stmt)).scalar() or 0

        # Paginate
        query = query.order_by(Course.course_code.asc()).offset(skip).limit(limit)
        results = (await db.execute(query)).all()

        items = []
        for course_row, count in results:
            items.append({
                "id": course_row.id,
                "course_code": course_row.course_code,
                "course_name": course_row.course_name,
                "description": course_row.description,
                "created_at": course_row.created_at,
                "updated_at": course_row.updated_at,
                "outcomes_count": count,
            })

        return items, total

    @staticmethod
    async def get_course_by_id(
        db: AsyncSession,
        course_id: int,
        include_outcomes: bool = True,
    ) -> Optional[Course]:
        """Fetches a single course by its ID, optionally with loaded outcomes."""
        stmt = select(Course).where(Course.id == course_id)
        if include_outcomes:
            stmt = stmt.options(selectinload(Course.outcomes))
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_course_by_code(
        db: AsyncSession,
        course_code: str,
    ) -> Optional[Course]:
        """Fetches a course by exact case-insensitive code."""
        stmt = select(Course).where(func.lower(Course.course_code) == course_code.strip().lower())
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create_course(
        db: AsyncSession,
        data: CourseCreate,
    ) -> Course:
        """Creates a new course with unique course_code validation."""
        existing = await CourseService.get_course_by_code(db, data.course_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course with code '{data.course_code}' already exists.",
            )

        course = Course(
            course_code=data.course_code.strip(),
            course_name=data.course_name.strip(),
            description=data.description.strip() if data.description else None,
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        logger.info(f"Created Course id={course.id} code={course.course_code}")
        return course

    @staticmethod
    async def update_course(
        db: AsyncSession,
        course_id: int,
        data: CourseUpdate,
    ) -> Course:
        """Updates an existing course with duplicate code verification."""
        course = await CourseService.get_course_by_id(db, course_id, include_outcomes=True)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

        if data.course_code is not None:
            new_code = data.course_code.strip()
            if new_code.lower() != course.course_code.lower():
                existing = await CourseService.get_course_by_code(db, new_code)
                if existing and existing.id != course_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Course with code '{new_code}' already exists.",
                    )
                course.course_code = new_code

        if data.course_name is not None:
            course.course_name = data.course_name.strip()

        if data.description is not None:
            course.description = data.description.strip() if data.description else None

        await db.commit()
        await db.refresh(course)
        logger.info(f"Updated Course id={course.id} code={course.course_code}")
        return course

    @staticmethod
    async def delete_course(
        db: AsyncSession,
        course_id: int,
    ) -> bool:
        """Deletes a course and cascades deletion to child outcomes."""
        course = await CourseService.get_course_by_id(db, course_id, include_outcomes=False)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

        await db.delete(course)
        await db.commit()
        logger.info(f"Deleted Course id={course_id}")
        return True

    # ---------------- Course Outcome Operations ---------------- #

    @staticmethod
    async def get_course_outcomes(
        db: AsyncSession,
        course_id: int,
    ) -> List[CourseOutcome]:
        """Lists all outcomes for a specific course ordered by sort_order and code."""
        # Verify course exists
        course = await CourseService.get_course_by_id(db, course_id, include_outcomes=False)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

        stmt = (
            select(CourseOutcome)
            .where(CourseOutcome.course_id == course_id)
            .order_by(CourseOutcome.sort_order.asc(), CourseOutcome.code.asc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def get_course_outcome_by_id(
        db: AsyncSession,
        co_id: int,
    ) -> Optional[CourseOutcome]:
        """Fetches a specific course outcome by its ID."""
        stmt = select(CourseOutcome).where(CourseOutcome.id == co_id).options(selectinload(CourseOutcome.course))
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create_course_outcome(
        db: AsyncSession,
        course_id: int,
        data: CourseOutcomeCreate,
    ) -> CourseOutcome:
        """Creates a course outcome under a course with unique code validation."""
        course = await CourseService.get_course_by_id(db, course_id, include_outcomes=False)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

        # Check for duplicate code in same course
        check_stmt = select(CourseOutcome).where(
            CourseOutcome.course_id == course_id,
            func.lower(CourseOutcome.code) == data.code.strip().lower(),
        )
        existing = (await db.execute(check_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"CourseOutcome with code '{data.code}' already exists for Course {course.course_code}.",
            )

        outcome = CourseOutcome(
            course_id=course_id,
            code=data.code.strip().upper(),
            description=data.description.strip(),
            sort_order=data.sort_order,
        )
        db.add(outcome)
        await db.commit()
        await db.refresh(outcome)
        logger.info(f"Created CourseOutcome id={outcome.id} code={outcome.code} for course_id={course_id}")
        return outcome

    @staticmethod
    async def update_course_outcome(
        db: AsyncSession,
        co_id: int,
        data: CourseOutcomeUpdate,
    ) -> CourseOutcome:
        """Updates a course outcome with duplicate code checking."""
        outcome = await CourseService.get_course_outcome_by_id(db, co_id)
        if not outcome:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CourseOutcome with ID {co_id} not found.",
            )

        if data.code is not None:
            new_code = data.code.strip().upper()
            if new_code.lower() != outcome.code.lower():
                check_stmt = select(CourseOutcome).where(
                    CourseOutcome.course_id == outcome.course_id,
                    func.lower(CourseOutcome.code) == new_code.lower(),
                )
                existing = (await db.execute(check_stmt)).scalar_one_or_none()
                if existing and existing.id != co_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"CourseOutcome with code '{new_code}' already exists for this course.",
                    )
                outcome.code = new_code

        if data.description is not None:
            outcome.description = data.description.strip()

        if data.sort_order is not None:
            outcome.sort_order = data.sort_order

        await db.commit()
        await db.refresh(outcome)
        logger.info(f"Updated CourseOutcome id={outcome.id} code={outcome.code}")
        return outcome

    @staticmethod
    async def delete_course_outcome(
        db: AsyncSession,
        co_id: int,
    ) -> bool:
        """Deletes a course outcome."""
        outcome = await CourseService.get_course_outcome_by_id(db, co_id)
        if not outcome:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CourseOutcome with ID {co_id} not found.",
            )

        await db.delete(outcome)
        await db.commit()
        logger.info(f"Deleted CourseOutcome id={co_id}")
        return True

    @staticmethod
    async def bulk_create_or_replace_outcomes(
        db: AsyncSession,
        course_id: int,
        outcomes_data: List[CourseBulkOutcomeItem],
    ) -> List[CourseOutcome]:
        """
        Atomically replaces all outcomes for a course with a new list.
        Validates duplicate codes in the payload.
        """
        course = await CourseService.get_course_by_id(db, course_id, include_outcomes=False)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

        # Check for duplicates in incoming payload
        seen_codes = set()
        for item in outcomes_data:
            code_upper = item.code.strip().upper()
            if code_upper in seen_codes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate CourseOutcome code '{code_upper}' in request payload.",
                )
            seen_codes.add(code_upper)

        # Delete existing outcomes
        await db.execute(delete(CourseOutcome).where(CourseOutcome.course_id == course_id))

        # Add new outcomes
        new_outcomes = []
        for idx, item in enumerate(outcomes_data):
            sort_val = item.sort_order if item.sort_order != 0 else idx + 1
            co = CourseOutcome(
                course_id=course_id,
                code=item.code.strip().upper(),
                description=item.description.strip(),
                sort_order=sort_val,
            )
            db.add(co)
            new_outcomes.append(co)

        await db.commit()
        for co in new_outcomes:
            await db.refresh(co)

        logger.info(f"Replaced {len(new_outcomes)} outcomes for Course id={course_id}")
        return new_outcomes
