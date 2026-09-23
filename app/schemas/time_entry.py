from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimeEntryCreate(BaseModel):
    task_id: int | None = None
    started_at: datetime
    ended_at: datetime | None = None


class TimeEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    task_id: int | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None


class TimerStart(BaseModel):
    task_id: int | None = None

class TimeCostResponse(BaseModel):
    total_seconds: int
    total_hours: float
    hourly_rate: float | None
    total_cost: float | None