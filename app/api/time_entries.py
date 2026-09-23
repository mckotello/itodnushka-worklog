from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.schemas.time_entry import TimeEntryCreate, TimeEntryResponse
from app.schemas.time_entry import (
    TimeCostResponse,
    TimeEntryCreate,
    TimeEntryResponse,
    TimerStart,
)

router = APIRouter(
    prefix="/projects/{project_id}/time-entries",
    tags=["time entries"],
)


@router.post(
    "/",
    response_model=TimeEntryResponse,
    status_code=201,
)
async def create_time_entry(
    project_id: int,
    entry_data: TimeEntryCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )

    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if entry_data.task_id is not None:
        result = await session.execute(
            select(Task).where(
                Task.id == entry_data.task_id,
                Task.project_id == project_id,
            )
        )

        task = result.scalar_one_or_none()

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

    if entry_data.ended_at is not None:
        if entry_data.ended_at <= entry_data.started_at:
            raise HTTPException(
                status_code=400,
                detail="ended_at must be later than started_at",
            )

        duration_seconds = int(
            (
                entry_data.ended_at - entry_data.started_at
            ).total_seconds()
        )
    else:
        duration_seconds = None

    time_entry = TimeEntry(
        project_id=project_id,
        task_id=entry_data.task_id,
        started_at=entry_data.started_at,
        ended_at=entry_data.ended_at,
        duration_seconds=duration_seconds,
    )
    session.add(time_entry)

    await session.commit()
    await session.refresh(time_entry)

    return time_entry
@router.get(
    "/",
    response_model=list[TimeEntryResponse],
)
async def get_time_entries(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )

    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    result = await session.execute(
        select(TimeEntry)
        .where(TimeEntry.project_id == project_id)
        .order_by(TimeEntry.started_at.desc())
    )

    return result.scalars().all()
@router.post(
    "/start",
    response_model=TimeEntryResponse,
    status_code=201,
)
async def start_timer(
    project_id: int,
    timer_data: TimerStart,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )

    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if timer_data.task_id is not None:
        result = await session.execute(
            select(Task).where(
                Task.id == timer_data.task_id,
                Task.project_id == project_id,
            )
        )

        task = result.scalar_one_or_none()

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

    result = await session.execute(
        select(TimeEntry).where(
            TimeEntry.project_id == project_id,
            TimeEntry.ended_at.is_(None),
        )
    )

    active_timer = result.scalar_one_or_none()

    if active_timer is not None:
        raise HTTPException(
            status_code=409,
            detail="A timer is already running for this project",
        )

    time_entry = TimeEntry(
        project_id=project_id,
        task_id=timer_data.task_id,
        started_at=datetime.now(timezone.utc),
    )

    session.add(time_entry)

    await session.commit()
    await session.refresh(time_entry)

    return time_entry
@router.post(
    "/stop",
    response_model=TimeEntryResponse,
)
async def stop_timer(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(TimeEntry)
        .join(Project)
        .where(
            TimeEntry.project_id == project_id,
            TimeEntry.ended_at.is_(None),
            Project.user_id == current_user.id,
        )
    )

    time_entry = result.scalar_one_or_none()

    if time_entry is None:
        raise HTTPException(
            status_code=404,
            detail="No active timer found",
        )

    ended_at = datetime.now(timezone.utc)

    time_entry.ended_at = ended_at
    time_entry.duration_seconds = int(
        (ended_at - time_entry.started_at).total_seconds()
    )

    await session.commit()
    await session.refresh(time_entry)

    return time_entry
@router.get(
    "/cost",
    response_model=TimeCostResponse,
)
async def get_time_cost(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )

    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    result = await session.execute(
        select(TimeEntry).where(
            TimeEntry.project_id == project_id,
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

    return TimeCostResponse(
        total_seconds=total_seconds,
        total_hours=total_hours,
        hourly_rate=project.hourly_rate,
        total_cost=total_cost,
    )
@router.delete(
    "/{time_entry_id}",
    status_code=204,
)
async def delete_time_entry(
    project_id: int,
    time_entry_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(TimeEntry)
        .join(Project)
        .where(
            TimeEntry.id == time_entry_id,
            TimeEntry.project_id == project_id,
            Project.user_id == current_user.id,
        )
    )

    time_entry = result.scalar_one_or_none()

    if time_entry is None:
        raise HTTPException(
            status_code=404,
            detail="Time entry not found",
        )

    await session.delete(time_entry)
    await session.commit()