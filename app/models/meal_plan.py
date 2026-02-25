from sqlalchemy import Column, String, Float, Date, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


# =========================
# DAILY MEAL PLAN
# =========================
class DailyMealPlan(Base):
    __tablename__ = "daily_meal_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    plan_date = Column(Date, nullable=False)

    # Target macros (from calorie engine)
    target_calories = Column(Float, nullable=False)
    target_protein = Column(Float, nullable=False)
    target_carbs = Column(Float, nullable=False)
    target_fat = Column(Float, nullable=False)

    # Generated totals (from AI plan)
    generated_total_calories = Column(Float, nullable=True)
    generated_total_protein = Column(Float, nullable=True)
    generated_total_carbs = Column(Float, nullable=True)
    generated_total_fat = Column(Float, nullable=True)

    # Budget (optional)
    daily_budget = Column(Float, nullable=True)

    # Plan status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    is_regenerated = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    meals = relationship("Meal", back_populates="meal_plan")


# =========================
# MEAL (Breakfast / Lunch / etc.)
# =========================
class Meal(Base):
    __tablename__ = "meals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    meal_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("daily_meal_plans.id"),
        nullable=False
    )

    meal_name = Column(String, nullable=False)
    meal_type = Column(String, nullable=False)
    # breakfast / lunch / dinner / snack

    # Primary or alternative
    is_primary = Column(Boolean, default=True)

    # Macro totals for the meal
    total_calories = Column(Float, nullable=False)
    total_protein = Column(Float, nullable=False)
    total_carbs = Column(Float, nullable=False)
    total_fat = Column(Float, nullable=False)

    estimated_cost = Column(Float, nullable=True)

    meal_plan = relationship("DailyMealPlan", back_populates="meals")
    ingredients = relationship("MealIngredient", back_populates="meal")


# =========================
# MEAL INGREDIENTS
# =========================
class MealIngredient(Base):
    __tablename__ = "meal_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    meal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meals.id"),
        nullable=False
    )

    ingredient_name = Column(String, nullable=False)
    quantity_grams = Column(Float, nullable=False)

    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)

    cost = Column(Float, nullable=True)

    meal = relationship("Meal", back_populates="ingredients")
