from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class HealthRecordBase(BaseModel):
    has_diabetes: Optional[bool] = None
    has_bp: Optional[bool] = None
    has_heart_conditions: Optional[bool] = None
    is_pregnant: Optional[bool] = None

    medications: Optional[List[str]] = None
    injuries: Optional[List[str]] = None

    manual_medical_notes: Optional[str] = None
    resting_heart_rate: Optional[int] = None


class HealthRecordCreateUpdate(HealthRecordBase):
    pass


class HealthRecordResponse(HealthRecordBase):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
