import uuid
from datetime import datetime
from sqlalchemy import String

from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Core Metrics
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    body_fat_percent = Column(Float, nullable=True)
    from sqlalchemy import String

    activity_level = Column(String, nullable=True)

    # Full Body Measurements (All Optional)
    chest_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hip_cm = Column(Float, nullable=True)
    neck_cm = Column(Float, nullable=True)
    left_arm_cm = Column(Float, nullable=True)
    right_arm_cm = Column(Float, nullable=True)
    left_thigh_cm = Column(Float, nullable=True)
    right_thigh_cm = Column(Float, nullable=True)
    calf_cm = Column(Float, nullable=True)

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", backref="body_measurements")
