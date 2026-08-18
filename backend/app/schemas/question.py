from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionPatchSchema(BaseModel):
    """Schema for human overriding/correcting question fields."""
    question_text: Optional[str] = Field(None, description="Human corrected question text")
    marks: Optional[float] = Field(None, ge=0.0, description="Human corrected marks")
    topic_name: Optional[str] = Field(None, description="Human corrected topic name")
    unit: Optional[str] = Field(None, description="Human corrected unit e.g. Unit 1")
    bloom_level: Optional[str] = Field(None, description="Human corrected Bloom level e.g. L1, L2... L6")
    question_type: Optional[str] = Field(None, description="Human corrected question type")
    co_mapping: Optional[Dict[str, List[str]]] = Field(None, description="CO/PO outcome mapping dict")
    choice_group: Optional[str] = Field(None, description="Optional choice group identifier")


class QuestionSimilarityResponse(BaseModel):
    id: int
    source_question_id: int
    target_question_id: int
    target_question_text: Optional[str] = None
    target_question_number: Optional[str] = None
    similarity_score: float
    similarity_type: str
    classification: str

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    id: int
    question_paper_id: int
    parent_question_id: Optional[int] = None
    question_number: str
    original_text: str
    normalized_text: str
    marks: Optional[float] = None
    marks_confidence: Optional[str] = None

    # Bloom level representations
    ai_bloom_level: Optional[str] = None
    human_bloom_level: Optional[str] = None
    effective_bloom_level: Optional[str] = None
    bloom_confidence: Optional[float] = None
    bloom_explanation: Optional[str] = None

    # Question types
    ai_question_type: Optional[str] = None
    human_question_type: Optional[str] = None
    question_type: Optional[str] = None

    # Metadata & Taxonomy
    unit: Optional[str] = None
    topic: Optional[str] = None
    co_mapping: Optional[Dict[str, List[str]]] = None
    choice_group: Optional[str] = None
    extraction_confidence: Optional[float] = 1.0
    review_status: str
    ai_analysis_metadata: Optional[Dict[str, Any]] = None

    # Sub-questions hierarchy
    sub_questions: List["QuestionResponse"] = []

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    items: List[QuestionResponse]
    total: int
    page: int
    limit: int
