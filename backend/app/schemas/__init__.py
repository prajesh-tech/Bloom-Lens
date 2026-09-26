"""Pydantic schemas for request validation and API responses."""

from app.schemas.course import (
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CourseOutcomeBase,
    CourseOutcomeCreate,
    CourseOutcomeUpdate,
    CourseOutcomeResponse,
    CourseResponse,
    CourseWithOutcomesResponse,
    CourseListResponse,
    CourseOutcomeListResponse,
    CourseBulkOutcomeItem,
    CourseBulkOutcomeRequest,
)

__all__ = [
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseOutcomeBase",
    "CourseOutcomeCreate",
    "CourseOutcomeUpdate",
    "CourseOutcomeResponse",
    "CourseResponse",
    "CourseWithOutcomesResponse",
    "CourseListResponse",
    "CourseOutcomeListResponse",
    "CourseBulkOutcomeItem",
    "CourseBulkOutcomeRequest",
]
