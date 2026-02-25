from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.users import User
from app.services.compliance_engine import ComplianceEngine

router = APIRouter()


@router.get("/compliance")
def get_compliance(
    days: int = Query(default=7, ge=3, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    engine = ComplianceEngine()

    result = engine.analyze_compliance(
        db=db,
        user_id=current_user.id,
        days=days
    )

    return result
