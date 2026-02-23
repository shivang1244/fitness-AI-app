from sqlalchemy import Column, String, Float, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class ManualActivity(Base):
    __tablename__ = "manual_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    activity_type = Column(String, nullable=False)  # gym, running, yoga, etc
    met_value = Column(Float, nullable=False)       # MET score
    duration_minutes = Column(Integer, nullable=False)

    activity_date = Column(Date, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="manual_activities")
