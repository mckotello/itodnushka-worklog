from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.schemas.time_entry import (
    TimeCostResponse,
    TimeEntryCreate,
    TimeEntryResponse,
    TimerStart,
)
from app.services.project_access_service import get_user_project
from app.services.time_entry_service import (
    calculate_duration_seconds,
    calculate_time_cost,
    get_active_timer,
    get_active_user_timer,
    get_project_task,
    get_project_time_entries,
    get_user_time_entry,
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
    project = await get_user_project(
        session=session,
        project_id=project_id,
        user=current_user,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if entry_data.task_id is not None:
        task = await get_project_task(
            session=session,
            project_id=project_id,
            task_id=entry_data.task_id,
        )

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

    duration_seconds = None

    if entry_data.ended_at is not None:
        if entry_data.ended_at <= entry_data.started_at:
            raise HTTPException(
                status_code=400,
                detail="ended_at must be later than started_at",
            )

        duration_seconds = calculate_duration_seconds(
            started_at=entry_data.started_at,
            ended_at=entry_data.ended_at,
        )

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
    project = await get_user_project(
        session=session,
        project_id=project_id,
        user=current_user,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return await get_project_time_entries(
        session=session,
        project_id=project_id,
    )


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
    project = await get_user_project(
        session=session,
        project_id=project_id,
        user=current_user,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if timer_data.task_id is not None:
        task = await get_project_task(
            session=session,
            project_id=project_id,
            task_id=timer_data.task_id,
        )

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

    active_timer = await get_active_timer(
        session=session,
        project_id=project_id,
    )

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

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail="A timer is already running for this project",
        )

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
    time_entry = await get_active_user_timer(
        session=session,
        project_id=project_id,
        user=current_user,
    )

    if time_entry is None:
        raise HTTPException(
            status_code=404,
            detail="No active timer found",
        )

    ended_at = datetime.now(timezone.utc)

    time_entry.ended_at = ended_at
    time_entry.duration_seconds = calculate_duration_seconds(
        started_at=time_entry.started_at,
        ended_at=ended_at,
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
    project = await get_user_project(
        session=session,
        project_id=project_id,
        user=current_user,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    cost = await calculate_time_cost(
        session=session,
        project=project,
    )

    return TimeCostResponse(**cost)


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
    time_entry = await get_user_time_entry(
        session=session,
        project_id=project_id,
        time_entry_id=time_entry_id,
        user=current_user,
    )

    if time_entry is None:
        raise HTTPException(
            status_code=404,
            detail="Time entry not found",
        )

    await session.delete(time_entry)
    await session.commit()