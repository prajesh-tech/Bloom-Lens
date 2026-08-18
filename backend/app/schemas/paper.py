from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class PaperCreateSchema(BaseModel):
    subject_code: str = Field(..., description="Subject code e.g. CS301")
    subject_name: str = Field(..., description="Subject name e.g. Database Systems")
    examination_type: str = Field(..., description="Examination type e.g. Mid-Term, End-Semester")
    maximum_marks: float = Field(..., gt=0, description="Maximum paper marks > 0")
    year_date: Optional[str] = Field(None, description="Year or Date e.g. 2024 or May 2024")


class SubjectSchema(BaseModel):
    id: int
    code: str
    name: str
    department: Optional[str] = None

    model_config = {"from_attributes": True}


class PaperResponse(BaseModel):
    id: int
    subject_id: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    examination_type: str
    maximum_marks: float
    original_filename: str
    upload_timestamp: datetime
    year_date: Optional[str] = None
    processing_status: str
    extraction_status: str
    validation_status: str
    optional_question_flag: bool
    validation_metadata: Optional[Dict[str, Any]] = None
    total_questions: Optional[int] = 0

    model_config = {"from_attributes": True}


class PaperStatusResponse(BaseModel):
    paper_id: int
    processing_status: str
    extraction_status: str
    validation_status: str
    optional_question_flag: bool
    validation_metadata: Optional[Dict[str, Any]] = None
    message: str


class PaperListResponse(BaseModel):
    items: List[PaperResponse]
    total: int
    page: int
    limit: int
