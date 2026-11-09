from typing import AsyncGenerator
import asyncio
from pathlib import Path
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.logging import logger

# Create async engine based on settings.DATABASE_URL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.APP_ENV == "development_verbose"),
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass


async def ensure_database_schema_current() -> None:
    """Reject missing migrations before startup tasks access newer columns."""
    migration_path = Path(__file__).resolve().parents[2] / "alembic"
    expected = await asyncio.to_thread(lambda: set(ScriptDirectory(str(migration_path)).get_heads()))
    async with engine.connect() as connection:
        current = await connection.run_sync(
            lambda sync: set(MigrationContext.configure(sync).get_current_heads())
        )
    if current != expected:
        raise RuntimeError(
            "Database schema is out of date. From backend/, run "
            "`.venv/bin/alembic upgrade head`, then restart the backend. "
            "Back up existing data before applying migrations."
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a database session to API route handlers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error, rolled back: {e}")
            raise
        finally:
            await session.close()
