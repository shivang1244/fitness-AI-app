from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.models.users import User
from app.models.food_log import FoodLog
from app.models.meal_plan import DailyMealPlan, Meal
from app.services.food_search_engine import FoodSearchEngine

router = APIRouter()


# Temporary GPT wrapper (connect real GPT later)
def gpt_client(prompt: str):
    raise NotImplementedError("Connect GPT API here.")


# =====================================================
# 1️⃣ LOG SUGGESTED MEAL
# =====================================================
@router.post("/food/log/suggested")
def log_suggested_meal(
    meal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    meal = db.query(Meal).filter(Meal.id == meal_id).first()

    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    food_log = FoodLog(
        user_id=current_user.id,
        meal_plan_id=meal.meal_plan_id,
        meal_id=meal.id,
        calories=meal.total_calories,
        protein=meal.total_protein,
        carbs=meal.total_carbs,
        fat=meal.total_fat,
        log_date=date.today()
    )

    db.add(food_log)
    db.commit()

    return {"message": "Meal logged successfully"}


# =====================================================
# 2️⃣ LOG CUSTOM MEAL
# =====================================================
@router.post("/food/log/custom")
def log_custom_meal(
    food_name: str,
    grams: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    engine = FoodSearchEngine()

    try:
        result = engine.search_food(
            food_name=food_name,
            grams=grams,
            gpt_client=gpt_client
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    food_log = FoodLog(
        user_id=current_user.id,
        custom_meal_name=food_name,
        calories=result.get("calories", 0),
        protein=result.get("protein", 0),
        carbs=result.get("carbs", 0),
        fat=result.get("fat", 0),
        log_date=date.today()
    )

    db.add(food_log)
    db.commit()

    return {
        "message": "Custom meal logged",
        "nutrition": result
    }


# =====================================================
# 3️⃣ DAILY SUMMARY + COMPLIANCE
# =====================================================
@router.get("/food/log/summary")
def daily_summary(
    selected_date: date = Query(default=date.today()),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    logs = (
        db.query(FoodLog)
        .filter(
            FoodLog.user_id == current_user.id,
            FoodLog.log_date == selected_date
        )
        .all()
    )

    if not logs:
        return {
            "date": selected_date,
            "total_calories": 0,
            "total_protein": 0,
            "total_carbs": 0,
            "total_fat": 0,
            "compliance": None
        }

    total_calories = sum(log.calories for log in logs)
    total_protein = sum(log.protein for log in logs)
    total_carbs = sum(log.carbs for log in logs)
    total_fat = sum(log.fat for log in logs)

    # Fetch target from latest meal plan
    latest_plan = (
        db.query(DailyMealPlan)
        .filter(DailyMealPlan.user_id == current_user.id)
        .order_by(DailyMealPlan.plan_date.desc())
        .first()
    )

    compliance = None

    if latest_plan:
        compliance = {
            "calorie_compliance_percent": round(
                (total_calories / latest_plan.target_calories) * 100, 2
            ) if latest_plan.target_calories else 0,
            "protein_compliance_percent": round(
                (total_protein / latest_plan.target_protein) * 100, 2
            ) if latest_plan.target_protein else 0,
        }

    return {
        "date": selected_date,
        "total_calories": total_calories,
        "total_protein": total_protein,
        "total_carbs": total_carbs,
        "total_fat": total_fat,
        "compliance": compliance
    }


# =====================================================
# 4️⃣ DELETE LOG
# =====================================================
@router.delete("/food/log/{log_id}")
def delete_food_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    log = (
        db.query(FoodLog)
        .filter(
            FoodLog.id == log_id,
            FoodLog.user_id == current_user.id
        )
        .first()
    )

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    db.delete(log)
    db.commit()

    return {"message": "Log deleted successfully"}
