from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.project import Project
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.services.project_access_service import get_user_project
from app.services.project_service import (
    calculate_dashboard,
    calculate_project_summary,
)
from app.security import hash_password


@pytest.mark.asyncio
async def test_get_user_project_returns_owned_project(
    db_session,
):
    user = User(
        email="service-owner@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Owned Project",
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
async def test_get_user_project_rejects_other_user_project(
    db_session,
):
    owner = User(
        email="service-owner-2@example.com",
        password_hash=hash_password("test12345"),
    )

    other_user = User(
        email="service-other@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add_all([owner, other_user])
    await db_session.flush()

    project = Project(
        user_id=owner.id,
        name="Private Project",
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
async def test_calculate_project_summary(
    db_session,
):
    user = User(
        email="summary-service@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Summary Project",
        budget=Decimal("100000.00"),
        hourly_rate=Decimal("3000.00"),
    )

    db_session.add(project)
    await db_session.flush()

    time_entry = TimeEntry(
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
    )

    db_session.add(time_entry)
    await db_session.commit()

    summary = await calculate_project_summary(
        session=db_session,
        project=project,
    )

    assert summary["total_seconds"] == 5400
    assert summary["total_hours"] == Decimal("1.5")
    assert summary["total_cost"] == Decimal("4500.000")
    assert summary["remaining_budget"] == Decimal("95500.000")
    assert summary["budget_used_percent"] == Decimal("4.500")


@pytest.mark.asyncio
async def test_calculate_project_summary_without_time_entries(
    db_session,
):
    user = User(
        email="empty-summary-service@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Empty Project",
        budget=Decimal("100000.00"),
        hourly_rate=Decimal("3000.00"),
    )

    db_session.add(project)
    await db_session.commit()

    summary = await calculate_project_summary(
        session=db_session,
        project=project,
    )

    assert summary["total_seconds"] == 0
    assert summary["total_hours"] == Decimal("0")
    assert summary["total_cost"] == Decimal("0.000")
    assert summary["remaining_budget"] == Decimal("100000.000")
    assert summary["budget_used_percent"] == Decimal("0.000")


@pytest.mark.asyncio
async def test_calculate_dashboard(
    db_session,
):
    user = User(
        email="dashboard-service@example.com",
        password_hash=hash_password("test12345"),
    )

    db_session.add(user)
    await db_session.flush()

    active_project = Project(
        user_id=user.id,
        name="Active Project",
        budget=Decimal("100000.00"),
        hourly_rate=Decimal("3000.00"),
        status="active",
    )

    completed_project = Project(
        user_id=user.id,
        name="Completed Project",
        budget=Decimal("50000.00"),
        hourly_rate=Decimal("2000.00"),
        status="completed",
    )

    db_session.add_all([
        active_project,
        completed_project,
    ])

    await db_session.flush()

    db_session.add_all([
        TimeEntry(
            project_id=active_project.id,
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
            project_id=completed_project.id,
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

    dashboard = await calculate_dashboard(
        session=db_session,
        user=user,
    )

    assert dashboard["total_projects"] == 2
    assert dashboard["active_projects"] == 1
    assert dashboard["total_seconds"] == 9000
    assert dashboard["total_hours"] == Decimal("2.5")
    assert dashboard["total_budget"] == Decimal("150000.00")
    assert dashboard["total_cost"] == Decimal("6500.000")
    assert dashboard["budget_used_percent"] == (
        Decimal("4.333333333333333333333333333")
    )