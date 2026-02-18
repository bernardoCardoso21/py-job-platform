import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.core_config import settings

# Use the configured URI for tests
TEST_DATABASE_URL = settings.sqlalchemy_database_uri.replace("backend", "test_db")

@pytest.fixture(scope="session", autouse=True)
def setup_test_db_dir():
    import os
    os.makedirs(settings.FILES_DIR, exist_ok=True)

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers():
    return {"Authorization": f"Bearer {settings.API_KEY}"}
