from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ActivityLevelEnum(str, Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    high = "high"
class UnitSystemEnum(str, Enum):
    metric = "metric"      # cm, kg
    imperial = "imperial"  # inches, pounds



class BodyMeasurementCreate(BaseModel):
    unit_system: Optional[UnitSystemEnum] = None


    height_cm: float
    weight_kg: float
    activity_level: ActivityLevelEnum

    neck_cm: float
    waist_cm: float
    hip_cm: Optional[float] = None

    chest_cm: Optional[float] = None
    left_arm_cm: Optional[float] = None
    right_arm_cm: Optional[float] = None
    left_thigh_cm: Optional[float] = None
    right_thigh_cm: Optional[float] = None
    calf_cm: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
class BodyMeasurementUpdate(BaseModel):
    unit_system: Optional[UnitSystemEnum] = None

    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[ActivityLevelEnum] = None

    neck_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None

    chest_cm: Optional[float] = None
    left_arm_cm: Optional[float] = None
    right_arm_cm: Optional[float] = None
    left_thigh_cm: Optional[float] = None
    right_thigh_cm: Optional[float] = None
    calf_cm: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
