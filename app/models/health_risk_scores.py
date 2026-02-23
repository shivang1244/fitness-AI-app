import uuid

from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class HealthRiskScore(Base):
    __tablename__ = "health_risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    longevity_score = Column(Float, nullable=True)
    metabolic_risk_score = Column(Float, nullable=True)
    cardiovascular_risk_score = Column(Float, nullable=True)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="health_risk_scores")
