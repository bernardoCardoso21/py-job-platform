import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.main import app
from backend.db.session import get_db
from backend.db.models import Base
from backend.core_config import settings

# Use a separate test database or just the same one if local
# For simplicity in this checkpoint, we'll use the main one but could use an in-memory or different DB
TEST_DATABASE_URL = settings.DATABASE_URL.replace("backend", "test_db")

@pytest.fixture(scope="session", autouse=True)
def setup_test_db_dir():
    import os
    os.makedirs(settings.FILES_DIR, exist_ok=True)

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers():
    return {"Authorization": f"Bearer {settings.API_KEY}"}
