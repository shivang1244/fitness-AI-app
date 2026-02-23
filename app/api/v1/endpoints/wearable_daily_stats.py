from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.dependencies import get_db, get_current_user
from app.models.wearable_daily_stats import WearableDailyStat
from app.models.device_connections import DeviceConnection
from app.models.health_records import HealthRecord
from app.models.users import User
from app.schemas.wearable_daily_stats import (
    WearableDailyStatCreateUpdate,
    WearableDailyStatResponse
)

router = APIRouter()


# =========================
# SYNC DAILY WEARABLE DATA
# =========================
@router.post("/wearable/sync", response_model=WearableDailyStatResponse)
def sync_wearable_data(
    request: WearableDailyStatCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Ensure device sync is enabled
    device = (
        db.query(DeviceConnection)
        .filter(DeviceConnection.user_id == current_user.id)
        .first()
    )

    if not device or not device.wearable_sync_enabled:
        raise HTTPException(status_code=400, detail="Wearable sync not enabled")

    # Check if record already exists for that date
    existing_stat = (
        db.query(WearableDailyStat)
        .filter(
            WearableDailyStat.user_id == current_user.id,
            WearableDailyStat.stat_date == request.stat_date
        )
        .first()
    )

    if existing_stat:
        # Update existing
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(existing_stat, field, value)

        existing_stat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_stat)

        stat_record = existing_stat

    else:
        # Create new
        new_stat = WearableDailyStat(
            user_id=current_user.id,
            **request.model_dump(exclude_unset=True)
        )

        db.add(new_stat)
        db.commit()
        db.refresh(new_stat)

        stat_record = new_stat

    # -------------------------
    # Update resting heart rate in health record (if provided)
    # -------------------------
    if request.resting_heart_rate:
        health_record = (
            db.query(HealthRecord)
            .filter(HealthRecord.user_id == current_user.id)
            .first()
        )

        if health_record:
            health_record.resting_heart_rate = request.resting_heart_rate
            db.commit()

    # -------------------------
    # Update device last synced time
    # -------------------------
    device.last_synced_at = datetime.utcnow()
    db.commit()

    return stat_record


# =========================
# GET DAILY WEARABLE DATA
# =========================
@router.get("/wearable/daily", response_model=WearableDailyStatResponse)
def get_wearable_daily_stat(
    stat_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    stat = (
        db.query(WearableDailyStat)
        .filter(
            WearableDailyStat.user_id == current_user.id,
            WearableDailyStat.stat_date == stat_date.date()
        )
        .first()
    )

    if not stat:
        raise HTTPException(status_code=404, detail="No wearable data found")

    return stat
