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


class COExtractTextRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Raw syllabus or curriculum text containing Course Outcomes")


class COExtractedItem(BaseModel):
    code: str = Field(..., description="Normalized CO code e.g. CO1")
    description: str = Field(..., description="Extracted outcome description")
    sort_order: int = Field(0, description="Inferred sequence order")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    suggested_bloom_level: Optional[str] = Field(None, description="Suggested Bloom level code e.g. L2, L3")


class COExtractionPreviewResponse(BaseModel):
    course_id: int
    course_code: str
    extracted_outcomes: List[COExtractedItem]
    total_extracted: int
    source_type: str  # "text" or "file"
    raw_text_snippet: Optional[str] = None


class COImportConfirmItem(BaseModel):
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


class COImportConfirmRequest(BaseModel):
    outcomes: List[COImportConfirmItem] = Field(..., min_length=1, description="List of confirmed Course Outcomes")
    mode: str = Field("replace", description="Import mode: 'replace' to overwrite existing COs, or 'append' to add new ones")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in {"replace", "append"}:
            raise ValueError("mode must be either 'replace' or 'append'")
        return v_clean


class COImportConfirmResponse(BaseModel):
    course_id: int
    mode: str
    saved_outcomes: List[CourseOutcomeResponse]
    total_saved: int
    message: str

