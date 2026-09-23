from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.schemas.project import (
    DashboardResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectSummaryResponse,
    ProjectUpdate,
)


router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=201,
)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    project = Project(
        user_id=current_user.id,
        **project_data.model_dump(),
    )

    session.add(project)

    await session.commit()
    await session.refresh(project)

    return project


@router.get("/", response_model=list[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Project).where(Project.user_id == current_user.id)
    )

    return result.scalars().all()
@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Project).where(
            Project.user_id == current_user.id,
        )
    )

    projects = result.scalars().all()

    total_projects = len(projects)

    active_projects = sum(
        1
        for project in projects
        if project.status == "active"
    )

    total_budget = sum(
        (
            project.budget
            for project in projects
            if project.budget is not None
        ),
        Decimal(0),
    )

    project_ids = [project.id for project in projects]

    total_seconds = 0
    total_cost = Decimal(0)

    if project_ids:
        result = await session.execute(
            select(TimeEntry).where(
                TimeEntry.project_id.in_(project_ids),
                TimeEntry.ended_at.is_not(None),
            )
        )

        time_entries = result.scalars().all()

        project_rates = {
            project.id: project.hourly_rate
            for project in projects
        }

        for entry in time_entries:
            duration = entry.duration_seconds or 0
            total_seconds += duration

            hourly_rate = project_rates.get(entry.project_id)

            if hourly_rate is not None:
                total_cost += (
                    Decimal(duration)
                    / Decimal(3600)
                    * hourly_rate
                )

    total_hours = (
        Decimal(total_seconds) / Decimal(3600)
    )

    budget_used_percent = None

    if total_budget > 0:
        budget_used_percent = (
            total_cost
            / total_budget
            * Decimal(100)
        )

    return DashboardResponse(
        total_projects=total_projects,
        active_projects=active_projects,
        total_seconds=total_seconds,
        total_hours=total_hours,
        total_budget=total_budget,
        total_cost=total_cost,
        budget_used_percent=budget_used_percent,
    )
@router.get(
    "/{project_id}/summary",
    response_model=ProjectSummaryResponse,
)
async def get_project_summary(
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

    total_hours = (
        Decimal(total_seconds) / Decimal(3600)
    )

    total_cost = None
    remaining_budget = None
    budget_used_percent = None

    if project.hourly_rate is not None:
        total_cost = (
            total_hours * project.hourly_rate
        )

    if (
        project.budget is not None
        and total_cost is not None
    ):
        remaining_budget = (
            project.budget - total_cost
        )

        if project.budget > 0:
            budget_used_percent = (
                total_cost
                / project.budget
                * Decimal(100)
            )

    return ProjectSummaryResponse(
        project_id=project.id,
        budget=project.budget,
        hourly_rate=project.hourly_rate,
        total_seconds=total_seconds,
        total_hours=total_hours,
        total_cost=total_cost,
        remaining_budget=remaining_budget,
        budget_used_percent=budget_used_percent,
    )
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
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

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
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

    update_data = project_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(project, field, value)

    await session.commit()
    await session.refresh(project)

    return project
@router.delete("/{project_id}", status_code=204)
async def delete_project(
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

    await session.delete(project)
    await session.commit()