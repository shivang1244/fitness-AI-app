from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class WearableDailyStatCreateUpdate(BaseModel):
    stat_date: date

    total_calories: Optional[float] = None
    active_calories: Optional[float] = None
    steps: Optional[int] = None
    resting_heart_rate: Optional[int] = None
    sleep_hours: Optional[float] = None

    source: Optional[str] = None


class WearableDailyStatResponse(WearableDailyStatCreateUpdate):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
