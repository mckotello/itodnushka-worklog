from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.models.user import User


async def get_project_tasks(
    session: AsyncSession,
    project_id: int,
    page: int,
    limit: int,
) -> tuple[list[Task], int]:
    count_result = await session.execute(
        select(func.count(Task.id))
        .where(
            Task.project_id == project_id,
        )
    )

    total = count_result.scalar_one()

    offset = (page - 1) * limit

    result = await session.execute(
        select(Task)
        .where(
            Task.project_id == project_id,
        )
        .order_by(Task.id.desc())
        .offset(offset)
        .limit(limit)
    )

    tasks = list(result.scalars().all())

    return tasks, total


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