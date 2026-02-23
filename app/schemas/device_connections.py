from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class DeviceConnectionBase(BaseModel):
    wearable_type: Optional[str] = None
    wearable_id: Optional[str] = None
    wearable_sync_enabled: Optional[bool] = False


class DeviceConnectionCreateUpdate(DeviceConnectionBase):
    pass


class DeviceConnectionResponse(DeviceConnectionBase):
    id: UUID
    user_id: UUID
    last_synced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
