import uuid
from datetime import datetime

from sqlalchemy import Column, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class BehaviorEngagement(Base):
    __tablename__ = "behavior_engagement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    onboarding_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    weekly_completion_rate = Column(Float, nullable=True)

    app_open_frequency = Column(Integer, nullable=True)
    last_active_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="behavior_engagement")
