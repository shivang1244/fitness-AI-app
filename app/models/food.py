from sqlalchemy import Column, String, Float, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Food(Base):
    __tablename__ = "foods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Info
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)

    # Macronutrients (per 100g)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    carbs_per_100g = Column(Float, nullable=False)
    fat_per_100g = Column(Float, nullable=False)
    fiber_per_100g = Column(Float, nullable=True)

    # Cost (for budget engine)
    cost_per_100g = Column(Float, nullable=True)

    # Diet classification
    diet_type = Column(String, nullable=False)
    # vegetarian / non_vegetarian / vegan / eggetarian / both

    # Meal category tagging
    meal_type = Column(String, nullable=False)
    # breakfast / lunch / dinner / snack

    # Allergen information
    allergens = Column(JSON, nullable=True)
    # Example: ["milk", "peanut"]

    # Medical safety flags
    high_sodium = Column(Boolean, default=False)
    high_sugar = Column(Boolean, default=False)
    pregnancy_safe = Column(Boolean, default=True)

    # Optional advanced nutrition
    glycemic_index = Column(Integer, nullable=True)

    # Active flag (for admin control)
    is_active = Column(Boolean, default=True)
