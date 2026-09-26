from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CourseBase(BaseModel):
    course_code: str = Field(..., min_length=1, max_length=50, description="Unique course code e.g. CS301")
    course_name: str = Field(..., min_length=1, max_length=255, description="Course title")
    description: Optional[str] = Field(None, description="Course syllabus/description")

    @field_validator("course_code", "course_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or only whitespace")
            return v_stripped
        return v


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    course_code: Optional[str] = Field(None, min_length=1, max_length=50)
    course_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

    @field_validator("course_code", "course_name")
    @classmethod
    def strip_whitespace_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or only whitespace")
            return v_stripped
        return v


class CourseOutcomeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="CO identifier e.g. CO1")
    description: str = Field(..., min_length=1, description="CO description/statement")
    sort_order: int = Field(0, description="Display order sequence")

    @field_validator("code", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or only whitespace")
            return v_stripped
        return v


class CourseOutcomeCreate(CourseOutcomeBase):
    pass


class CourseOutcomeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1)
    sort_order: Optional[int] = None

    @field_validator("code", "description")
    @classmethod
    def strip_whitespace_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or only whitespace")
            return v_stripped
        return v


class CourseOutcomeResponse(BaseModel):
    id: int
    course_id: int
    code: str
    description: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CourseResponse(BaseModel):
    id: int
    course_code: str
    course_name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    outcomes_count: int = 0

    model_config = {"from_attributes": True}


class CourseWithOutcomesResponse(CourseResponse):
    outcomes: List[CourseOutcomeResponse] = []

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    items: List[CourseResponse]
    total: int
    page: int
    limit: int


class CourseOutcomeListResponse(BaseModel):
    items: List[CourseOutcomeResponse]
    total: int


class CourseBulkOutcomeItem(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    sort_order: int = Field(0)

    @field_validator("code", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or only whitespace")
            return v_stripped
        return v


class CourseBulkOutcomeRequest(BaseModel):
    outcomes: List[CourseBulkOutcomeItem]
