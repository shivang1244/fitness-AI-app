from pydantic import BaseModel, EmailStr, Field


class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

    model_config = {
        "from_attributes": True
    }


class OTPVerificationRequest(BaseModel):
    email: EmailStr
    otp_code: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
