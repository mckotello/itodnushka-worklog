from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.services.project_access_service import get_user_project


async def get_project_task(
    session: AsyncSession,
    project_id: int,
    task_id: int,
) -> Task | None:
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
        )
    )

    return result.scalar_one_or_none()


def calculate_duration_seconds(
    started_at: datetime,
    ended_at: datetime,
) -> int:
    return int(
        (ended_at - started_at).total_seconds()
    )


async def get_active_timer(
    session: AsyncSession,
    project_id: int,
) -> TimeEntry | None:
    result = await session.execute(
        select(TimeEntry).where(
            TimeEntry.project_id == project_id,
            TimeEntry.ended_at.is_(None),
        )
    )

    return result.scalar_one_or_none()


async def get_active_user_timer(
    session: AsyncSession,
    project_id: int,
    user: User,
) -> TimeEntry | None:
    result = await session.execute(
        select(TimeEntry)
        .join(Project)
        .where(
            TimeEntry.project_id == project_id,
            TimeEntry.ended_at.is_(None),
            Project.user_id == user.id,
        )
    )

    return result.scalar_one_or_none()


async def get_project_time_entries(
    session: AsyncSession,
    project_id: int,
    page: int,
    limit: int,
) -> tuple[list[TimeEntry], int]:
    count_result = await session.execute(
        select(func.count(TimeEntry.id))
        .where(
            TimeEntry.project_id == project_id,
        )
    )

    total = count_result.scalar_one()

    offset = (page - 1) * limit

    result = await session.execute(
        select(TimeEntry)
        .where(
            TimeEntry.project_id == project_id,
        )
        .order_by(TimeEntry.started_at.desc())
        .offset(offset)
        .limit(limit)
    )

    time_entries = list(result.scalars().all())

    return time_entries, total


async def get_user_time_entry(
    session: AsyncSession,
    project_id: int,
    time_entry_id: int,
    user: User,
) -> TimeEntry | None:
    result = await session.execute(
        select(TimeEntry)
        .join(Project)
        .where(
            TimeEntry.id == time_entry_id,
            TimeEntry.project_id == project_id,
            Project.user_id == user.id,
        )
    )

    return result.scalar_one_or_none()


async def calculate_time_cost(
    session: AsyncSession,
    project: Project,
) -> dict:
    result = await session.execute(
        select(TimeEntry).where(
            TimeEntry.project_id == project.id,
            TimeEntry.ended_at.is_not(None),
        )
    )

    time_entries = result.scalars().all()

    total_seconds = sum(
        entry.duration_seconds or 0
        for entry in time_entries
    )

    total_hours = total_seconds / 3600

    total_cost = None

    if project.hourly_rate is not None:
        total_cost = (
            Decimal(total_seconds)
            / Decimal(3600)
            * project.hourly_rate
        )

    return {
        "total_seconds": total_seconds,
        "total_hours": total_hours,
        "hourly_rate": project.hourly_rate,
        "total_cost": total_cost,
    }