import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app import main
from app.core import database
from app.services import paper_processing_service


@pytest.mark.asyncio
async def test_startup_explains_pending_migrations_before_recovering_jobs(tmp_path, monkeypatch):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "outdated.db"}')
    try:
        async with engine.begin() as connection:
            await connection.execute(text('CREATE TABLE question_papers (id INTEGER PRIMARY KEY, processing_status TEXT, updated_at TEXT)'))
            await connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
            await connection.execute(text("INSERT INTO alembic_version VALUES ('c0a1b2c3d4e5')"))
        monkeypatch.setattr(database, 'engine', engine)
        monkeypatch.setattr(paper_processing_service, 'AsyncSessionLocal', async_sessionmaker(engine))
        with pytest.raises(RuntimeError, match='alembic upgrade head'):
            async with main.lifespan(main.app):
                pytest.fail('An outdated database must not serve requests')
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_startup_accepts_current_schema(tmp_path, monkeypatch):
    from pathlib import Path
    from alembic.script import ScriptDirectory
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "current.db"}')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(database.Base.metadata.create_all)
            await connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
            head = ScriptDirectory(str(Path(__file__).resolve().parents[1] / 'alembic')).get_current_head()
            await connection.execute(text('INSERT INTO alembic_version VALUES (:head)'), {'head': head})
        monkeypatch.setattr(database, 'engine', engine)
        monkeypatch.setattr(paper_processing_service, 'AsyncSessionLocal', async_sessionmaker(engine))
        monkeypatch.setattr(main.settings, 'WARMUP_EMBEDDING_ON_STARTUP', False)
        async with main.lifespan(main.app):
            pass
    finally:
        await engine.dispose()
