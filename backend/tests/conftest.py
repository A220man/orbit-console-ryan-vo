"""Test configuration and fixtures."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import Settings
from app.core.database import Base, get_db

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings."""
    return Settings(
        environment="test",
        debug=True,
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key-for-testing-only-32-chars",
        oidc_issuer_url="http://localhost:8080/realms/test",
        oidc_client_id="test-client",
        oidc_redirect_uri="http://localhost:3000/callback",
    )


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncSession:
    """Create test session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_session):
    """Create test client with overridden dependencies."""
    from httpx import AsyncClient, ASGITransport

    def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """Mock auth headers for testing."""
    return {"Authorization": "Bearer test-token"}