import uuid

from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ProductivityScore(Base):
    __tablename__ = "productivity_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    productivity_score = Column(Float, nullable=True)
    cognitive_efficiency_score = Column(Float, nullable=True)
    energy_stability_score = Column(Float, nullable=True)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="productivity_scores")
