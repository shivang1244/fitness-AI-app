from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.core.dependencies import get_db, get_current_user
from app.models.goal_settings import GoalSettings
from app.models.users import User
from app.models.body_measurements import BodyMeasurement
from app.models.manual_activity import ManualActivity
from app.models.wearable_daily_stats import WearableDailyStat

from app.schemas.goal_settings import GoalCreateUpdate
from app.services.calorie_engine import CalorieEngine

router = APIRouter()


# =========================
# CREATE / UPDATE GOAL
# =========================
@router.post("/goal")
def create_or_update_goal(
    request: GoalCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_goals = (
        db.query(GoalSettings)
        .filter(
            GoalSettings.user_id == current_user.id,
            GoalSettings.is_active.is_(True),
        )
        .all()
    )

    for goal in existing_goals:
        goal.is_active = False

    new_goal = GoalSettings(
        user_id=current_user.id,
        goal_type=request.goal_type.value,
        goal_weight=request.goal_weight,
        target_date=request.target_date,
        intensity=request.intensity.value,
        auto_adjust=request.auto_adjust,
        is_active=True,
    )

    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)

    return {"message": "Goal created and activated successfully"}


# =========================
# GET ACTIVE GOAL
# =========================
@router.get("/goal")
def get_active_goal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = (
        db.query(GoalSettings)
        .filter(
            GoalSettings.user_id == current_user.id,
            GoalSettings.is_active.is_(True),
        )
        .first()
    )

    if not goal:
        raise HTTPException(status_code=404, detail="No active goal found")

    return goal


# =========================
# DAILY PLAN (AUTO WEARABLE HYBRID)
# =========================
@router.get("/goal/daily-plan")
def get_daily_plan(
    activity_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if not current_user.profile:
        raise HTTPException(status_code=400, detail="Profile required")

    latest_measurement = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == current_user.id)
        .order_by(BodyMeasurement.recorded_at.desc())
        .first()
    )

    if not latest_measurement:
        raise HTTPException(status_code=400, detail="Measurement required")

    active_goal = (
        db.query(GoalSettings)
        .filter(
            GoalSettings.user_id == current_user.id,
            GoalSettings.is_active.is_(True),
        )
        .first()
    )

    if not active_goal:
        raise HTTPException(status_code=400, detail="Active goal required")

    # -------------------------
    # 1️⃣ Calculate BMR
    # -------------------------
    bmr = CalorieEngine.calculate_bmr(
        profile=current_user.profile,
        measurement=latest_measurement,
    )

    query_date = activity_date or date.today()

    # -------------------------
    # 2️⃣ Fetch Wearable Stats
    # -------------------------
    wearable_stat = (
        db.query(WearableDailyStat)
        .filter(
            WearableDailyStat.user_id == current_user.id,
            WearableDailyStat.stat_date == query_date
        )
        .first()
    )

    # -------------------------
    # 3️⃣ Fetch Manual Activity
    # -------------------------
    manual_activities = (
        db.query(ManualActivity)
        .filter(
            ManualActivity.user_id == current_user.id,
            ManualActivity.activity_date == query_date,
        )
        .all()
    )

    manual_activity_calories = 0.0

    if manual_activities:
        manual_activity_calories = CalorieEngine.calculate_manual_activity_calories(
            activities=manual_activities,
            weight_kg=latest_measurement.weight_kg,
        )

    # -------------------------
    # 4️⃣ HYBRID TDEE PRIORITY
    # -------------------------

    if wearable_stat and wearable_stat.total_calories:
        tdee = wearable_stat.total_calories

    elif wearable_stat and wearable_stat.active_calories:
        tdee = bmr + wearable_stat.active_calories

    elif manual_activity_calories > 0:
        tdee = bmr + manual_activity_calories

    elif wearable_stat and wearable_stat.steps:
        tdee = CalorieEngine.calculate_tdee(
            bmr=bmr,
            weight_kg=latest_measurement.weight_kg,
            activity_level=latest_measurement.activity_level,
            steps=wearable_stat.steps,
        )

    else:
        tdee = CalorieEngine.calculate_tdee(
            bmr=bmr,
            weight_kg=latest_measurement.weight_kg,
            activity_level=latest_measurement.activity_level,
        )

    # -------------------------
    # 5️⃣ Hybrid Goal Calories
    # -------------------------
    hybrid_goal = CalorieEngine.calculate_hybrid_goal_calories(
        tdee=tdee,
        current_weight=latest_measurement.weight_kg,
        body_fat=latest_measurement.body_fat_percent,
        goal_weight=active_goal.goal_weight,
        goal_type=active_goal.goal_type,
        target_date=active_goal.target_date,
    )

    target_calories = hybrid_goal["calories"]

    # -------------------------
    # 6️⃣ Macro Calculation
    # -------------------------
    macros = CalorieEngine.calculate_macros(
        target_calories=target_calories,
        weight_kg=latest_measurement.weight_kg,
        goal_type=active_goal.goal_type,
    )

    return {
        "BMR": round(bmr, 2),
        "TDEE": round(tdee, 2),
        "manual_activity_calories": round(manual_activity_calories, 2),
        "wearable_detected": bool(wearable_stat),
        "target_calories": hybrid_goal,
        "macros": macros,
    }
