from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, distinct, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.models.subject import Subject
from app.models.topic import Topic, QuestionTopic
from app.models.bloom_level import BloomLevel
from app.models.question_similarity import QuestionSimilarity
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    BloomAnalyticsResponse,
    BloomDistributionItem,
    TopicAnalyticsResponse,
    TopicFrequencyItem,
    TrendsAnalyticsResponse,
    HistoricalTrendItem,
    QuestionAnalyticsResponse,
)


class AnalyticsService:
    """Service for computing BloomLens metrics and frontend analytics aggregations."""

    @staticmethod
    async def get_overview(db: AsyncSession, subject_id: Optional[int] = None) -> OverviewAnalyticsResponse:
        """Returns macro overview metrics: papers, questions, subjects, topics, and total marks."""
        paper_stmt = select(func.count(QuestionPaper.id))
        question_stmt = select(func.count(Question.id))
        subject_stmt = select(func.count(distinct(Subject.id)))
        topic_stmt = select(func.count(distinct(Topic.id)))
        marks_stmt = select(func.coalesce(func.sum(Question.marks), 0.0))

        if subject_id:
            paper_stmt = paper_stmt.where(QuestionPaper.subject_id == subject_id)
            question_stmt = question_stmt.join(QuestionPaper).where(QuestionPaper.subject_id == subject_id)
            subject_stmt = subject_stmt.where(Subject.id == subject_id)
            topic_stmt = topic_stmt.where(Topic.subject_id == subject_id)
            marks_stmt = marks_stmt.join(QuestionPaper).where(QuestionPaper.subject_id == subject_id)

        papers_analyzed = (await db.execute(paper_stmt)).scalar() or 0
        questions_analyzed = (await db.execute(question_stmt)).scalar() or 0
        subjects_count = (await db.execute(subject_stmt)).scalar() or 0
        topics_count = (await db.execute(topic_stmt)).scalar() or 0
        total_relevant_marks = float((await db.execute(marks_stmt)).scalar() or 0.0)

        return OverviewAnalyticsResponse(
            papers_analyzed=papers_analyzed,
            questions_analyzed=questions_analyzed,
            subjects_count=subjects_count,
            topics_count=topics_count,
            total_relevant_marks=total_relevant_marks,
        )

    @staticmethod
    async def get_bloom_analytics(db: AsyncSession, subject_id: Optional[int] = None) -> BloomAnalyticsResponse:
        """
        Computes both Question-Count Distribution and Marks-Weighted Bloom Distribution.
        """
        # Fetch all bloom levels L1 - L6
        bloom_levels_res = await db.execute(select(BloomLevel).order_by(BloomLevel.id))
        bloom_levels = bloom_levels_res.scalars().all()

        query = select(
            Question.effective_bloom_level_id,
            func.count(Question.id).label("q_count"),
            func.coalesce(func.sum(Question.marks), 0.0).label("m_sum"),
        ).group_by(Question.effective_bloom_level_id)

        if subject_id:
            query = query.join(QuestionPaper).where(QuestionPaper.subject_id == subject_id)

        results = (await db.execute(query)).all()

        counts_map = {row.effective_bloom_level_id: row.q_count for row in results if row.effective_bloom_level_id}
        marks_map = {row.effective_bloom_level_id: float(row.m_sum) for row in results if row.effective_bloom_level_id}

        total_questions = sum(counts_map.values())
        total_marks = sum(marks_map.values())

        distributions: List[BloomDistributionItem] = []
        for bl in bloom_levels:
            q_cnt = counts_map.get(bl.id, 0)
            m_sum = marks_map.get(bl.id, 0.0)

            q_pct = (q_cnt / total_questions * 100.0) if total_questions > 0 else 0.0
            m_pct = (m_sum / total_marks * 100.0) if total_marks > 0 else 0.0

            distributions.append(
                BloomDistributionItem(
                    bloom_level=bl.code,
                    name=bl.name,
                    question_count=q_cnt,
                    question_count_percentage=round(q_pct, 2),
                    total_marks=m_sum,
                    marks_percentage=round(m_pct, 2),
                )
            )

        return BloomAnalyticsResponse(
            distributions=distributions,
            total_questions=total_questions,
            total_marks=total_marks,
        )

    @staticmethod
    async def get_topic_analytics(db: AsyncSession, subject_id: Optional[int] = None) -> TopicAnalyticsResponse:
        """Computes topic frequency and Bloom level breakdown per topic."""
        query = (
            select(
                Topic.name.label("topic_name"),
                func.count(distinct(Question.id)).label("frequency"),
                func.coalesce(func.sum(Question.marks), 0.0).label("total_marks"),
            )
            .join(QuestionTopic, QuestionTopic.topic_id == Topic.id)
            .join(Question, QuestionTopic.question_id == Question.id)
            .group_by(Topic.name)
            .order_by(func.count(distinct(Question.id)).desc())
        )

        if subject_id:
            query = query.where(Topic.subject_id == subject_id)

        rows = (await db.execute(query)).all()

        items: List[TopicFrequencyItem] = []
        for r in rows:
            items.append(
                TopicFrequencyItem(
                    topic=r.topic_name,
                    frequency=r.frequency,
                    total_marks=float(r.total_marks),
                    bloom_breakdown={},
                )
            )

        return TopicAnalyticsResponse(topics=items)

    @staticmethod
    async def get_trends_analytics(
        db: AsyncSession, metric_type: str = "marks_weighted", subject_id: Optional[int] = None
    ) -> TrendsAnalyticsResponse:
        """
        Computes historical Bloom level trends across question papers over time.
        Metric type: "count" or "marks_weighted".
        """
        papers_query = select(QuestionPaper).order_by(QuestionPaper.upload_timestamp.asc())
        if subject_id:
            papers_query = papers_query.where(QuestionPaper.subject_id == subject_id)

        papers_res = await db.execute(papers_query)
        papers = papers_res.scalars().all()

        bloom_levels_res = await db.execute(select(BloomLevel))
        bloom_levels = {bl.id: bl.code for bl in bloom_levels_res.scalars().all()}

        trends: List[HistoricalTrendItem] = []

        for p in papers:
            q_query = select(
                Question.effective_bloom_level_id,
                func.count(Question.id).label("q_count"),
                func.coalesce(func.sum(Question.marks), 0.0).label("m_sum"),
            ).where(Question.question_paper_id == p.id).group_by(Question.effective_bloom_level_id)

            q_rows = (await db.execute(q_query)).all()

            trend_vals = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": 0.0, "L5": 0.0, "L6": 0.0}

            tot_cnt = sum(r.q_count for r in q_rows if r.effective_bloom_level_id)
            tot_m = sum(float(r.m_sum) for r in q_rows if r.effective_bloom_level_id)

            for r in q_rows:
                if not r.effective_bloom_level_id:
                    continue
                code = bloom_levels.get(r.effective_bloom_level_id, "L1")
                if metric_type == "count":
                    trend_vals[code] = round((r.q_count / tot_cnt * 100.0), 2) if tot_cnt > 0 else 0.0
                else:  # marks_weighted
                    trend_vals[code] = round((float(r.m_sum) / tot_m * 100.0), 2) if tot_m > 0 else 0.0

            paper_label = f"{p.original_filename} ({p.year_date or 'N/A'})"
            trends.append(
                HistoricalTrendItem(
                    paper_id=p.id,
                    paper=paper_label,
                    year=p.year_date,
                    examination_type=p.examination_type,
                    **trend_vals,
                )
            )

        return TrendsAnalyticsResponse(metric_type=metric_type, trends=trends)

    @staticmethod
    async def get_question_analytics(db: AsyncSession, subject_id: Optional[int] = None) -> QuestionAnalyticsResponse:
        """Returns analytics on repeated questions, highest-mark questions, and question-type distribution."""
        # 1. Similarity counts
        rep_query = select(func.count(QuestionSimilarity.id)).where(QuestionSimilarity.classification == "exact_repeat")
        sim_query = select(func.count(QuestionSimilarity.id)).where(QuestionSimilarity.classification == "potentially_repeated")

        repeated_cnt = (await db.execute(rep_query)).scalar() or 0
        similar_cnt = (await db.execute(sim_query)).scalar() or 0

        # 2. Highest mark questions
        high_marks_query = (
            select(Question)
            .where(Question.marks.isnot(None))
            .order_by(Question.marks.desc())
            .limit(5)
        )
        if subject_id:
            high_marks_query = high_marks_query.join(QuestionPaper).where(QuestionPaper.subject_id == subject_id)

        high_qs = (await db.execute(high_marks_query)).scalars().all()
        highest_mark_questions = [
            {
                "id": q.id,
                "question_number": q.question_number,
                "text": q.original_text,
                "marks": q.marks,
                "unit": q.unit,
            }
            for q in high_qs
        ]

        # 3. Question type distribution
        qt_query = select(
            Question.question_type, func.count(Question.id)
        ).group_by(Question.question_type)
        if subject_id:
            qt_query = qt_query.join(QuestionPaper).where(QuestionPaper.subject_id == subject_id)

        qt_rows = (await db.execute(qt_query)).all()
        qt_dist = {r[0] or "Descriptive": r[1] for r in qt_rows}

        return QuestionAnalyticsResponse(
            repeated_questions_count=repeated_cnt,
            similar_questions_count=similar_cnt,
            highest_mark_questions=highest_mark_questions,
            question_type_distribution=qt_dist,
        )
