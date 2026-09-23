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
from app.services.project_service import (
    calculate_dashboard,
    calculate_project_summary,
    get_user_project,
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
    dashboard = await calculate_dashboard(
        session=session,
        user=current_user,
    )

    return DashboardResponse(**dashboard)


@router.get(
    "/{project_id}/summary",
    response_model=ProjectSummaryResponse,
)
async def get_project_summary(
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

    summary = await calculate_project_summary(
        session=session,
        project=project,
    )

    return ProjectSummaryResponse(**summary)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
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

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
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

    await session.delete(project)
    await session.commit()