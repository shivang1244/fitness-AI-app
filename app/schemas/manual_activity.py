from pydantic import BaseModel
from typing import Optional
from datetime import date
from enum import Enum
from uuid import UUID
from datetime import date, datetime

class PredefinedActivityEnum(str, Enum):
    walking_slow = "walking_slow"
    walking_brisk = "walking_brisk"
    running = "running"
    gym_moderate = "gym_moderate"
    hiit = "hiit"
    cycling = "cycling"
    yoga = "yoga"
    swimming = "swimming"
    custom = "custom"


# Predefined MET values
PREDEFINED_MET_MAP = {
    "walking_slow": 3.0,
    "walking_brisk": 4.0,
    "running": 9.0,
    "gym_moderate": 6.0,
    "hiit": 10.0,
    "cycling": 7.0,
    "yoga": 3.0,
    "swimming": 8.0,
}


class ManualActivityCreate(BaseModel):
    activity_type: PredefinedActivityEnum
    duration_minutes: int
    activity_date: date
    custom_met_value: Optional[float] = None


class ManualActivityResponse(BaseModel):
    id: UUID
    user_id: UUID
    activity_type: str
    met_value: float
    duration_minutes: int
    activity_date: date
    created_at: datetime

    class Config:
        from_attributes = True
