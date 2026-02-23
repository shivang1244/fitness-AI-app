from sqlalchemy import Column, String, Time, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class LifestylePreference(Base):
    __tablename__ = "lifestyle_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    sleep_preference = Column(String, nullable=True)
    work_start = Column(Time, nullable=True)
    work_end = Column(Time, nullable=True)
    preferred_workout_time = Column(String, nullable=True)
    water_goal_liters = Column(Float, nullable=True)
    diet_preference = Column(String, nullable=True)
    food_allergies = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="lifestyle")
