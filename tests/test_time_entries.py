import uuid
from datetime import datetime, timedelta, timezone

import pytest


async def register_user(client, email: str):
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "test12345",
        },
    )

    assert response.status_code == 201

    return response.json()["access_token"]


async def create_project(client, token: str):
    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Time Entry Test",
            "client_name": "Test Client",
            "budget": 100000,
            "hourly_rate": 3000,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


async def create_task(client, token: str, project_id: int):
    response = await client.post(
        f"/projects/{project_id}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Test Task",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_time_entry(client):
    email = f"time-{uuid.uuid4()}@example.com"
    token = await register_user(client, email)
    project_id = await create_project(client, token)

    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=90)

    response = await client.post(
        f"/projects/{project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 201

    entry = response.json()

    assert entry["project_id"] == project_id
    assert entry["duration_seconds"] == 5400
    assert entry["task_id"] is None


@pytest.mark.asyncio
async def test_time_entry_cost(client):
    email = f"cost-{uuid.uuid4()}@example.com"
    token = await register_user(client, email)
    project_id = await create_project(client, token)

    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=90)

    response = await client.post(
        f"/projects/{project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 201

    response = await client.get(
        f"/projects/{project_id}/time-entries/cost",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_seconds"] == 5400
    assert data["total_hours"] == 1.5
    assert data["hourly_rate"] == 3000
    assert data["total_cost"] == 4500


@pytest.mark.asyncio
async def test_timer_start_and_stop(client):
    email = f"timer-{uuid.uuid4()}@example.com"
    token = await register_user(client, email)
    project_id = await create_project(client, token)

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = await client.post(
        f"/projects/{project_id}/time-entries/start",
        headers=headers,
        json={},
    )

    assert response.status_code == 201

    entry = response.json()

    assert entry["project_id"] == project_id
    assert entry["ended_at"] is None
    assert entry["duration_seconds"] is None

    response = await client.post(
        f"/projects/{project_id}/time-entries/start",
        headers=headers,
        json={},
    )

    assert response.status_code == 409

    response = await client.post(
        f"/projects/{project_id}/time-entries/stop",
        headers=headers,
    )

    assert response.status_code == 200

    stopped_entry = response.json()

    assert stopped_entry["ended_at"] is not None
    assert stopped_entry["duration_seconds"] is not None
    assert stopped_entry["duration_seconds"] >= 0


@pytest.mark.asyncio
async def test_create_time_entry_invalid_time_range(client):
    email = f"invalid-time-{uuid.uuid4()}@example.com"
    token = await register_user(client, email)
    project_id = await create_project(client, token)

    started_at = datetime.now(timezone.utc)
    ended_at = started_at - timedelta(minutes=10)

    response = await client.post(
        f"/projects/{project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_time_entry_task_association_and_isolation(client):
    user1_email = f"time-task-user1-{uuid.uuid4()}@example.com"
    user2_email = f"time-task-user2-{uuid.uuid4()}@example.com"

    user1_token = await register_user(client, user1_email)
    user2_token = await register_user(client, user2_email)

    user1_project_id = await create_project(client, user1_token)
    user2_project_id = await create_project(client, user2_token)

    task_id = await create_task(
        client,
        user1_token,
        user1_project_id,
    )

    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=30)

    response = await client.post(
        f"/projects/{user1_project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {user1_token}",
        },
        json={
            "task_id": task_id,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 201

    entry = response.json()

    assert entry["project_id"] == user1_project_id
    assert entry["task_id"] == task_id
    assert entry["duration_seconds"] == 1800

    response = await client.post(
        f"/projects/{user2_project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
        json={
            "task_id": task_id,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_time_entry_delete_and_isolation(client):
    user1_email = f"delete-user1-{uuid.uuid4()}@example.com"
    user2_email = f"delete-user2-{uuid.uuid4()}@example.com"

    user1_token = await register_user(client, user1_email)
    user2_token = await register_user(client, user2_email)

    user1_project_id = await create_project(client, user1_token)
    user2_project_id = await create_project(client, user2_token)

    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=30)

    response = await client.post(
        f"/projects/{user1_project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {user1_token}",
        },
        json={
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 201

    entry = response.json()
    entry_id = entry["id"]

    response = await client.delete(
        f"/projects/{user1_project_id}/time-entries/{entry_id}",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
    )

    assert response.status_code == 404

    response = await client.delete(
        f"/projects/{user1_project_id}/time-entries/{entry_id}",
        headers={
            "Authorization": f"Bearer {user1_token}",
        },
    )

    assert response.status_code == 204

    response = await client.get(
        f"/projects/{user1_project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {user1_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        entry["id"] != entry_id
        for entry in data["items"]
    )


@pytest.mark.asyncio
async def test_timer_stop_without_active_timer(client):
    token = await register_user(
        client,
        f"stop-without-timer-{uuid.uuid4()}@example.com",
    )
    project_id = await create_project(client, token)

    response = await client.post(
        f"/projects/{project_id}/time-entries/stop",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_time_entry_requires_authentication(client):
    response = await client.get(
        "/projects/999999999/time-entries/",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_time_entry_project_not_found(client):
    token = await register_user(
        client,
        f"time-project-not-found-{uuid.uuid4()}@example.com",
    )

    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=30)

    response = await client.post(
        "/projects/999999999/time-entries/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_time_entry_invalid_datetime(client):
    token = await register_user(
        client,
        f"time-invalid-datetime-{uuid.uuid4()}@example.com",
    )
    project_id = await create_project(client, token)

    response = await client.post(
        f"/projects/{project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "started_at": "not-a-datetime",
            "ended_at": "also-not-a-datetime",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_time_entry_nonexistent_task(client):
    token = await register_user(
        client,
        f"time-invalid-task-{uuid.uuid4()}@example.com",
    )
    project_id = await create_project(client, token)

    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=30)

    response = await client.post(
        f"/projects/{project_id}/time-entries/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "task_id": 999999999,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 404
import pytest

@pytest.mark.asyncio
async def test_start_timer_rejects_second_active_timer(
    client,
    auth_token,
    project_factory,
    db_session,
):
    token = await auth_token(
        "second-timer-test@example.com",
    )

    project = await project_factory(token)

    headers = {
        "Authorization": f"Bearer {token}",
    }

    first_response = await client.post(
        f"/projects/{project['id']}/time-entries/start",
        headers=headers,
        json={},
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        f"/projects/{project['id']}/time-entries/start",
        headers=headers,
        json={},
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "A timer is already running for this project",
    }

@pytest.mark.asyncio
async def test_user_cannot_access_another_users_time_entry(
    client,
    auth_token,
    project_factory,
    db_session,
):
    token_1 = await auth_token("user1@example.com")
    token_2 = await auth_token("user2@example.com")

    project = await project_factory(
        token_1,
        name="Private Project",
    )

    response = await client.post(
        f"/projects/{project['id']}/time-entries/",
        headers={
            "Authorization": f"Bearer {token_1}",
        },
        json={
            "started_at": "2026-09-25T10:00:00Z",
            "ended_at": "2026-09-25T11:00:00Z",
        },
    )

    assert response.status_code == 201

    time_entry = response.json()

    response = await client.get(
        f"/projects/{project['id']}/time-entries/",
        headers={
            "Authorization": f"Bearer {token_2}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

    response = await client.delete(
        f"/projects/{project['id']}/time-entries/{time_entry['id']}",
        headers={
            "Authorization": f"Bearer {token_2}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Time entry not found"