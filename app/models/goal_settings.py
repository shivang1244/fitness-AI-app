from sqlalchemy import Column, String, Date, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class GoalSettings(Base):
    __tablename__ = "goal_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    goal_type = Column(String, nullable=False)
    goal_weight = Column(Float, nullable=True)
    target_date = Column(Date, nullable=True)

    intensity = Column(String, nullable=False, default="moderate")
    auto_adjust = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="goals")
