from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.body_measurements import BodyMeasurement
from app.models.goal_settings import GoalSettings
from app.models.users import User

from app.services.progress_engine import ProgressEngine

router = APIRouter()


@router.get("/progress")
def get_progress_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 1️⃣ Fetch all measurements
    measurements = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == current_user.id)
        .order_by(BodyMeasurement.recorded_at.asc())
        .all()
    )

    if not measurements:
        raise HTTPException(status_code=400, detail="No measurements found")

    # 2️⃣ Fetch active goal
    active_goal = (
        db.query(GoalSettings)
        .filter(
            GoalSettings.user_id == current_user.id,
            GoalSettings.is_active.is_(True)
        )
        .first()
    )

    if not active_goal:
        raise HTTPException(status_code=400, detail="No active goal found")

    # 3️⃣ Analyze progress
    result = ProgressEngine.analyze_progress(
        measurements=measurements,
        active_goal=active_goal
    )

    return result
