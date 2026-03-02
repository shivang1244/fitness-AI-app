from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_user
from app.models.users import User

from app.services.diet_engine import DietEngine
from app.services.supplement_engine import SupplementEngine

router = APIRouter()


# =====================================================
# GPT CLIENT WRAPPER (TEMP – Replace With Real API)
# =====================================================
from app.services.llm_client import LLMClient

llm = LLMClient()

def gpt_client(prompt: str):
    return llm.generate(prompt)

# =====================================================
# 1️⃣ DIET PLAN GENERATION
# =====================================================
@router.post("/diet/generate")
def generate_diet_plan(
    target_calories: float,
    target_protein: float,
    target_carbs: float,
    target_fat: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    diet_engine = DietEngine()

    target_macros = {
        "calories": target_calories,
        "protein": target_protein,
        "carbs": target_carbs,
        "fat": target_fat,
    }

    # Build minimal user context (expand later if needed)
    user_context = {
        "diet_type": current_user.profile.preferred_unit_system if current_user.profile else None,
        "allergies": [],
        "medical_conditions": {},
        "goal_type": None,
        "progress_flags": {},
        "budget": None,
    }

    try:
        plan = diet_engine.generate_daily_plan(
            db=db,
            user_id=current_user.id,
            target_macros=target_macros,
            user_context=user_context,
            gpt_client=gpt_client
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return plan


# =====================================================
# 2️⃣ SUPPLEMENT GENERATION
# =====================================================
@router.get("/supplements/generate")
def generate_supplements(
    monthly_budget: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    supplement_engine = SupplementEngine()

    try:
        supplements = supplement_engine.generate_supplements(
            db=db,
            user_id=current_user.id,
            gpt_client=gpt_client,
            monthly_budget=monthly_budget
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return supplements


# =====================================================
# 3️⃣ SUPPLEMENT SEARCH (EDUCATIONAL)
# =====================================================
@router.get("/supplements/search")
def search_supplement(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not query:
        raise HTTPException(status_code=400, detail="Query required")

    prompt = f"""
You are a neutral evidence-based supplement educator.

Explain the supplement: {query}

Rules:
- Educational tone only.
- No prescription language.
- Include:
  - What it is
  - How it works
  - Who may benefit
  - Who should avoid
  - Typical dosage
  - Possible side effects
  - Scientific support level

Return STRICT JSON format:

{{
  "supplement_name": "",
  "what_it_is": "",
  "how_it_works": "",
  "who_should_use": "",
  "who_should_avoid": "",
  "typical_dosage": "",
  "side_effects": "",
  "scientific_support_level": ""
}}
"""

    try:
        response = gpt_client(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return response
