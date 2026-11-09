import re
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, distinct, and_, union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services.performance_estimation_service import extract_leaf_questions
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
    async def _optional_papers(db: AsyncSession, subject_id: Optional[int] = None) -> List[QuestionPaper]:
        query = select(QuestionPaper).where(QuestionPaper.optional_question_flag.is_(True))
        if subject_id is not None:
            query = query.where(QuestionPaper.subject_id == subject_id)
        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def _leaf_ids(db: AsyncSession, subject_id: Optional[int] = None) -> List[int]:
        query = select(Question)
        if subject_id is not None:
            query = query.join(QuestionPaper).where(QuestionPaper.subject_id == subject_id)
        questions = (await db.execute(query)).scalars().all()
        return [q.id for q in extract_leaf_questions(list(questions))]

    @staticmethod
    async def get_overview(db: AsyncSession, subject_id: Optional[int] = None) -> OverviewAnalyticsResponse:
        """Returns macro overview metrics: papers, questions, subjects, topics, and total marks."""
        leaf_ids = await AnalyticsService._leaf_ids(db, subject_id)
        paper_stmt = select(func.count(QuestionPaper.id))
        question_stmt = select(func.count(Question.id)).where(Question.id.in_(leaf_ids))
        subject_stmt = select(func.count(distinct(Subject.id)))
        topic_stmt = select(func.count(distinct(Topic.id)))
        marks_stmt = select(func.coalesce(func.sum(Question.marks), 0.0)).where(Question.id.in_(leaf_ids))

        if subject_id is not None:
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

        optional_papers = await AnalyticsService._optional_papers(db, subject_id)
        if optional_papers:
            rows = (await db.execute(select(Question.question_paper_id, func.coalesce(func.sum(Question.marks), 0)).where(
                Question.question_paper_id.in_([p.id for p in optional_papers]), Question.id.in_(leaf_ids)
            ).group_by(Question.question_paper_id))).all()
            available_marks = dict(rows)
            for paper in optional_papers:
                metadata = paper.validation_metadata or {}
                if paper.validation_status == "valid" and metadata.get("extracted_marks") is not None:
                    total_relevant_marks += float(metadata["extracted_marks"]) - float(available_marks.get(paper.id, 0))

        return OverviewAnalyticsResponse(
            uncertain_paper_ids=[p.id for p in optional_papers if p.validation_status != "valid"],
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
        leaf_ids = await AnalyticsService._leaf_ids(db, subject_id)
        # Fetch all bloom levels L1 - L6
        bloom_levels_res = await db.execute(select(BloomLevel).order_by(BloomLevel.id))
        bloom_levels = bloom_levels_res.scalars().all()

        query = select(
            Question.effective_bloom_level_id,
            func.count(Question.id).label("q_count"),
            func.coalesce(func.sum(Question.marks), 0.0).label("m_sum"),
        ).where(Question.id.in_(leaf_ids)).group_by(Question.effective_bloom_level_id)

        if subject_id is not None:
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
            uncertain_paper_ids=[p.id for p in await AnalyticsService._optional_papers(db, subject_id)],
            distributions=distributions,
            total_questions=total_questions,
            total_marks=total_marks,
        )

    @staticmethod
    async def get_topic_analytics(db: AsyncSession, subject_id: Optional[int] = None) -> TopicAnalyticsResponse:
        """Computes topic frequency and Bloom level breakdown per topic."""
        leaf_ids = await AnalyticsService._leaf_ids(db, subject_id)
        query = (select(Topic.id, Topic.name, Question.effective_bloom_level_id,
                        func.count(distinct(Question.id)), func.coalesce(func.sum(Question.marks), 0.0))
                 .join(QuestionTopic, QuestionTopic.topic_id == Topic.id)
                 .join(Question, QuestionTopic.question_id == Question.id)
                 .where(Question.id.in_(leaf_ids))
                 .group_by(Topic.id, Topic.name, Question.effective_bloom_level_id))
        if subject_id is not None:
            query = query.where(Topic.subject_id == subject_id)
        levels = {level.id: level.code for level in (await db.execute(select(BloomLevel))).scalars()}
        items_by_id = {}
        for topic_id, name, level, count, marks in (await db.execute(query)).all():
            item = items_by_id.setdefault(topic_id, TopicFrequencyItem(topic_id=topic_id, topic=name, frequency=0, total_marks=0))
            item.frequency += count
            item.total_marks += float(marks)
            code = levels.get(level, 'UNKNOWN')
            item.bloom_breakdown[code] = item.bloom_breakdown.get(code, 0) + count
        items = sorted(items_by_id.values(), key=lambda item: (-item.frequency, item.topic_id))

        return TopicAnalyticsResponse(uncertain_paper_ids=[p.id for p in await AnalyticsService._optional_papers(db, subject_id)], topics=items)

    @staticmethod
    async def get_trends_analytics(
        db: AsyncSession, metric_type: str = "marks_weighted", subject_id: Optional[int] = None
    ) -> TrendsAnalyticsResponse:
        """
        Computes historical Bloom level trends across question papers over time.
        Metric type: "count" or "marks_weighted".
        """
        if metric_type not in ("count", "marks_weighted"):
            raise ValueError(f"Invalid metric_type '{metric_type}'. Must be 'count' or 'marks_weighted'.")

        leaf_ids = await AnalyticsService._leaf_ids(db, subject_id)
        papers_query = select(QuestionPaper)
        if subject_id is not None:
            papers_query = papers_query.where(QuestionPaper.subject_id == subject_id)

        papers_res = await db.execute(papers_query)
        def exam_order(paper):
            value = paper.year_date or ''
            year = re.search(r"\b(?:19|20)\d{2}\b", value)
            month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            month = next((index + 1 for index, name in enumerate(month_names) if name in value.lower()), 0)
            numeric = re.search(r"(?:19|20)\d{2}-(\d{2})(?:-(\d{2}))?", value)
            if numeric:
                month = int(numeric.group(1))
            return (int(year.group()) if year else 9999, month, int(numeric.group(2) or 0) if numeric else 0, paper.id)
        papers = sorted(papers_res.scalars().all(), key=exam_order)

        bloom_levels_res = await db.execute(select(BloomLevel))
        bloom_levels = {bl.id: bl.code for bl in bloom_levels_res.scalars().all()}

        # Single aggregated query across matching papers to avoid N+1 queries
        paper_ids = [p.id for p in papers]
        paper_rows_map: Dict[int, List[Any]] = {p.id: [] for p in papers}

        if paper_ids:
            q_query = (
                select(
                    Question.question_paper_id,
                    Question.effective_bloom_level_id,
                    func.count(Question.id).label("q_count"),
                    func.coalesce(func.sum(Question.marks), 0.0).label("m_sum"),
                )
                .where(Question.question_paper_id.in_(paper_ids), Question.id.in_(leaf_ids))
                .group_by(Question.question_paper_id, Question.effective_bloom_level_id)
            )
            q_rows = (await db.execute(q_query)).all()
            for r in q_rows:
                paper_rows_map[r.question_paper_id].append(r)

        trends: List[HistoricalTrendItem] = []

        for p in papers:
            q_rows = paper_rows_map.get(p.id, [])

            trend_vals = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": 0.0, "L5": 0.0, "L6": 0.0}

            tot_cnt = sum(r.q_count for r in q_rows if r.effective_bloom_level_id)
            tot_m = sum(float(r.m_sum) for r in q_rows if r.effective_bloom_level_id)

            for r in q_rows:
                if not r.effective_bloom_level_id:
                    continue
                code = bloom_levels.get(r.effective_bloom_level_id)
                if code not in trend_vals:
                    continue
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
                    unknown_question_count=sum(r.q_count for r in q_rows if bloom_levels.get(r.effective_bloom_level_id) not in trend_vals),
                    **trend_vals,
                )
            )

        return TrendsAnalyticsResponse(uncertain_paper_ids=[p.id for p in await AnalyticsService._optional_papers(db, subject_id)], metric_type=metric_type, trends=trends)

    @staticmethod
    async def get_question_analytics(db: AsyncSession, subject_id: Optional[int] = None) -> QuestionAnalyticsResponse:
        """Returns analytics on repeated questions, highest-mark questions, and question-type distribution."""
        leaf_ids = await AnalyticsService._leaf_ids(db, subject_id)
        async def unique_participants(classifications):
            filters = (QuestionSimilarity.classification.in_(classifications),
                       QuestionSimilarity.source_question_id.in_(leaf_ids), QuestionSimilarity.target_question_id.in_(leaf_ids))
            participants = union(select(QuestionSimilarity.source_question_id).where(*filters),
                                 select(QuestionSimilarity.target_question_id).where(*filters)).subquery()
            return (await db.execute(select(func.count()).select_from(participants))).scalar() or 0
        repeated_cnt = await unique_participants(['exact_repeat'])
        similar_cnt = await unique_participants(['near_duplicate', 'potentially_repeated'])

        # 2. Highest mark questions
        high_marks_query = (
            select(Question)
            .where(Question.marks.isnot(None), Question.id.in_(leaf_ids))
            .order_by(Question.marks.desc())
            .limit(5)
        )
        if subject_id is not None:
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
        ).where(Question.id.in_(leaf_ids)).group_by(Question.question_type)
        if subject_id is not None:
            qt_query = qt_query.join(QuestionPaper).where(QuestionPaper.subject_id == subject_id)

        qt_rows = (await db.execute(qt_query)).all()
        qt_dist = {r[0] or "Descriptive": r[1] for r in qt_rows}

        return QuestionAnalyticsResponse(
            uncertain_paper_ids=[p.id for p in await AnalyticsService._optional_papers(db, subject_id)],
            repeated_questions_count=repeated_cnt,
            similar_questions_count=similar_cnt,
            highest_mark_questions=highest_mark_questions,
            question_type_distribution=qt_dist,
        )
