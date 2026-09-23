from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProjectStatus = Literal[
    "active",
    "completed",
    "archived",
]


class ProjectCreate(BaseModel):
    name: str
    client_name: str | None = None
    budget: Decimal | None = Field(default=None, ge=0)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    status: ProjectStatus = "active"
    deadline: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Project name cannot be empty")

        if len(value) > 255:
            raise ValueError("Project name must be 255 characters or less")

        return value


class ProjectUpdate(BaseModel):
    name: str | None = None
    client_name: str | None = None
    budget: Decimal | None = Field(default=None, ge=0)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    status: ProjectStatus | None = None
    deadline: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Project name cannot be empty")

        if len(value) > 255:
            raise ValueError("Project name must be 255 characters or less")

        return value


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    client_name: str | None
    budget: Decimal | None
    hourly_rate: Decimal | None
    status: str
    created_at: datetime
    deadline: date | None


class ProjectSummaryResponse(BaseModel):
    project_id: int
    budget: Decimal | None
    hourly_rate: Decimal | None
    total_seconds: int
    total_hours: Decimal
    total_cost: Decimal | None
    remaining_budget: Decimal | None
    budget_used_percent: Decimal | None


class DashboardResponse(BaseModel):
    total_projects: int
    active_projects: int
    total_seconds: int
    total_hours: Decimal
    total_budget: Decimal
    total_cost: Decimal
    budget_used_percent: Decimal | None