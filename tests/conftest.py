import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.core_config import settings
from backend.db.session import engine, Base


@pytest.fixture(scope="session", autouse=True)
def setup_test_db_dir():
    import os
    os.makedirs(settings.FILES_DIR, exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers():
    return {"Authorization": f"Bearer {settings.API_KEY}"}
