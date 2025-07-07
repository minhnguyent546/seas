import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionLocal, init_db
from app.main import app
from tests.utils.users import get_superuser_token_headers


@pytest_asyncio.fixture(scope="session", autouse=True)
async def session():
    """Create a database session for the test session."""
    async with AsyncSessionLocal() as async_session_local:  # pyright: ignore[reportGeneralTypeIssues]
        await init_db(session=async_session_local)
        yield async_session_local


@pytest_asyncio.fixture(scope="session")
async def client():
    """Asynchronous test client for FastAPI."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="session")
async def superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    headers = await get_superuser_token_headers(client=client)
    return headers
