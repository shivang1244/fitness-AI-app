from sqlalchemy import Column, Float, Integer, Date, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy import UniqueConstraint

from app.core.database import Base


class WearableDailyStat(Base):
    __tablename__ = "wearable_daily_stats"

    __table_args__ = (
        UniqueConstraint("user_id", "stat_date", name="unique_user_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    stat_date = Column(Date, nullable=False)

    total_calories = Column(Float, nullable=True)
    active_calories = Column(Float, nullable=True)
    steps = Column(Integer, nullable=True)
    resting_heart_rate = Column(Integer, nullable=True)
    sleep_hours = Column(Float, nullable=True)

    source = Column(String, nullable=True)  # apple / fitbit / garmin / samsung

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="wearable_stats")
