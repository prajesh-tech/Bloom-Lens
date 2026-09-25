from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, AuthenticatedUser
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    BloomAnalyticsResponse,
    TopicAnalyticsResponse,
    QuestionAnalyticsResponse,
    TrendsAnalyticsResponse,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/overview", response_model=OverviewAnalyticsResponse)
async def get_overview_analytics(
    subject_id: Optional[int] = Query(None, description="Optional subject ID filter"),
    db: AsyncSession = Depends(get_db),
):
    """Returns top-level macro metrics (papers, questions, subjects, topics, total marks)."""
    return await AnalyticsService.get_overview(db, subject_id)


@router.get("/bloom", response_model=BloomAnalyticsResponse)
async def get_bloom_analytics(
    subject_id: Optional[int] = Query(None, description="Optional subject ID filter"),
    db: AsyncSession = Depends(get_db),
):
    """Returns Question-Count and Marks-Weighted Bloom Distributions (L1 - L6)."""
    return await AnalyticsService.get_bloom_analytics(db, subject_id)


@router.get("/topics", response_model=TopicAnalyticsResponse)
async def get_topic_analytics(
    subject_id: Optional[int] = Query(None, description="Optional subject ID filter"),
    db: AsyncSession = Depends(get_db),
):
    """Returns topic frequency distribution and total topic marks."""
    return await AnalyticsService.get_topic_analytics(db, subject_id)


@router.get("/questions", response_model=QuestionAnalyticsResponse)
async def get_question_analytics(
    subject_id: Optional[int] = Query(None, description="Optional subject ID filter"),
    db: AsyncSession = Depends(get_db),
):
    """Returns analytics on repeated questions, highest-mark questions, and question types."""
    return await AnalyticsService.get_question_analytics(db, subject_id)


@router.get("/trends", response_model=TrendsAnalyticsResponse)
async def get_trends_analytics(
    metric_type: Literal["count", "marks_weighted"] = Query("marks_weighted", description="Metric type: 'count' or 'marks_weighted'"),
    subject_id: Optional[int] = Query(None, description="Optional subject ID filter"),
    db: AsyncSession = Depends(get_db),
):
    """Returns historical cognitive Bloom level trends over time."""
    return await AnalyticsService.get_trends_analytics(db, metric_type, subject_id)
