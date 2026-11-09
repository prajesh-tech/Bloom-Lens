import pytest
from app.core.config import Settings


@pytest.mark.asyncio
@pytest.mark.parametrize('path', ['/papers', '/questions', '/courses', '/course-outcomes/1', '/analytics/overview', '/health/deep'])
async def test_every_private_router_requires_auth(unauthed_client, path):
    assert (await unauthed_client.get('/api/v1' + path)).status_code == 401


@pytest.mark.asyncio
async def test_health_is_public_and_minimal(unauthed_client):
    response = await unauthed_client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'online'}


def test_production_refuses_disabled_auth():
    config = Settings(_env_file=None, APP_ENV='production', AUTH_ENABLED=False, GEMINI_API_KEY='configured')
    with pytest.raises(RuntimeError, match='AUTH_ENABLED'):
        config.validate_runtime_config()


@pytest.mark.asyncio
async def test_request_id_is_sanitized(client):
    response = await client.get('/api/v1/health', headers={'X-Request-ID': 'a' * 1000})
    assert len(response.headers['X-Request-ID']) <= 64


@pytest.mark.asyncio
async def test_login_exists_without_public_registration(unauthed_client):
    response = await unauthed_client.post('/api/v1/auth/login', json={'username': 'missing', 'password': 'incorrect'})
    assert response.status_code == 401
    assert (await unauthed_client.post('/api/v1/auth/register', json={})).status_code == 404


@pytest.mark.asyncio
async def test_course_search_treats_wildcards_literally(client):
    for code in ('100%', '100x'):
        response = await client.post('/api/v1/courses', json={'course_code': code, 'course_name': code})
        assert response.status_code == 201
    response = await client.get('/api/v1/courses', params={'search': '100%'})
    assert response.json()['total'] == 1
    assert response.json()['items'][0]['course_code'] == '100%'


@pytest.mark.asyncio
async def test_override_records_actor_and_exact_values(client, db_session):
    from app.models.subject import Subject
    from app.models.question_paper import QuestionPaper
    from app.models.question import Question
    subject = Subject(code='AUDIT', name='Databases')
    db_session.add(subject)
    await db_session.flush()
    paper = QuestionPaper(subject_id=subject.id, examination_type='Internal', maximum_marks=5, original_filename='audit.docx', stored_file_path='audit.docx')
    db_session.add(paper)
    await db_session.flush()
    question = Question(question_paper_id=paper.id, question_number='Q1', original_text='Define keys.', normalized_text='define keys', marks=5)
    db_session.add(question)
    await db_session.commit()
    response = await client.patch(f'/api/v1/questions/{question.id}', json={'marks': 7})
    assert response.status_code == 200
    history = await client.get(f'/api/v1/questions/{question.id}/revisions')
    assert history.status_code == 200
    revision = history.json()[0]
    assert revision['acting_user'] == 'api_key_user'
    assert revision['old_value']['marks'] == 5
    assert revision['new_value']['marks'] == 7
    assert revision['created_at']


@pytest.mark.asyncio
async def test_browser_session_csrf_logout_and_attribution(unauthed_client, db_session, monkeypatch):
    from app.core.config import settings
    from app.core.browser_sessions import hash_password
    from app.models.reviewer import Reviewer, ReviewerSession
    from sqlalchemy import select
    monkeypatch.setattr(settings, 'SESSION_COOKIE_SECURE', False)
    user = Reviewer(username='reviewer', password_hash=hash_password('long-test-password'), role='instructor')
    db_session.add(user)
    await db_session.commit()
    response = await unauthed_client.post('/api/v1/auth/login', json={'username': 'reviewer', 'password': 'long-test-password'})
    assert response.status_code == 200
    cookie = response.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'SameSite=lax' in cookie
    csrf = response.json()['csrf_token']
    identity = await unauthed_client.get('/api/v1/auth/me')
    assert identity.json()['user_id'] == f'reviewer:{user.id}:reviewer'
    from app.models.subject import Subject
    from app.models.question_paper import QuestionPaper
    from app.models.question import Question
    subject = Subject(code='BROWSER', name='Databases')
    db_session.add(subject)
    await db_session.flush()
    paper = QuestionPaper(subject_id=subject.id, examination_type='Internal', maximum_marks=5, original_filename='review.docx', stored_file_path='review.docx')
    db_session.add(paper)
    await db_session.flush()
    question = Question(question_paper_id=paper.id, question_number='Q1', original_text='Define keys.', normalized_text='define keys', marks=5)
    db_session.add(question)
    await db_session.commit()
    assert (await unauthed_client.patch(f'/api/v1/questions/{question.id}', json={'marks': 6}, headers={'X-CSRF-Token': csrf, 'X-User-ID': 'spoofed-admin'})).status_code == 200
    history = await unauthed_client.get(f'/api/v1/questions/{question.id}/revisions')
    assert history.json()[0]['acting_user'] == f'reviewer:{user.id}:reviewer'
    assert (await unauthed_client.post('/api/v1/auth/logout')).status_code == 403
    assert (await unauthed_client.post('/api/v1/auth/logout', headers={'X-CSRF-Token': csrf, 'Origin': 'https://attacker.invalid'})).status_code == 403
    assert (await unauthed_client.post('/api/v1/auth/logout', headers={'X-CSRF-Token': csrf})).status_code == 204
    assert (await unauthed_client.get('/api/v1/auth/me')).status_code == 401
    assert list((await db_session.execute(select(ReviewerSession))).scalars()) == []


@pytest.mark.asyncio
async def test_login_limited_and_disabled_accounts_rejected(unauthed_client, db_session, monkeypatch):
    from app.core.config import settings
    from app.core.browser_sessions import hash_password
    from app.models.reviewer import Reviewer
    db_session.add(Reviewer(username='disabled', password_hash=hash_password('long-test-password'), enabled=False))
    await db_session.commit()
    monkeypatch.setattr(settings, 'LOGIN_RATE_LIMIT_PER_MINUTE', 1)
    assert (await unauthed_client.post('/api/v1/auth/login', json={'username': 'disabled', 'password': 'long-test-password'})).status_code == 401
    assert (await unauthed_client.post('/api/v1/auth/login', json={'username': 'disabled', 'password': 'wrong'})).status_code == 429


@pytest.mark.asyncio
async def test_expired_session_is_rejected(unauthed_client, db_session):
    from datetime import datetime, timedelta, timezone
    from app.models.reviewer import Reviewer, ReviewerSession
    from app.core.browser_sessions import COOKIE_NAME, token_digest, hash_password
    user = Reviewer(username='expired', password_hash=hash_password('long-test-password'))
    db_session.add(user)
    await db_session.flush()
    db_session.add(ReviewerSession(token_hash=token_digest('expired-token'), reviewer_id=user.id,
                                  csrf_token='expired-csrf', expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
    await db_session.commit()
    unauthed_client.cookies.set(COOKIE_NAME, 'expired-token')
    assert (await unauthed_client.get('/api/v1/auth/me')).status_code == 401
