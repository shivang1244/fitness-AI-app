from app.core.database import SessionLocal
from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from app.core.token import decode_access_token
from app.models.users import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    import uuid
    user_id = uuid.UUID(user_id)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
