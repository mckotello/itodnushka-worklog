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