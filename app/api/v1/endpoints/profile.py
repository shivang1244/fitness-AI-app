from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user_profile import UserProfile
from app.models.users import User
from app.schemas.user_profile import UserProfileCreateUpdate

router = APIRouter()


@router.post("/profile")
def create_or_update_profile(
    request: UserProfileCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    request_data = request.model_dump(exclude_unset=True)

    # Ensure preferred_unit_system always exists
    if "preferred_unit_system" not in request_data:
        request_data["preferred_unit_system"] = "metric"

    if profile:
        # Update existing profile
        for field, value in request_data.items():
            setattr(profile, field, value)

        db.commit()
        db.refresh(profile)

        return {"message": "Profile updated successfully"}

    # Create new profile
    new_profile = UserProfile(
        user_id=current_user.id,
        **request_data
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return {"message": "Profile created successfully"}
