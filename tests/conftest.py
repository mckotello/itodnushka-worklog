import os
import sys
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://worklog:worklog@postgres_test:5432/worklog_test"
)

from app.main import app
from app.api import dependencies


test_engine = create_async_engine(
    os.environ["DATABASE_URL"],
    poolclass=NullPool,
)

test_session_factory = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


async def override_get_db():
    async with test_session_factory() as session:
        yield session


app.dependency_overrides[dependencies.get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def auth_token(client):
    async def _create(email: str):
        response = await client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "test12345",
            },
        )

        assert response.status_code == 201

        return response.json()["access_token"]

    return _create


@pytest_asyncio.fixture
async def project_factory(client):
    async def _create(token: str, name: str = "Test Project"):
        response = await client.post(
            "/projects/",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "name": name,
                "client_name": "Test Client",
                "budget": 100000,
                "hourly_rate": 3000,
            },
        )

        assert response.status_code == 201

        return response.json()

    return _create
@pytest_asyncio.fixture
async def task_factory(client):
    async def _create(
        token: str,
        project_id: int,
        name: str = "Test Task",
    ):
        response = await client.post(
            f"/projects/{project_id}/tasks/",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "name": name,
            },
        )

        assert response.status_code == 201

        return response.json()

    return _create