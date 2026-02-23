from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class DeviceConnection(Base):
    __tablename__ = "device_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,  # 1 device per user for now
        nullable=False
    )

    wearable_type = Column(String, nullable=True)  # apple, fitbit, garmin, samsung
    wearable_id = Column(String, nullable=True)    # external account/device id
    wearable_sync_enabled = Column(Boolean, default=False)

    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="device_connection")
