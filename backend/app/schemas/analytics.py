from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class OverviewAnalyticsResponse(BaseModel):
    papers_analyzed: int = Field(..., description="Total question papers analyzed")
    questions_analyzed: int = Field(..., description="Total questions analyzed")
    subjects_count: int = Field(..., description="Total distinct subjects")
    topics_count: int = Field(..., description="Total distinct topics identified")
    total_relevant_marks: float = Field(..., description="Sum of relevant marks analyzed")


class BloomDistributionItem(BaseModel):
    bloom_level: str  # L1 - L6
    name: str  # Remember, Understand...
    question_count: int
    question_count_percentage: float
    total_marks: float
    marks_percentage: float


class BloomAnalyticsResponse(BaseModel):
    distributions: List[BloomDistributionItem]
    total_questions: int
    total_marks: float


class TopicFrequencyItem(BaseModel):
    topic: str
    frequency: int
    total_marks: float
    bloom_breakdown: Dict[str, int] = Field(default_factory=dict)


class TopicAnalyticsResponse(BaseModel):
    topics: List[TopicFrequencyItem]


class HistoricalTrendItem(BaseModel):
    paper_id: Optional[int] = None
    paper: str
    year: Optional[str] = None
    examination_type: Optional[str] = None
    subject_code: Optional[str] = None
    L1: float = 0.0
    L2: float = 0.0
    L3: float = 0.0
    L4: float = 0.0
    L5: float = 0.0
    L6: float = 0.0


class TrendsAnalyticsResponse(BaseModel):
    metric_type: str  # "count" or "marks_weighted"
    trends: List[HistoricalTrendItem]


class QuestionAnalyticsResponse(BaseModel):
    repeated_questions_count: int
    similar_questions_count: int
    highest_mark_questions: List[Dict[str, Any]]
    question_type_distribution: Dict[str, int]
