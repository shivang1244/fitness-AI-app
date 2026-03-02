from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.users import User
from app.services.food_search_engine import FoodSearchEngine
from app.services.llm_client import LLMClient
router = APIRouter()


# TEMP GPT WRAPPER
llm = LLMClient()
def gpt_client(prompt: str):
    return llm.generate(prompt)

@router.get("/food/search")
def search_food(
    food: str = Query(...),

    grams: float = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    engine = FoodSearchEngine()

    try:
        result = engine.search_food(
            food_name=food,
            grams=grams,
            gpt_client=gpt_client
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result
