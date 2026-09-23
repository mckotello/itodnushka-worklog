from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


TaskStatus = Literal[
    "todo",
    "in_progress",
    "done",
]


class TaskCreate(BaseModel):
    name: str
    status: TaskStatus = "todo"

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Task name cannot be empty")

        if len(value) > 255:
            raise ValueError("Task name must be 255 characters or less")

        return value


class TaskUpdate(BaseModel):
    name: str | None = None
    status: TaskStatus | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Task name cannot be empty")

        if len(value) > 255:
            raise ValueError("Task name must be 255 characters or less")

        return value


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    status: str
    created_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    limit: int
    pages: int