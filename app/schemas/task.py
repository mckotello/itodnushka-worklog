from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    name: str
    status: str = "todo"


class TaskUpdate(BaseModel):
    name: str | None = None
    status: str | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    status: str
    created_at: datetime