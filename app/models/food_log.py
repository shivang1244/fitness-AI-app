from sqlalchemy import Column, Float, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class FoodLog(Base):
    __tablename__ = "food_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    # Optional link to meal plan
    meal_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("daily_meal_plans.id"),
        nullable=True
    )

    # Optional link to suggested meal
    meal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meals.id"),
        nullable=True
    )

    # If user logs custom meal
    custom_meal_name = Column(String, nullable=True)

    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)

    log_date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="food_logs")
    meal_plan = relationship("DailyMealPlan", backref="food_logs")
    meal = relationship("Meal", backref="food_logs")
