from sqlalchemy import Column, Boolean, Integer, ForeignKey, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    # Medical Conditions (All Optional)
    has_diabetes = Column(Boolean, nullable=True)
    has_bp = Column(Boolean, nullable=True)
    has_heart_conditions = Column(Boolean, nullable=True)
    is_pregnant = Column(Boolean, nullable=True)

    # Structured Medical Data
    medications = Column(JSON, nullable=True)
    injuries = Column(JSON, nullable=True)

    # Additional Medical Notes (AI will analyze this later)
    manual_medical_notes = Column(String, nullable=True)

    # Cardio / Recovery Data
    resting_heart_rate = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="health_record")
