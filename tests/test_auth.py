import uuid

import jwt
import pytest

from app.auth import SECRET_KEY, ALGORITHM


@pytest.mark.asyncio
async def test_register(client):
    email = f"user-{uuid.uuid4()}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "test12345",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    email = f"duplicate-{uuid.uuid4()}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "test12345",
        },
    )

    assert response.status_code == 201

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "another-password",
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    email = f"login-{uuid.uuid4()}@example.com"
    password = "test12345"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    email = f"invalid-password-{uuid.uuid4()}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "test12345",
        },
    )

    assert response.status_code == 201

    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_invalid_token(client):
    response = await client.get(
        "/projects/",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token(client):
    token = jwt.encode(
        {
            "sub": "1",
            "exp": 0,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = await client.get(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "test12345",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_requires_fields(client):
    response = await client.post(
        "/auth/register",
        json={},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_email(client):
    response = await client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "test12345",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_requires_fields(client):
    response = await client.post(
        "/auth/login",
        json={},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_rejects_short_password(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": f"short-password-{uuid.uuid4()}@example.com",
            "password": "1234567",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_rejects_short_password(client):
    response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "1234567",
        },
    )

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_protected_endpoint_rejects_invalid_token(
        client,
):
    response = await client.get(
        "/projects/",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

@pytest.mark.asyncio
async def test_protected_endpoint_rejects_missing_token(
        client,
):
    response = await client.get("/projects/")

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_rejects_invalid_password(
        client,
        db_session,
):
    email = "invalid-password@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct-password",
        },
    )

    assert response.status_code == 201

    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(
        client,
        db_session,
):
    email = "duplicate@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 201

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email already exists"

@pytest.mark.asyncio
async def test_register_rejects_short_password(
        client,
        db_session,
):
    response = await client.post(
        "/auth/register",
        json={
            "email": "short-password@example.com",
            "password": "1234567",
        },
    )

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_rejects_invalid_email(
        client,
        db_session,
):
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_login_and_access_protected_endpoint(
        client,
        db_session,
):
    email = "auth-flow@example.com"
    password = "password123"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["token_type"] == "bearer"

    token = data["access_token"]

    response = await client.get(
        "/projects/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    projects = response.json()

    assert projects["total"] == 0
    assert projects["items"] == []

@pytest.mark.asyncio
async def test_user_cannot_access_another_users_project(
        client,
        db_session,
        auth_token,
        project_factory,
):
    owner_token = await auth_token("project-owner@example.com")
    other_user_token = await auth_token("other-project-user@example.com")

    project = await project_factory(
        owner_token,
        name="Private Project",
    )

    response = await client.get(
        f"/projects/{project['id']}",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

@pytest.mark.asyncio
async def test_user_cannot_update_another_users_project(
        client,
        auth_token,
        project_factory,
):
    owner_token = await auth_token("update-owner@example.com")
    other_user_token = await auth_token("update-other@example.com")

    project = await project_factory(
        owner_token,
        name="Private Project",
    )

    response = await client.put(
        f"/projects/{project['id']}",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
        json={
            "name": "Hacked Project",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"
@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_project(
    client,
    auth_token,
    project_factory,
):
    owner_token = await auth_token("delete-owner@example.com")
    other_user_token = await auth_token("delete-other@example.com")

    project = await project_factory(
        owner_token,
        name="Private Project",
    )

    response = await client.delete(
        f"/projects/{project['id']}",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

@pytest.mark.asyncio
async def test_user_project_list_contains_only_own_projects(
    client,
    auth_token,
    project_factory,
):
    first_user_token = await auth_token("list-owner@example.com")
    second_user_token = await auth_token("list-other@example.com")

    await project_factory(
        first_user_token,
        name="First User Project",
    )
    await project_factory(
        second_user_token,
        name="Second User Project",
    )

    response = await client.get(
        "/projects/",
        headers={
            "Authorization": f"Bearer {first_user_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "First User Project"

@pytest.mark.asyncio
async def test_user_cannot_access_another_users_project_summary(
    client,
    auth_token,
    project_factory,
):
    owner_token = await auth_token("summary-owner@example.com")
    other_user_token = await auth_token("summary-other@example.com")

    project = await project_factory(
        owner_token,
        name="Private Summary Project",
    )

    response = await client.get(
        f"/projects/{project['id']}/summary",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

@pytest.mark.asyncio
async def test_create_project_requires_authentication(client):
    response = await client.post(
        "/projects/",
        json={
            "name": "Unauthorized Project",
        },
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_project_requires_authentication(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token("update-auth@example.com")

    project = await project_factory(
        token,
        name="Protected Project",
    )

    response = await client.put(
        f"/projects/{project['id']}",
        json={
            "name": "Changed Project",
        },
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_delete_project_requires_authentication(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token("delete-auth@example.com")

    project = await project_factory(
        token,
        name="Protected Project",
    )

    response = await client.delete(
        f"/projects/{project['id']}",
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_user_cannot_access_another_users_project_tasks(
    client,
    auth_token,
    project_factory,
):
    owner_token = await auth_token("task-owner@example.com")
    other_user_token = await auth_token("task-other@example.com")

    project = await project_factory(
        owner_token,
        name="Private Tasks Project",
    )

    response = await client.get(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {other_user_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"