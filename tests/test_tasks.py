import uuid

import pytest


async def create_task(client, token: str, project_id: int, name: str):
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


@pytest.mark.asyncio
async def test_task_creation_and_project_isolation(
    client,
    auth_token,
    project_factory,
):
    user1_token = await auth_token(
        f"tasks-user1-{uuid.uuid4()}@example.com",
    )
    user2_token = await auth_token(
        f"tasks-user2-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        user1_token,
        "Task Test Project",
    )

    project_id = project["id"]

    task = await create_task(
        client,
        user1_token,
        project_id,
        "Implement API tests",
    )

    task_id = task["id"]

    assert task["project_id"] == project_id
    assert task["name"] == "Implement API tests"
    assert task["status"] == "todo"

    response = await client.get(
        f"/projects/{project_id}/tasks/",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
    )

    assert response.status_code == 404

    response = await client.post(
        f"/projects/{project_id}/tasks/",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
        json={
            "name": "Unauthorized task",
        },
    )

    assert response.status_code == 404

    response = await client.put(
        f"/projects/{project_id}/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
        json={
            "name": "Hacked task",
        },
    )

    assert response.status_code == 404

    response = await client.delete(
        f"/projects/{project_id}/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_task_list(client, auth_token, project_factory):
    token = await auth_token(
        f"task-list-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Test Project",
    )

    project_id = project["id"]

    await create_task(
        client,
        token,
        project_id,
        "First task",
    )

    await create_task(
        client,
        token,
        project_id,
        "Second task",
    )

    response = await client.get(
        f"/projects/{project_id}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    tasks = response.json()

    assert len(tasks) == 2
    assert tasks[0]["name"] == "First task"
    assert tasks[1]["name"] == "Second task"


@pytest.mark.asyncio
async def test_task_update(client, auth_token, project_factory):
    token = await auth_token(
        f"task-update-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Test Project",
    )

    project_id = project["id"]

    task = await create_task(
        client,
        token,
        project_id,
        "Original task",
    )

    task_id = task["id"]

    response = await client.put(
        f"/projects/{project_id}/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Updated task",
            "status": "in_progress",
        },
    )

    assert response.status_code == 200

    updated_task = response.json()

    assert updated_task["id"] == task_id
    assert updated_task["project_id"] == project_id
    assert updated_task["name"] == "Updated task"
    assert updated_task["status"] == "in_progress"


@pytest.mark.asyncio
async def test_task_delete(client, auth_token, project_factory):
    token = await auth_token(
        f"task-delete-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Test Project",
    )

    project_id = project["id"]

    task = await create_task(
        client,
        token,
        project_id,
        "Task to delete",
    )

    task_id = task["id"]

    response = await client.delete(
        f"/projects/{project_id}/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 204

    response = await client.get(
        f"/projects/{project_id}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    tasks = response.json()

    assert all(task["id"] != task_id for task in tasks)


@pytest.mark.asyncio
async def test_task_creation_requires_name(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-validation-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Validation Project",
    )

    project_id = project["id"]

    response = await client.post(
        f"/projects/{project_id}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_task_project_not_found(client, auth_token):
    token = await auth_token(
        f"task-project-not-found-{uuid.uuid4()}@example.com",
    )

    response = await client.post(
        "/projects/999999999/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Task for missing project",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_task_requires_authentication(client):
    response = await client.get(
        "/projects/999999999/tasks/",
    )

    assert response.status_code == 401