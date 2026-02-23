from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.core.dependencies import get_db, get_current_user
from app.models.manual_activity import ManualActivity
from app.models.users import User
from app.schemas.manual_activity import (
    ManualActivityCreate,
    ManualActivityResponse,
    PREDEFINED_MET_MAP
)

router = APIRouter()


@router.post("/manual-activity", response_model=ManualActivityResponse)
def add_manual_activity(
    request: ManualActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Determine MET value
    if request.activity_type.value == "custom":
        if not request.custom_met_value:
            raise HTTPException(status_code=400, detail="Custom MET value required")
        met_value = request.custom_met_value
    else:
        met_value = PREDEFINED_MET_MAP.get(request.activity_type.value)

    new_activity = ManualActivity(
        user_id=current_user.id,
        activity_type=request.activity_type.value,
        met_value=met_value,
        duration_minutes=request.duration_minutes,
        activity_date=request.activity_date,
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return new_activity


@router.get("/manual-activity")
def get_manual_activities(
    activity_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    activities = (
        db.query(ManualActivity)
        .filter(
            ManualActivity.user_id == current_user.id,
            ManualActivity.activity_date == activity_date
        )
        .all()
    )

    return activities
