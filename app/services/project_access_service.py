from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
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