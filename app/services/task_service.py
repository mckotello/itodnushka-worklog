from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.models.user import User


async def get_user_project(
    session: AsyncSession,
    project_id: int,
    user: User,
) -> Project | None:
    result = await session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    return result.scalar_one_or_none()


async def get_project_tasks(
    session: AsyncSession,
    project_id: int,
) -> list[Task]:
    result = await session.execute(
        select(Task).where(
            Task.project_id == project_id,
        )
    )

    return list(result.scalars().all())


async def get_user_task(
    session: AsyncSession,
    project_id: int,
    task_id: int,
    user: User,
) -> Task | None:
    result = await session.execute(
        select(Task)
        .join(Project)
        .where(
            Task.id == task_id,
            Task.project_id == project_id,
            Project.user_id == user.id,
        )
    )

    return result.scalar_one_or_none()