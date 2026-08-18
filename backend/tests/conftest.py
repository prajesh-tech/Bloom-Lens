import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.models.bloom_level import BloomLevel
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initializes in-memory SQLite database tables and seeds Bloom levels L1 - L6 for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed Bloom Levels L1 to L6
    async with TestAsyncSessionLocal() as session:
        seed_levels = [
            BloomLevel(id=1, code="L1", name="Remember", description="Recall facts", keywords=["define", "list"]),
            BloomLevel(id=2, code="L2", name="Understand", description="Explain concepts", keywords=["explain", "describe"]),
            BloomLevel(id=3, code="L3", name="Apply", description="Use information", keywords=["apply", "calculate"]),
            BloomLevel(id=4, code="L4", name="Analyze", description="Draw connections", keywords=["analyze", "compare"]),
            BloomLevel(id=5, code="L5", name="Evaluate", description="Justify stand", keywords=["evaluate", "justify"]),
            BloomLevel(id=6, code="L6", name="Create", description="Produce new work", keywords=["design", "develop"]),
        ]
        session.add_all(seed_levels)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
