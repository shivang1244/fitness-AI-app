import random
from datetime import datetime, timedelta
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import OTPVerificationRequest
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.models.users import User
from app.schemas.auth import UserSignupRequest
from app.core.security import verify_password
from app.schemas.auth import UserLoginRequest
from app.core.token import create_access_token
from app.core.dependencies import get_current_user


router = APIRouter()


@router.post("/signup")
def signup_user(request: UserSignupRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate OTP (temporary simple logic)
    otp_code = str(random.randint(100000, 999999))
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    # Hash password
    hashed_pwd = hash_password(request.password)

    # Create new user
    new_user = User(
        email=request.email,
        hashed_password=hashed_pwd,
        otp_code=otp_code,
        otp_expiry=otp_expiry,
        is_email_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully. Verify OTP.",
        "otp_for_testing": otp_code  # REMOVE in production
    }

@router.post("/verify-otp")
def verify_otp(request: OTPVerificationRequest, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_email_verified:
        return {"message": "Email already verified"}

    if not user.otp_code or not user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP not generated")

    # Check expiry
    if datetime.utcnow() > user.otp_expiry:

        raise HTTPException(status_code=400, detail="OTP expired")

    # Check OTP match
    if user.otp_code != request.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Mark verified
    user.is_email_verified = True
    user.otp_code = None
    user.otp_expiry = None

    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/login")
def login_user(request: UserLoginRequest, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not user.is_email_verified:
        raise HTTPException(status_code=400, detail="Email not verified")

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create JWT token
    access_token = create_access_token(data={"user_id": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "is_verified": current_user.is_email_verified
    }
