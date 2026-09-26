from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, AuthenticatedUser
from app.schemas.course import (
    CourseOutcomeUpdate,
    CourseOutcomeResponse,
)
from app.services.course_service import CourseService

router = APIRouter(prefix="/course-outcomes", tags=["Course Outcomes"])


@router.get("/{co_id}", response_model=CourseOutcomeResponse)
async def get_course_outcome(
    co_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves a single course outcome by ID."""
    outcome = await CourseService.get_course_outcome_by_id(db, co_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CourseOutcome with ID {co_id} not found.",
        )
    return CourseOutcomeResponse.model_validate(outcome)


@router.put("/{co_id}", response_model=CourseOutcomeResponse)
async def update_course_outcome(
    co_id: int,
    data: CourseOutcomeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Updates a single course outcome by ID (Auth required)."""
    outcome = await CourseService.update_course_outcome(db, co_id, data)
    return CourseOutcomeResponse.model_validate(outcome)


@router.delete("/{co_id}", status_code=status.HTTP_200_OK)
async def delete_course_outcome(
    co_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Deletes a single course outcome by ID (Auth required)."""
    await CourseService.delete_course_outcome(db, co_id)
    return {"message": f"CourseOutcome {co_id} deleted successfully."}
