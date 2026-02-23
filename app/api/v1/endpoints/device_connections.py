from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.dependencies import get_db, get_current_user
from app.models.device_connections import DeviceConnection
from app.models.users import User
from app.schemas.device_connections import (
    DeviceConnectionCreateUpdate,
    DeviceConnectionResponse
)

router = APIRouter()


# =========================
# CONNECT / UPDATE DEVICE
# =========================
@router.post("/device", response_model=DeviceConnectionResponse)
def connect_or_update_device(
    request: DeviceConnectionCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    device = (
        db.query(DeviceConnection)
        .filter(DeviceConnection.user_id == current_user.id)
        .first()
    )

    if device:
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(device, field, value)

        db.commit()
        db.refresh(device)
        return device

    new_device = DeviceConnection(
        user_id=current_user.id,
        **request.model_dump(exclude_unset=True)
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return new_device


# =========================
# GET DEVICE STATUS
# =========================
@router.get("/device", response_model=DeviceConnectionResponse)
def get_device_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    device = (
        db.query(DeviceConnection)
        .filter(DeviceConnection.user_id == current_user.id)
        .first()
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not connected")

    return device
