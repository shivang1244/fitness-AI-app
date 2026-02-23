from pydantic import BaseModel
from typing import Optional
from datetime import date
from enum import Enum


class GoalTypeEnum(str, Enum):
    fat_loss = "fat_loss"
    muscle_gain = "muscle_gain"
    maintain = "maintain"
    yoga = "yoga"
    calisthenics = "calisthenics"


class IntensityEnum(str, Enum):
    slow = "slow"
    moderate = "moderate"
    aggressive = "aggressive"


class GoalCreateUpdate(BaseModel):
    goal_type: GoalTypeEnum
    goal_weight: Optional[float] = None
    target_date: Optional[date] = None
    intensity: IntensityEnum = IntensityEnum.moderate
    auto_adjust: bool = True
