import pytest

from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.security import hash_password
from app.services.task_service import (
    get_project_tasks,
    get_user_project,
    get_user_task,
)


async def create_user(db_session, email: str) -> User:
    user = User(
        email=email,
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    return user


async def create_project(db_session, user: User, name: str) -> Project:
    project = Project(
        user_id=user.id,
        name=name,
    )

    db_session.add(project)
    await db_session.flush()

    return project


async def create_task(db_session, project: Project, name: str) -> Task:
    task = Task(
        project_id=project.id,
        name=name,
    )

    db_session.add(task)
    await db_session.flush()

    return task


@pytest.mark.asyncio
async def test_get_user_project_returns_owned_project(db_session):
    user = await create_user(
        db_session,
        "task-service-owner@example.com",
    )

    project = await create_project(db_session, user, "Owned Project")

    result = await get_user_project(
        session=db_session,
        project_id=project.id,
        user=user,
    )

    assert result is not None
    assert result.id == project.id


@pytest.mark.asyncio
async def test_get_user_project_rejects_other_user_project(db_session):
    owner = await create_user(
        db_session,
        "task-service-owner-2@example.com",
    )

    other_user = await create_user(db_session, "task-service-other@example.com")

    project = await create_project(db_session, owner, "Private Project")

    result = await get_user_project(
        session=db_session,
        project_id=project.id,
        user=other_user,
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_project_tasks_returns_only_project_tasks(db_session):
    user = await create_user(
        db_session,
        "task-list-service@example.com",
    )

    project = await create_project(db_session, user, "Main Project")
    other_project = await create_project(db_session, user, "Other Project")

    task_1 = await create_task(db_session, project, "Task 1")
    task_2 = await create_task(db_session, project, "Task 2")
    await create_task(db_session, other_project, "Other Task")

    await db_session.commit()

    result = await get_project_tasks(
        session=db_session,
        project_id=project.id,
    )

    result_ids = {task.id for task in result}

    assert len(result) == 2
    assert result_ids == {task_1.id, task_2.id}


@pytest.mark.asyncio
async def test_get_user_task_checks_project_and_user(db_session):
    owner = await create_user(
        db_session,
        "task-owner@example.com",
    )

    other_user = await create_user(db_session, "task-other@example.com")

    project = await create_project(db_session, owner, "Owner Project")
    task = await create_task(db_session, project, "Private Task")

    await db_session.commit()

    result = await get_user_task(
        session=db_session,
        project_id=project.id,
        task_id=task.id,
        user=owner,
    )

    assert result is not None
    assert result.id == task.id

    other_result = await get_user_task(
        session=db_session,
        project_id=project.id,
        task_id=task.id,
        user=other_user,
    )

    assert other_result is None

    wrong_project_result = await get_user_task(
        session=db_session,
        project_id=999999,
        task_id=task.id,
        user=owner,
    )

    assert wrong_project_result is None