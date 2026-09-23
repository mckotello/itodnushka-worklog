import uuid
from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.asyncio
async def test_project_isolation(client, auth_token, project_factory):
    user1_token = await auth_token(f"user1-{uuid.uuid4()}@example.com")
    user2_token = await auth_token(f"user2-{uuid.uuid4()}@example.com")

    project = await project_factory(
        user1_token,
        "Private Project",
    )

    project_id = project["id"]

    response = await client.get(
        f"/projects/{project_id}",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_crud(client, auth_token):
    token = await auth_token(f"crud-{uuid.uuid4()}@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = await client.post(
        "/projects/",
        headers=headers,
        json={
            "name": "CRUD Project",
            "client_name": "Test Client",
            "budget": 50000,
            "hourly_rate": 2500,
        },
    )

    assert response.status_code == 201

    project = response.json()
    project_id = project["id"]

    assert project["name"] == "CRUD Project"
    assert project["client_name"] == "Test Client"
    assert project["budget"] == "50000.00"
    assert project["hourly_rate"] == "2500.00"

    response = await client.get(
        f"/projects/{project_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == project_id

    response = await client.put(
        f"/projects/{project_id}",
        headers=headers,
        json={
            "name": "Updated Project",
            "budget": 75000,
        },
    )

    assert response.status_code == 200

    updated_project = response.json()

    assert updated_project["name"] == "Updated Project"
    assert updated_project["budget"] == "75000.00"

    response = await client.delete(
        f"/projects/{project_id}",
        headers=headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/projects/{project_id}",
        headers=headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_list(client, auth_token, project_factory):
    token = await auth_token(f"list-{uuid.uuid4()}@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    project = await project_factory(
        token,
        "List Project",
    )

    project_id = project["id"]

    response = await client.get(
        "/projects/",
        headers=headers,
    )

    assert response.status_code == 200

    projects = response.json()

    assert isinstance(projects, list)
    assert any(project["id"] == project_id for project in projects)


@pytest.mark.asyncio
async def test_project_summary(client, auth_token, project_factory):
    token = await auth_token(f"summary-{uuid.uuid4()}@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    project = await project_factory(
        token,
        "Summary Project",
    )

    project_id = project["id"]

    started_at = datetime.now(timezone.utc) - timedelta(hours=1)
    ended_at = datetime.now(timezone.utc)

    response = await client.post(
        f"/projects/{project_id}/time-entries/",
        headers=headers,
        json={
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 201

    response = await client.get(
        f"/projects/{project_id}/summary",
        headers=headers,
    )

    assert response.status_code == 200

    summary = response.json()

    assert summary["project_id"] == project_id
    assert summary["budget"] == "100000.00"
    assert summary["hourly_rate"] == "3000.00"
    assert summary["total_seconds"] == 3600
    assert summary["total_hours"] == "1"
    assert summary["total_cost"] == "3000.00"
    assert summary["remaining_budget"] == "97000.00"
    assert summary["budget_used_percent"] == "3.00"


@pytest.mark.asyncio
async def test_project_summary_isolation(
    client,
    auth_token,
    project_factory,
):
    user1_token = await auth_token(
        f"summary-user1-{uuid.uuid4()}@example.com",
    )
    user2_token = await auth_token(
        f"summary-user2-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        user1_token,
        "Private Summary",
    )

    project_id = project["id"]

    response = await client.get(
        f"/projects/{project_id}/summary",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_dashboard(client, auth_token, project_factory):
    token = await auth_token(f"dashboard-{uuid.uuid4()}@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    project = await project_factory(
        token,
        "Dashboard Project",
    )

    project_id = project["id"]

    started_at = datetime.now(timezone.utc) - timedelta(hours=1)
    ended_at = datetime.now(timezone.utc)

    response = await client.post(
        f"/projects/{project_id}/time-entries/",
        headers=headers,
        json={
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
        },
    )

    assert response.status_code == 201

    response = await client.get(
        "/projects/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    dashboard = response.json()

    assert dashboard["total_projects"] == 1
    assert dashboard["active_projects"] == 1
    assert dashboard["total_seconds"] == 3600
    assert dashboard["total_hours"] == "1"
    assert dashboard["total_budget"] == "100000.00"
    assert dashboard["total_cost"] == "3000.00"
    assert dashboard["budget_used_percent"] == "3.00"


@pytest.mark.asyncio
async def test_project_requires_authentication(client):
    response = await client.get("/projects/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_project_not_found(client, auth_token):
    token = await auth_token(
        f"not-found-{uuid.uuid4()}@example.com",
    )

    response = await client.get(
        "/projects/999999999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_creation_requires_name(client, auth_token):
    token = await auth_token(
        f"validation-{uuid.uuid4()}@example.com",
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "client_name": "Test Client",
            "budget": 100000,
            "hourly_rate": 3000,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_project_creation_rejects_invalid_money_values(
    client,
    auth_token,
):
    token = await auth_token(
        f"money-{uuid.uuid4()}@example.com",
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Invalid Budget",
            "budget": "not-a-number",
            "hourly_rate": 3000,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_project_creation_rejects_invalid_deadline(
    client,
    auth_token,
):
    token = await auth_token(
        f"deadline-{uuid.uuid4()}@example.com",
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Invalid Deadline",
            "budget": 100000,
            "hourly_rate": 3000,
            "deadline": "not-a-date",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_project_update_isolation(
    client,
    auth_token,
    project_factory,
):
    user1_token = await auth_token(
        f"update-user1-{uuid.uuid4()}@example.com",
    )
    user2_token = await auth_token(
        f"update-user2-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        user1_token,
        "Private Update Project",
    )

    project_id = project["id"]

    response = await client.put(
        f"/projects/{project_id}",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
        json={
            "name": "Unauthorized Update",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_delete_isolation(
    client,
    auth_token,
    project_factory,
):
    user1_token = await auth_token(
        f"delete-user1-{uuid.uuid4()}@example.com",
    )
    user2_token = await auth_token(
        f"delete-user2-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        user1_token,
        "Private Delete Project",
    )

    project_id = project["id"]

    response = await client.delete(
        f"/projects/{project_id}",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
    )

    assert response.status_code == 404

    response = await client.get(
        f"/projects/{project_id}",
        headers={
            "Authorization": f"Bearer {user1_token}",
        },
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_project_creation_rejects_negative_budget(
    client,
    auth_token,
):
    token = await auth_token(
        f"negative-budget-{uuid.uuid4()}@example.com",
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Negative Budget",
            "budget": -1000,
            "hourly_rate": 3000,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_project_creation_rejects_negative_hourly_rate(
    client,
    auth_token,
):
    token = await auth_token(
        f"negative-rate-{uuid.uuid4()}@example.com",
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Negative Hourly Rate",
            "budget": 100000,
            "hourly_rate": -3000,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_rejects_empty_name(client, auth_token):
    token = await auth_token(
        f"empty-name-{uuid.uuid4()}@example.com"
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "   ",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_rejects_invalid_status(client, auth_token):
    token = await auth_token(
        f"invalid-status-{uuid.uuid4()}@example.com"
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Test Project",
            "status": "invalid",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_strips_name(client, auth_token):
    token = await auth_token(
        f"strip-name-{uuid.uuid4()}@example.com"
    )

    response = await client.post(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "  Test Project  ",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"