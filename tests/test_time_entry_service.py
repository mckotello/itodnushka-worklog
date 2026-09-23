from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.services.time_entry_service import (
    calculate_duration_seconds,
    calculate_time_cost,
    get_active_timer,
    get_active_user_timer,
    get_project_task,
    get_project_time_entries,
    get_user_project,
    get_user_time_entry,
)
from app.security import hash_password


@pytest.mark.asyncio
async def test_get_user_project_returns_owned_project(db_session):
    user = User(
        email="time-service-owner@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Time Project",
    )

    db_session.add(project)
    await db_session.commit()

    result = await get_user_project(
        session=db_session,
        project_id=project.id,
        user=user,
    )

    assert result is not None
    assert result.id == project.id


@pytest.mark.asyncio
async def test_get_user_project_rejects_other_user(db_session):
    owner = User(
        email="time-service-owner-2@example.com",
        password_hash=hash_password("test12345"),
    )

    other_user = User(
        email="time-service-other@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add_all([owner, other_user])
    await db_session.flush()

    project = Project(
        user_id=owner.id,
        name="Private Time Project",
    )

    db_session.add(project)
    await db_session.commit()

    result = await get_user_project(
        session=db_session,
        project_id=project.id,
        user=other_user,
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_project_task_checks_project(db_session):
    user = User(
        email="time-service-task@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Task Project",
    )

    other_project = Project(
        user_id=user.id,
        name="Other Project",
    )

    db_session.add_all([project, other_project])
    await db_session.flush()

    task = Task(
        project_id=project.id,
        name="Test Task",
    )

    db_session.add(task)
    await db_session.commit()

    result = await get_project_task(
        session=db_session,
        project_id=project.id,
        task_id=task.id,
    )

    assert result is not None
    assert result.id == task.id

    wrong_project_result = await get_project_task(
        session=db_session,
        project_id=other_project.id,
        task_id=task.id,
    )

    assert wrong_project_result is None


@pytest.mark.asyncio
async def test_calculate_duration_seconds():
    started_at = datetime(
        2026,
        1,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ended_at = started_at + timedelta(
        hours=2,
        minutes=30,
    )

    result = calculate_duration_seconds(
        started_at=started_at,
        ended_at=ended_at,
    )

    assert result == 9000


@pytest.mark.asyncio
async def test_get_active_timer(db_session):
    user = User(
        email="active-timer-service@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Active Timer Project",
    )

    db_session.add(project)
    await db_session.flush()

    active_entry = TimeEntry(
        project_id=project.id,
        started_at=datetime.now(timezone.utc),
    )

    db_session.add(active_entry)
    await db_session.commit()

    result = await get_active_timer(
        session=db_session,
        project_id=project.id,
    )

    assert result is not None
    assert result.id == active_entry.id


@pytest.mark.asyncio
async def test_get_active_user_timer_isolation(db_session):
    user1 = User(
        email="active-user-1@example.com",
        password_hash=hash_password("test12345"),
    )

    user2 = User(
        email="active-user-2@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add_all([user1, user2])
    await db_session.flush()

    project1 = Project(
        user_id=user1.id,
        name="User 1 Project",
    )

    project2 = Project(
        user_id=user2.id,
        name="User 2 Project",
    )

    db_session.add_all([project1, project2])
    await db_session.flush()

    entry1 = TimeEntry(
        project_id=project1.id,
        started_at=datetime.now(timezone.utc),
    )

    entry2 = TimeEntry(
        project_id=project2.id,
        started_at=datetime.now(timezone.utc),
    )

    db_session.add_all([entry1, entry2])
    await db_session.commit()

    result = await get_active_user_timer(
        session=db_session,
        project_id=project1.id,
        user=user1,
    )

    assert result is not None
    assert result.id == entry1.id

    other_user_result = await get_active_user_timer(
        session=db_session,
        project_id=project1.id,
        user=user2,
    )

    assert other_user_result is None


@pytest.mark.asyncio
async def test_get_project_time_entries_orders_by_started_at(db_session):
    user = User(
        email="time-order-service@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Order Project",
    )

    db_session.add(project)
    await db_session.flush()

    first = TimeEntry(
        project_id=project.id,
        started_at=datetime(
            2026,
            1,
            1,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        ended_at=datetime(
            2026,
            1,
            1,
            11,
            0,
            tzinfo=timezone.utc,
        ),
        duration_seconds=3600,
    )

    second = TimeEntry(
        project_id=project.id,
        started_at=datetime(
            2026,
            1,
            2,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        ended_at=datetime(
            2026,
            1,
            2,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        duration_seconds=7200,
    )

    db_session.add_all([first, second])
    await db_session.commit()

    result = await get_project_time_entries(
        session=db_session,
        project_id=project.id,
    )

    assert len(result) == 2
    assert result[0].id == second.id
    assert result[1].id == first.id


@pytest.mark.asyncio
async def test_get_user_time_entry_checks_user_and_project(db_session):
    owner = User(
        email="entry-owner@example.com",
        password_hash=hash_password("test12345"),
    )

    other_user = User(
        email="entry-other@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add_all([owner, other_user])
    await db_session.flush()

    project = Project(
        user_id=owner.id,
        name="Entry Project",
    )

    db_session.add(project)
    await db_session.flush()

    entry = TimeEntry(
        project_id=project.id,
        started_at=datetime.now(timezone.utc),
    )

    db_session.add(entry)
    await db_session.commit()

    result = await get_user_time_entry(
        session=db_session,
        project_id=project.id,
        time_entry_id=entry.id,
        user=owner,
    )

    assert result is not None
    assert result.id == entry.id

    other_user_result = await get_user_time_entry(
        session=db_session,
        project_id=project.id,
        time_entry_id=entry.id,
        user=other_user,
    )

    assert other_user_result is None


@pytest.mark.asyncio
async def test_calculate_time_cost(db_session):
    user = User(
        email="cost-service@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Cost Project",
        hourly_rate=Decimal("3000.00"),
    )

    db_session.add(project)
    await db_session.flush()

    db_session.add_all([
        TimeEntry(
            project_id=project.id,
            started_at=datetime(
                2026,
                1,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                1,
                1,
                11,
                30,
                tzinfo=timezone.utc,
            ),
            duration_seconds=5400,
        ),
        TimeEntry(
            project_id=project.id,
            started_at=datetime(
                2026,
                1,
                2,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                1,
                2,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            duration_seconds=3600,
        ),
    ])

    await db_session.commit()

    result = await calculate_time_cost(
        session=db_session,
        project=project,
    )

    assert result["total_seconds"] == 9000
    assert result["total_hours"] == 2.5
    assert result["hourly_rate"] == Decimal("3000.00")
    assert result["total_cost"] == Decimal("7500.000")