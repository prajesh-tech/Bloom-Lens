import pytest
from app.models.subject import Subject
from app.models.question_paper import QuestionPaper


@pytest.mark.asyncio
async def test_history_subject_filter_applies_to_items_and_total(client, db_session):
    ids = []
    for code in ('A', 'B'):
        subject = Subject(code=code, name=code)
        db_session.add(subject)
        await db_session.flush()
        ids.append(subject.id)
        db_session.add(QuestionPaper(subject_id=subject.id, examination_type='Internal', maximum_marks=5,
            original_filename=f'{code}.docx', stored_file_path=f'{code}.docx'))
    await db_session.commit()
    response = await client.get('/api/v1/papers', params={'subject_id': ids[0]})
    assert response.json()['total'] == 1
    assert [paper['subject_id'] for paper in response.json()['items']] == [ids[0]]
