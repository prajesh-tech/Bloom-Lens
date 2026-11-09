from io import BytesIO
import docx
import pytest


def paper_bytes():
    stream = BytesIO()
    document = docx.Document()
    document.add_paragraph('Q1. Define normalization. [5 Marks]')
    document.save(stream)
    return stream.getvalue()


async def upload(client, content, code='PIPE'):
    return await client.post('/api/v1/papers/upload', data={
        'subject_code': code, 'subject_name': 'Databases',
        'examination_type': 'Internal', 'maximum_marks': 5,
    }, files={'file': ('paper.docx', content, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')})


@pytest.mark.asyncio
async def test_upload_returns_accepted_with_committed_id(client):
    response = await upload(client, paper_bytes())
    assert response.status_code == 202
    body = response.json()
    assert body['processing_status'] == 'UPLOADED'
    assert body['status_url'] == f"/api/v1/papers/{body['id']}/status"
    assert (await client.get(body['status_url'])).json()['processing_status'] == 'COMPLETED'


@pytest.mark.asyncio
async def test_same_subject_duplicate_is_rejected(client):
    content = paper_bytes()
    first = await upload(client, content)
    assert first.status_code == 202
    second = await upload(client, content)
    assert second.status_code == 409
    assert second.json()['error_code'] == 'DuplicatePaper'
    assert (await upload(client, content, code='OTHER')).status_code == 202


@pytest.mark.asyncio
async def test_streaming_upload_uses_bounded_reads(tmp_path, monkeypatch):
    from app.utils import validators
    from app.core.config import settings
    from fastapi import UploadFile
    import hashlib
    content = paper_bytes()

    class BoundedFile(BytesIO):
        def read(self, size=-1):
            assert 0 < size <= 64 * 1024
            return super().read(size)

    monkeypatch.setattr(settings, 'UPLOAD_DIR', str(tmp_path))
    name, path, digest = await validators.store_and_validate_upload(UploadFile(file=BoundedFile(content), filename='paper.docx'), 5, 'Internal')
    assert name == 'paper.docx'
    assert digest == hashlib.sha256(content).hexdigest()
    from pathlib import Path
    assert Path(path).read_bytes() == content


@pytest.mark.asyncio
async def test_delete_preserves_file_when_commit_fails(client, db_session, tmp_path, monkeypatch):
    from app.models.subject import Subject
    from app.models.question_paper import QuestionPaper
    from unittest.mock import AsyncMock
    subject = Subject(code='DELETE', name='Databases')
    db_session.add(subject)
    await db_session.flush()
    path = tmp_path / 'paper.docx'
    path.write_bytes(paper_bytes())
    paper = QuestionPaper(subject_id=subject.id, examination_type='Internal', maximum_marks=5,
                          original_filename=path.name, stored_file_path=str(path))
    db_session.add(paper)
    await db_session.commit()
    monkeypatch.setattr(db_session, 'commit', AsyncMock(side_effect=RuntimeError('commit failed')))
    with pytest.raises(RuntimeError, match='commit failed'):
        await client.delete(f'/api/v1/papers/{paper.id}')
    assert path.exists()


@pytest.mark.asyncio
async def test_upload_rate_limit_and_body_limit(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'UPLOAD_RATE_LIMIT_PER_MINUTE', 1)
    assert (await upload(client, paper_bytes())).status_code == 202
    assert (await upload(client, paper_bytes())).status_code == 429
    response = await client.post('/api/v1/papers/upload', content=b'x', headers={'Content-Length': str(22 * 1024 * 1024)})
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_successful_extraction_removes_file_by_default(client, db_session):
    from app.models.question_paper import QuestionPaper
    from pathlib import Path
    response = await upload(client, paper_bytes())
    assert response.status_code == 202
    paper = await db_session.get(QuestionPaper, response.json()['id'])
    assert not Path(paper.stored_file_path).exists()


@pytest.mark.asyncio
async def test_configured_retention_keeps_extracted_file(client, db_session, monkeypatch):
    from app.core.config import settings
    from app.models.question_paper import QuestionPaper
    from pathlib import Path
    monkeypatch.setattr(settings, 'RETAIN_UPLOADED_FILES', True)
    response = await upload(client, paper_bytes())
    paper = await db_session.get(QuestionPaper, response.json()['id'])
    assert Path(paper.stored_file_path).exists()
    Path(paper.stored_file_path).unlink()


@pytest.mark.asyncio
async def test_worker_closes_sessions_for_extraction_and_classification(client, monkeypatch):
    from contextlib import asynccontextmanager
    from app.services import paper_processing_service as worker
    factory = worker.AsyncSessionLocal
    active = []
    statuses = []

    @asynccontextmanager
    async def tracked_session():
        async with factory() as session:
            active.append(session)
            original_commit = session.commit

            async def commit():
                for entity in list(session.identity_map.values()) + list(session.new):
                    if isinstance(entity, worker.QuestionPaper) and entity in session.dirty:
                        statuses.append(entity.processing_status)
                await original_commit()

            session.commit = commit
            try:
                yield session
            finally:
                active.remove(session)

    original_extract = worker.DocumentService.process_document
    original_classify = worker.BloomService.classify_question

    def extract(path):
        assert active == []
        assert statuses == ['PROCESSING']
        return original_extract(path)

    def classify(text):
        assert active == []
        assert statuses == ['PROCESSING', 'ANALYZING']
        return original_classify(text)

    monkeypatch.setattr(worker, 'AsyncSessionLocal', tracked_session)
    monkeypatch.setattr(worker.DocumentService, 'process_document', extract)
    monkeypatch.setattr(worker.BloomService, 'classify_question', classify)
    response = await upload(client, paper_bytes())
    assert (await client.get(response.json()['status_url'])).json()['processing_status'] == 'COMPLETED'
    assert statuses[-1] == 'COMPLETED'


@pytest.mark.asyncio
async def test_chunked_upload_body_limit(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'MAX_REQUEST_BODY_SIZE_MB', 1)

    async def body():
        yield b'--limit\r\nContent-Disposition: form-data; name="file"; filename="paper.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
        for _ in range(18):
            yield b'x' * (64 * 1024)
        yield b'\r\n--limit--\r\n'

    response = await client.post('/api/v1/papers/upload', content=body(), headers={'Content-Type': 'multipart/form-data; boundary=limit'})
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_restart_marks_interrupted_jobs_failed(db_session):
    from app.models.subject import Subject
    from app.models.question_paper import QuestionPaper
    from app.services.paper_processing_service import fail_interrupted_jobs
    subject = Subject(code='RESTART', name='Databases')
    db_session.add(subject)
    await db_session.flush()
    paper = QuestionPaper(subject_id=subject.id, examination_type='Internal', maximum_marks=5,
                          original_filename='interrupted.docx', stored_file_path='missing', processing_status='ANALYZING')
    db_session.add(paper)
    await db_session.commit()
    await fail_interrupted_jobs()
    await db_session.refresh(paper)
    assert paper.processing_status == 'FAILED'
    assert paper.error_message == 'Processing interrupted by server restart; upload again after deleting this paper.'


@pytest.mark.asyncio
async def test_concurrent_duplicate_inserts_have_one_winner(tmp_path):
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.exc import IntegrityError
    from app.core.database import Base
    from app.models.subject import Subject
    from app.models.question_paper import QuestionPaper
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "concurrent.db"}')
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with factory() as session:
            subject = Subject(code='RACE', name='Databases')
            session.add(subject)
            await session.commit()
            subject_id = subject.id

        async def insert():
            async with factory() as session:
                session.add(QuestionPaper(subject_id=subject_id, examination_type='Internal', maximum_marks=5,
                                         original_filename='same.docx', stored_file_path='same', file_hash='a' * 64))
                try:
                    await session.commit()
                    return 'accepted'
                except IntegrityError:
                    await session.rollback()
                    return 'duplicate'

        assert sorted(await asyncio.gather(insert(), insert())) == ['accepted', 'duplicate']
    finally:
        await engine.dispose()
