from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class COScoreBreakdown(BaseModel):
    semantic_score: float = Field(0.0, description="Normalized semantic embedding cosine similarity")
    concept_score: float = Field(0.0, description="Normalized technical keyword/concept overlap score")
    bloom_consistency_score: float = Field(0.0, description="Cognitive level alignment between Question and CO")
    final_score: float = Field(0.0, description="Weighted composite score")


class COMappingCandidate(BaseModel):
    course_outcome_id: int = Field(..., description="ID of the Course Outcome")
    code: str = Field(..., description="CO code e.g. CO1")
    description: str = Field(..., description="CO description statement")
    semantic_score: float = Field(0.0, ge=0.0, le=1.0)
    concept_score: float = Field(0.0, ge=0.0, le=1.0)
    bloom_consistency_score: float = Field(0.0, ge=0.0, le=1.0)
    final_score: float = Field(0.0, ge=0.0, le=1.0)
    rank: int = Field(1, description="Rank among candidate COs (1 = top candidate)")


class QuestionCOMappingResult(BaseModel):
    question_id: Optional[int] = None
    question_text: str
    question_bloom_level: Optional[str] = None
    primary_outcome: Optional[COMappingCandidate] = None
    candidates: List[COMappingCandidate] = []
    ai_confidence: float = Field(0.0, ge=0.0, le=1.0)
    llm_verified: str = Field("skipped", description="Verification status: verified, rejected, skipped, unavailable")
    llm_reason: Optional[str] = None
    is_mapped: bool = Field(False, description="Whether mapping meets confidence/match threshold")


class QuestionCOMappingRequest(BaseModel):
    question_text: str = Field(..., min_length=3, description="Question text to map to course outcomes")
    bloom_level: Optional[str] = Field(None, description="Optional question Bloom level (e.g. L1-L6)")


class BatchCOPaperMappingRequest(BaseModel):
    top_k: int = Field(1, ge=1, le=5, description="Number of top COs to link per question")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override minimum confidence threshold")


class BatchCOMappingResponse(BaseModel):
    course_id: int
    paper_id: Optional[int] = None
    total_questions: int
    mapped_questions: int
    results: List[QuestionCOMappingResult]


class QuestionCOMappingRecordResponse(BaseModel):
    id: int
    question_id: int
    course_outcome_id: int
    course_outcome_code: Optional[str] = None
    course_outcome_description: Optional[str] = None
    semantic_score: float
    concept_score: float
    bloom_consistency_score: float
    final_score: float
    ai_confidence: float
    llm_verified: str
    llm_reason: Optional[str] = None
    human_verified: bool
    human_override: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeminiCOMappingResponse(BaseModel):
    selected_co_code: str = Field(..., description="CO code that best matches the question")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the mapping")
    is_valid_mapping: bool = Field(True, description="Whether the question is relevant to the course outcomes")
    reason: str = Field(..., description="Academic justification for the mapping")
