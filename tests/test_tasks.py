import uuid

import pytest


async def create_task(
    client,
    token: str,
    project_id: int,
    name: str,
    status: str | None = None,
):
    payload = {
        "name": name,
    }

    if status is not None:
        payload["status"] = status

    response = await client.post(
        f"/projects/{project_id}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json=payload,
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
    assert response.json()["detail"] == "Project not found"

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
    assert response.json()["detail"] == "Project not found"

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
    assert response.json()["detail"] == "Task not found"

    response = await client.delete(
        f"/projects/{project_id}/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {user2_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


@pytest.mark.asyncio
async def test_task_list(
    client,
    auth_token,
    project_factory,
):
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

    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["pages"] == 1
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Second task"
    assert data["items"][1]["name"] == "First task"


@pytest.mark.asyncio
async def test_task_update(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-update-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Test Project",
    )

    task = await create_task(
        client,
        token,
        project["id"],
        "Original task",
    )

    response = await client.put(
        f"/projects/{project['id']}/tasks/{task['id']}",
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

    assert updated_task["id"] == task["id"]
    assert updated_task["project_id"] == project["id"]
    assert updated_task["name"] == "Updated task"
    assert updated_task["status"] == "in_progress"


@pytest.mark.asyncio
async def test_task_update_status_preserves_name(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-partial-update-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Project",
    )

    task = await create_task(
        client,
        token,
        project["id"],
        "Important Task",
    )

    response = await client.put(
        f"/projects/{project['id']}/tasks/{task['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "status": "done",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task["id"]
    assert data["project_id"] == project["id"]
    assert data["name"] == "Important Task"
    assert data["status"] == "done"


@pytest.mark.asyncio
async def test_task_delete(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-delete-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Test Project",
    )

    task = await create_task(
        client,
        token,
        project["id"],
        "Task to delete",
    )

    response = await client.delete(
        f"/projects/{project['id']}/tasks/{task['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 204

    response = await client.get(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []


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

    response = await client.post(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_rejects_empty_name(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"empty-task-name-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(token)

    response = await client.post(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "   ",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_rejects_invalid_status(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"invalid-task-status-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(token)

    response = await client.post(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Test Task",
            "status": "invalid",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_rejects_too_long_name(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"long-task-name-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(token)

    response = await client.post(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "a" * 256,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_strips_name(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"strip-task-name-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(token)

    response = await client.post(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "  Test Task  ",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Task"


@pytest.mark.asyncio
async def test_task_project_not_found(
    client,
    auth_token,
):
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
async def test_create_task_in_nonexistent_project(
    client,
    auth_token,
):
    token = await auth_token(
        f"task-no-project-{uuid.uuid4()}@example.com",
    )

    response = await client.post(
        "/projects/999999/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Orphan Task",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_task_requires_authentication(client):
    response = await client.get(
        "/projects/999999999/tasks/",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_task_list_requires_authentication(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-list-auth-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Protected Project",
    )

    response = await client.get(
        f"/projects/{project['id']}/tasks/",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_task_list_pagination(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-pagination-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Pagination Project",
    )

    for i in range(5):
        await create_task(
            client,
            token,
            project["id"],
            f"Task {i + 1}",
        )

    response = await client.get(
        f"/projects/{project['id']}/tasks/?page=1&limit=2",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_task_list_pagination_second_page(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-pagination-page2-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Pagination Page 2 Project",
    )

    created_tasks = []

    for i in range(5):
        created_tasks.append(
            await create_task(
                client,
                token,
                project["id"],
                f"Task {i + 1}",
            )
        )

    response = await client.get(
        f"/projects/{project['id']}/tasks/?page=2&limit=2",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2

    assert data["items"][0]["id"] == created_tasks[2]["id"]
    assert data["items"][1]["id"] == created_tasks[1]["id"]


@pytest.mark.asyncio
async def test_task_list_pagination_out_of_range(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-pagination-range-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Pagination Range Project",
    )

    for i in range(5):
        await create_task(
            client,
            token,
            project["id"],
            f"Task {i + 1}",
        )

    response = await client.get(
        f"/projects/{project['id']}/tasks/?page=4&limit=2",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 4
    assert data["limit"] == 2
    assert data["pages"] == 3
    assert data["items"] == []


@pytest.mark.asyncio
async def test_task_list_rejects_invalid_page(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-pagination-invalid-page-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Invalid Page Project",
    )

    response = await client.get(
        f"/projects/{project['id']}/tasks/?page=0",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_task_list_rejects_invalid_limit(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-pagination-invalid-limit-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        "Task Invalid Limit Project",
    )

    response = await client.get(
        f"/projects/{project['id']}/tasks/?limit=101",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_task(
    client,
    auth_token,
    project_factory,
):
    owner_token = await auth_token(
        f"task-access-owner-{uuid.uuid4()}@example.com",
    )
    other_token = await auth_token(
        f"task-access-other-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        owner_token,
        name="Owner Project",
    )

    task = await create_task(
        client,
        owner_token,
        project["id"],
        "Private Task",
    )

    response = await client.get(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {other_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

    response = await client.put(
        f"/projects/{project['id']}/tasks/{task['id']}",
        headers={
            "Authorization": f"Bearer {other_token}",
        },
        json={
            "name": "Hacked Task",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

    response = await client.delete(
        f"/projects/{project['id']}/tasks/{task['id']}",
        headers={
            "Authorization": f"Bearer {other_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


@pytest.mark.asyncio
async def test_user_cannot_create_task_in_another_users_project(
    client,
    auth_token,
    project_factory,
):
    owner_token = await auth_token(
        f"task-create-owner-{uuid.uuid4()}@example.com",
    )
    other_token = await auth_token(
        f"task-create-other-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        owner_token,
        name="Owner Project",
    )

    response = await client.post(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {other_token}",
        },
        json={
            "name": "Foreign Task",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_create_task_and_list_project_tasks(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-list-test-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        name="Task List Project",
    )

    task = await create_task(
        client,
        token,
        project["id"],
        "First Task",
    )

    assert task["project_id"] == project["id"]
    assert task["name"] == "First Task"
    assert task["status"] == "todo"

    response = await client.get(
        f"/projects/{project['id']}/tasks/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["pages"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == task["id"]
    assert data["items"][0]["name"] == "First Task"


@pytest.mark.asyncio
async def test_update_task_status(
    client,
    auth_token,
    project_factory,
):
    token = await auth_token(
        f"task-update-status-{uuid.uuid4()}@example.com",
    )

    project = await project_factory(
        token,
        name="Task Update Project",
    )

    task = await create_task(
        client,
        token,
        project["id"],
        "Task To Update",
    )

    assert task["status"] == "todo"

    response = await client.put(
        f"/projects/{project['id']}/tasks/{task['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "status": "in_progress",
        },
    )

    assert response.status_code == 200

    updated_task = response.json()

    assert updated_task["id"] == task["id"]
    assert updated_task["project_id"] == project["id"]
    assert updated_task["name"] == "Task To Update"
    assert updated_task["status"] == "in_progress"