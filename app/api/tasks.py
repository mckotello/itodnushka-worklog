from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate


router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
)


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=201,
)
async def create_task(
    project_id: int,
    task_data: TaskCreate,
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

    task = Task(
        project_id=project.id,
        **task_data.model_dump(),
    )

    session.add(task)

    await session.commit()
    await session.refresh(task)

    return task


@router.get(
    "/",
    response_model=list[TaskResponse],
)
async def get_tasks(
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
        select(Task).where(Task.project_id == project_id)
    )

    return result.scalars().all()


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
)
async def update_task(
    project_id: int,
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Task)
        .join(Project)
        .where(
            Task.id == task_id,
            Task.project_id == project_id,
            Project.user_id == current_user.id,
        )
    )

    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    update_data = task_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

    await session.commit()
    await session.refresh(task)

    return task

@router.delete(
    "/{task_id}",
    status_code=204,
)
async def delete_task(
    project_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Task)
        .join(Project)
        .where(
            Task.id == task_id,
            Task.project_id == project_id,
            Project.user_id == current_user.id,
        )
    )

    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    await session.delete(task)
    await session.commit()