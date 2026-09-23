from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.project_access_service import get_user_project
from app.services.task_service import (
    get_project_tasks,
    get_user_task,
)


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
    response_model=TaskListResponse,
)
async def get_tasks(
    project_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
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

    tasks, total = await get_project_tasks(
        session=session,
        project_id=project_id,
        page=page,
        limit=limit,
    )

    pages = (total + limit - 1) // limit if total > 0 else 0

    return TaskListResponse(
        items=tasks,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


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
    task = await get_user_task(
        session=session,
        project_id=project_id,
        task_id=task_id,
        user=current_user,
    )

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
    task = await get_user_task(
        session=session,
        project_id=project_id,
        task_id=task_id,
        user=current_user,
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    await session.delete(task)
    await session.commit()