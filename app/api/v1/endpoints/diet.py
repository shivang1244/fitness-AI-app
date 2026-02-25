from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.users import User
from app.models.goal_settings import GoalSettings
from app.models.body_measurements import BodyMeasurement
from app.models.health_records import HealthRecord
from app.models.lifestyle_preferences import LifestylePreference

from app.services.diet_engine import DietEngine
from app.services.calorie_engine import CalorieEngine
from app.services.progress_engine import ProgressEngine
from app.services.compliance_engine import ComplianceEngine

router = APIRouter()


# =====================================================
# GPT WRAPPER (Replace with real GPT integration)
# =====================================================
def gpt_client(prompt: str):
    raise NotImplementedError("Connect GPT API here.")


# =====================================================
# BUILD USER CONTEXT
# =====================================================
def build_user_context(db: Session, user_id):

    goal = (
        db.query(GoalSettings)
        .filter(
            GoalSettings.user_id == user_id,
            GoalSettings.is_active.is_(True)
        )
        .first()
    )

    measurement = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user_id)
        .order_by(BodyMeasurement.recorded_at.desc())
        .first()
    )

    health = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .first()
    )

    lifestyle = (
        db.query(LifestylePreference)
        .filter(LifestylePreference.user_id == user_id)
        .first()
    )

    if not goal or not measurement:
        raise HTTPException(
            status_code=400,
            detail="Goal and measurement required before generating diet."
        )

    return {
        "goal_type": goal.goal_type,
        "goal_weight": goal.goal_weight,
        "target_date": goal.target_date,

        "diet_type": lifestyle.diet_preference if lifestyle else None,
        "allergies": lifestyle.any_food_allergies if lifestyle else [],

        "medical_conditions": {
            "has_diabetes": health.has_diabetes if health else False,
            "has_bp": health.has_bp if health else False,
            "has_heart_conditions": health.has_heart_conditions if health else False,
            "is_pregnant": health.is_pregnant if health else False,
        }
    }


# =====================================================
# CALCULATE TARGET MACROS (INTELLIGENT VERSION)
# =====================================================
def calculate_target_macros(db: Session, user_id):

    goal = (
        db.query(GoalSettings)
        .filter(
            GoalSettings.user_id == user_id,
            GoalSettings.is_active.is_(True)
        )
        .first()
    )

    measurement = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user_id)
        .order_by(BodyMeasurement.recorded_at.desc())
        .first()
    )

    if not goal or not measurement:
        raise HTTPException(
            status_code=400,
            detail="Goal and measurement required."
        )

    calorie_engine = CalorieEngine()

    # 1️⃣ BMR
    bmr = calorie_engine.calculate_bmr(
        profile=measurement.user.profile,
        measurement=measurement
    )

    # 2️⃣ TDEE
    tdee = calorie_engine.calculate_tdee(
        bmr=bmr,
        weight_kg=measurement.weight_kg,
        activity_level=measurement.activity_level
    )

    # 3️⃣ Hybrid Goal Calories
    hybrid_goal = calorie_engine.calculate_hybrid_goal_calories(
        tdee=tdee,
        current_weight=measurement.weight_kg,
        body_fat=measurement.body_fat_percent,
        goal_weight=goal.goal_weight,
        goal_type=goal.goal_type,
        target_date=goal.target_date
    )

    # 4️⃣ Base Macro Calculation
    target_macros = calorie_engine.calculate_macros(
        target_calories=hybrid_goal["calories"],
        weight_kg=measurement.weight_kg,
        goal_type=goal.goal_type
    )

    # =====================================================
    # 🔥 STEP 2 — PROGRESS ENGINE ADAPTATION
    # =====================================================

    measurements = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user_id)
        .order_by(BodyMeasurement.recorded_at.desc())
        .limit(20)
        .all()
    )

    progress_engine = ProgressEngine()

    progress = progress_engine.analyze_progress(
        measurements=measurements,
        active_goal=goal
    )

    # Increase protein if muscle loss
    if progress.get("muscle_loss_warning"):
        target_macros["protein"] *= 1.15

    # Slight protein boost on plateau
    elif progress.get("plateau_detected"):
        target_macros["protein"] *= 1.08

    target_macros["protein"] = round(target_macros["protein"], 2)

    # =====================================================
    # 🔥 STEP 3 — COMPLIANCE ADAPTATION
    # =====================================================

    compliance_engine = ComplianceEngine()

    compliance = compliance_engine.analyze_compliance(
        db=db,
        user_id=user_id
    )

    compliance_percent = compliance.get("calorie_compliance_percent", 100)

    # Under-eating consistently → reduce slightly
    if compliance_percent < 75:
        target_macros["calories"] *= 0.95

    # Over-eating consistently → tighten slightly
    elif compliance_percent > 110:
        target_macros["calories"] *= 0.97

    target_macros["calories"] = round(target_macros["calories"], 2)

    return target_macros


# =====================================================
# GENERATE DIET
# =====================================================
@router.post("/diet/generate")
def generate_diet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    context = build_user_context(db, current_user.id)
    target_macros = calculate_target_macros(db, current_user.id)

    engine = DietEngine()

    result = engine.generate_daily_plan(
        db=db,
        user_id=current_user.id,
        target_macros=target_macros,
        user_context=context,
        gpt_client=gpt_client
    )

    return result


# =====================================================
# REGENERATE DIET
# =====================================================
@router.post("/diet/regenerate")
def regenerate_diet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    context = build_user_context(db, current_user.id)
    target_macros = calculate_target_macros(db, current_user.id)

    engine = DietEngine()

    result = engine.regenerate_plan(
        db=db,
        user_id=current_user.id,
        target_macros=target_macros,
        user_context=context,
        gpt_client=gpt_client
    )

    return result


# =====================================================
# MODIFY DIET
# =====================================================
@router.patch("/diet/modify")
def modify_diet(
    action: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    engine = DietEngine()

    result = engine.modify_plan(
        db=db,
        user_id=current_user.id,
        action=action,
        data=payload
    )

    return result
