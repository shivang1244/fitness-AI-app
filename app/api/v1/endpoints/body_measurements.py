import math
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.body_measurements import BodyMeasurement
from app.models.users import User
from app.schemas.body_measurements import (
    BodyMeasurementCreate,
    BodyMeasurementUpdate,
)

router = APIRouter()


# =========================
# Body Fat Formulas
# =========================

def calculate_body_fat_male(height_cm, neck_cm, waist_cm):
    return (
        86.010 * math.log10(waist_cm - neck_cm)
        - 70.041 * math.log10(height_cm)
        + 36.76
    )


def calculate_body_fat_female(height_cm, neck_cm, waist_cm, hip_cm):
    return (
        163.205 * math.log10(waist_cm + hip_cm - neck_cm)
        - 97.684 * math.log10(height_cm)
        - 78.387
    )


# =========================
# ADD MEASUREMENT
# =========================

@router.post("/measurements")
def add_body_measurement(
    request: BodyMeasurementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.profile:
        raise HTTPException(status_code=400, detail="Complete profile first")

    gender = current_user.profile.gender
    unit_system = request.unit_system or current_user.profile.preferred_unit_system

    # Work with metric internally
    height = request.height_cm
    weight = request.weight_kg
    neck = request.neck_cm
    waist = request.waist_cm
    hip = request.hip_cm

    # Convert if imperial
    if unit_system == "imperial":
        height *= 2.54
        neck *= 2.54
        waist *= 2.54
        if hip is not None:
            hip *= 2.54
        weight *= 0.453592

    # Validate + calculate
    if gender == "male":
        if waist <= neck:
            raise HTTPException(
                status_code=400,
                detail="Waist must be greater than neck",
            )
        body_fat = calculate_body_fat_male(height, neck, waist)

    elif gender == "female":
        if hip is None:
            raise HTTPException(
                status_code=400,
                detail="Hip required for female",
            )
        if (waist + hip) <= neck:
            raise HTTPException(
                status_code=400,
                detail="Invalid measurements",
            )
        body_fat = calculate_body_fat_female(height, neck, waist, hip)

    else:
        raise HTTPException(status_code=400, detail="Invalid gender")

    new_measurement = BodyMeasurement(
        id=uuid.uuid4(),
        user_id=current_user.id,
        height_cm=height,
        weight_kg=weight,
        activity_level=request.activity_level.value,
        neck_cm=neck,
        waist_cm=waist,
        hip_cm=hip,
        chest_cm=request.chest_cm,
        left_arm_cm=request.left_arm_cm,
        right_arm_cm=request.right_arm_cm,
        left_thigh_cm=request.left_thigh_cm,
        right_thigh_cm=request.right_thigh_cm,
        calf_cm=request.calf_cm,
        body_fat_percent=round(body_fat, 2),
    )

    db.add(new_measurement)
    db.commit()
    db.refresh(new_measurement)

    return {
        "message": "Measurement added successfully",
        "calculated_body_fat_percent": round(body_fat, 2),
    }


# =========================
# GET HISTORY
# =========================

@router.get("/measurements")
def get_measurement_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == current_user.id)
        .order_by(BodyMeasurement.recorded_at.desc())
        .all()
    )


# =========================
# GET SINGLE (UUID FIXED)
# =========================

@router.get("/measurements/{measurement_id}")
def get_single_measurement(
    measurement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    measurement = (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.id == measurement_id,
            BodyMeasurement.user_id == current_user.id,
        )
        .first()
    )

    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")

    return measurement


# =========================
# PATCH UPDATE (SAFE)
# =========================

@router.patch("/measurements/{measurement_id}")
def update_measurement(
    measurement_id: UUID,
    request: BodyMeasurementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    measurement = (
        db.query(BodyMeasurement)
        .filter(
            BodyMeasurement.id == measurement_id,
            BodyMeasurement.user_id == current_user.id,
        )
        .first()
    )

    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")

    if not current_user.profile:
        raise HTTPException(status_code=400, detail="Complete profile first")

    gender = current_user.profile.gender
    request_data = request.model_dump(exclude_unset=True)

    unit_system = request_data.get("unit_system") or current_user.profile.preferred_unit_system

    # Start from existing metric values
    height = measurement.height_cm
    weight = measurement.weight_kg
    neck = measurement.neck_cm
    waist = measurement.waist_cm
    hip = measurement.hip_cm

    # Override only provided fields
    if "height_cm" in request_data:
        height = request_data["height_cm"]
    if "weight_kg" in request_data:
        weight = request_data["weight_kg"]
    if "neck_cm" in request_data:
        neck = request_data["neck_cm"]
    if "waist_cm" in request_data:
        waist = request_data["waist_cm"]
    if "hip_cm" in request_data:
        hip = request_data["hip_cm"]

    # Convert if imperial
    if unit_system == "imperial":
        height *= 2.54
        neck *= 2.54
        waist *= 2.54
        if hip is not None:
            hip *= 2.54
        weight *= 0.453592

    # Recalculate
    if gender == "male":
        if waist <= neck:
            raise HTTPException(status_code=400, detail="Waist must be greater than neck")
        body_fat = calculate_body_fat_male(height, neck, waist)

    elif gender == "female":
        if hip is None:
            raise HTTPException(status_code=400, detail="Hip required for female")
        body_fat = calculate_body_fat_female(height, neck, waist, hip)

    else:
        raise HTTPException(status_code=400, detail="Invalid gender")

    # Save updated metric values
    measurement.height_cm = height
    measurement.weight_kg = weight
    measurement.neck_cm = neck
    measurement.waist_cm = waist
    measurement.hip_cm = hip
    measurement.body_fat_percent = round(body_fat, 2)

    # Optional fields
    for field in [
        "chest_cm",
        "left_arm_cm",
        "right_arm_cm",
        "left_thigh_cm",
        "right_thigh_cm",
        "calf_cm",
        "activity_level",
    ]:
        if field in request_data:
            value = request_data[field]
            if hasattr(value, "value"):
                value = value.value
            setattr(measurement, field, value)

    db.commit()
    db.refresh(measurement)

    return {
        "message": "Measurement updated successfully",
        "updated_body_fat_percent": round(body_fat, 2),
    }

