from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.time_entry import TimeEntry
from app.models.user import User


async def calculate_project_summary(
    session: AsyncSession,
    project: Project,
) -> dict:
    result = await session.execute(
        select(
            func.coalesce(
                func.sum(TimeEntry.duration_seconds),
                0,
            )
        ).where(
            TimeEntry.project_id == project.id,
            TimeEntry.duration_seconds.is_not(None),
        )
    )

    total_seconds = result.scalar_one()

    total_hours = Decimal(total_seconds) / Decimal(3600)

    total_cost = None

    if project.hourly_rate is not None:
        total_cost = total_hours * project.hourly_rate

    remaining_budget = None

    if project.budget is not None and total_cost is not None:
        remaining_budget = project.budget - total_cost

    budget_used_percent = None

    if (
        project.budget is not None
        and project.budget > 0
        and total_cost is not None
    ):
        budget_used_percent = (
            total_cost / project.budget * Decimal(100)
        )

    return {
        "project_id": project.id,
        "budget": project.budget,
        "hourly_rate": project.hourly_rate,
        "total_seconds": total_seconds,
        "total_hours": total_hours,
        "total_cost": total_cost,
        "remaining_budget": remaining_budget,
        "budget_used_percent": budget_used_percent,
    }


async def calculate_dashboard(
    session: AsyncSession,
    user: User,
) -> dict:
    result = await session.execute(
        select(Project).where(
            Project.user_id == user.id,
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

    total_hours = Decimal(total_seconds) / Decimal(3600)

    budget_used_percent = None

    if total_budget > 0:
        budget_used_percent = (
            total_cost
            / total_budget
            * Decimal(100)
        )

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_seconds": total_seconds,
        "total_hours": total_hours,
        "total_budget": total_budget,
        "total_cost": total_cost,
        "budget_used_percent": budget_used_percent,
    }