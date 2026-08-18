from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class BloomLevelSchema(BaseModel):
    id: int
    code: str
    name: str
    description: str
    keywords: Optional[List[str]] = []

    model_config = {"from_attributes": True}


class GeminiBloomResponse(BaseModel):
    """Structured format expected from Google Gemini LLM fallback verification."""
    bloom_level: str = Field(..., description="Bloom taxonomy code, e.g., L1, L2, L3, L4, L5, L6")
    bloom_name: str = Field(..., description="Bloom taxonomy name, e.g., Remember, Analyze")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    cognitive_operation: str = Field(..., description="Summary of cognitive operation required")
    detected_verbs: List[str] = Field(default_factory=list, description="Action verbs detected in the question")
    reason: str = Field(..., description="Detailed explanation of the classification decision")

    @field_validator("bloom_level")
    @classmethod
    def validate_bloom_level(cls, v: str) -> str:
        clean_v = v.strip().upper()
        if clean_v not in ["L1", "L2", "L3", "L4", "L5", "L6"]:
            raise ValueError(f"Invalid Bloom level code: {v}. Must be one of L1-L6.")
        return clean_v


class ComponentScores(BaseModel):
    verb_score: float = 0.0
    semantic_score: float = 0.0
    cognitive_score: float = 0.0
    structure_score: float = 0.0


class BloomClassificationResult(BaseModel):
    primary_level: str
    bloom_level_id: int
    confidence: float
    explanation: str
    detected_verbs: List[str] = []
    cognitive_operation: str = ""
    component_scores: Dict[str, float] = Field(default_factory=dict)
    candidate_scores: Dict[str, float] = Field(default_factory=dict)
    classifier_source: str = "hybrid"  # "hybrid" or "gemini_verified"
    gemini_verification_status: str = "not_required"  # "not_required", "verified", "failed_or_skipped"
