from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.health_records import HealthRecord
from app.models.users import User
from app.schemas.health_records import (
    HealthRecordCreateUpdate,
    HealthRecordResponse
)

router = APIRouter()


# =========================
# CREATE / UPDATE HEALTH RECORD
# =========================
@router.post("/health", response_model=HealthRecordResponse)
def create_or_update_health_record(
    request: HealthRecordCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Fetch existing record
    health_record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == current_user.id)
        .first()
    )

    # Pregnancy rule: only valid if female
    if current_user.profile and current_user.profile.gender:
        if current_user.profile.gender.lower() != "female":
            request.is_pregnant = None

    if health_record:
        # Update existing record
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(health_record, field, value)

        db.commit()
        db.refresh(health_record)

        return health_record

    # Create new record
    new_record = HealthRecord(
        user_id=current_user.id,
        **request.model_dump(exclude_unset=True)
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record


# =========================
# GET HEALTH RECORD
# =========================
@router.get("/health", response_model=HealthRecordResponse)
def get_health_record(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    health_record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == current_user.id)
        .first()
    )

    if not health_record:
        raise HTTPException(status_code=404, detail="Health record not found")

    return health_record
