from datetime import date
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class TimezoneEnum(str, Enum):
    asia_kolkata = "Asia/Kolkata"
    utc = "UTC"
    europe_london = "Europe/London"

class UnitSystemEnum(str, Enum):
    metric = "metric"
    imperial = "imperial"


class UserProfileCreateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    country: Optional[str] = None
    timezone: Optional[TimezoneEnum] = None
    preferred_unit_system: Optional[UnitSystemEnum] = "metric"

    model_config = {
        "from_attributes": True
    }
