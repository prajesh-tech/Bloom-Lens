from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.subject import Subject
from app.models.topic import Topic
from app.schemas.paper import SubjectSchema
from app.schemas.topic import TopicInput, TopicResponse

router = APIRouter(prefix='/subjects', tags=['Subjects and topics'], dependencies=[Depends(get_current_user)])


@router.get('', response_model=list[SubjectSchema], dependencies=[Depends(get_current_user)])
async def subjects(limit: int = Query(100, ge=1, le=1000), db: AsyncSession = Depends(get_db)):
    return [SubjectSchema.model_validate(subject) for subject in (await db.execute(select(Subject).order_by(Subject.code).limit(limit))).scalars()]


@router.get('/{subject_id}/topics', response_model=list[TopicResponse], dependencies=[Depends(get_current_user)])
async def subject_topics(subject_id: int, db: AsyncSession = Depends(get_db)):
    return [TopicResponse.model_validate(topic) for topic in (await db.execute(select(Topic).where(Topic.subject_id == subject_id).order_by(Topic.name))).scalars()]


@router.post('/{subject_id}/topics', response_model=TopicResponse, status_code=201, dependencies=[Depends(get_current_user)])
async def create_topic(subject_id: int, payload: TopicInput, db: AsyncSession = Depends(get_db)):
    if await db.get(Subject, subject_id) is None:
        raise HTTPException(404, 'Subject not found.')
    existing = (await db.execute(select(Topic).where(Topic.subject_id == subject_id, Topic.name == payload.name))).scalars().first()
    if existing:
        existing.is_managed = True
        topic = existing
    else:
        topic = Topic(subject_id=subject_id, name=payload.name, is_managed=True)
        db.add(topic)
    await db.commit()
    return TopicResponse.model_validate(topic)


@router.patch('/{subject_id}/topics/{topic_id}', response_model=TopicResponse, dependencies=[Depends(get_current_user)])
async def update_topic(subject_id: int, topic_id: int, payload: TopicInput, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if topic is None or topic.subject_id != subject_id:
        raise HTTPException(404, 'Topic not found.')
    topic.name, topic.is_managed = payload.name, True
    await db.commit()
    return TopicResponse.model_validate(topic)


@router.delete('/{subject_id}/topics/{topic_id}', status_code=204, dependencies=[Depends(get_current_user)])
async def delete_topic(subject_id: int, topic_id: int, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if topic is None or topic.subject_id != subject_id:
        raise HTTPException(404, 'Topic not found.')
    await db.delete(topic)
    await db.commit()
