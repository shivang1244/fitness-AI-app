import json
from typing import Dict, Any
from datetime import date
from sqlalchemy.orm import Session

from app.models.meal_plan import DailyMealPlan, Meal, MealIngredient


class DietEngine:

    # =====================================================
    # PUBLIC ENTRY POINT
    # =====================================================
    def generate_daily_plan(
        self,
        db: Session,
        user_id,
        target_macros: Dict[str, float],
        user_context: Dict[str, Any],
        gpt_client
    ) -> Dict[str, Any]:

        plan_data = self.generate_initial_plan(
            target_macros,
            user_context,
            gpt_client
        )

        if not isinstance(plan_data, dict):
            return {"error": "Invalid plan format from AI"}

        if not self.validate_structure(plan_data):
            return {"error": "AI returned invalid meal structure"}

        self.save_plan_to_db(db, user_id, plan_data, target_macros)

        return plan_data

    # =====================================================
    # GPT CALL
    # =====================================================
    def generate_initial_plan(self, target_macros, user_context, gpt_client):
        prompt = self.build_initial_prompt(target_macros, user_context)
        response = gpt_client(prompt)
        return self.safe_json_parse(response)

    # =====================================================
    # PROMPT
    # =====================================================
    def build_initial_prompt(self, target_macros, user_context):

        return f"""
Generate a structured daily meal plan.

TARGET:
Calories: {target_macros['calories']}
Protein: {target_macros['protein']}
Carbs: {target_macros['carbs']}
Fat: {target_macros['fat']}

Return JSON:

{{
  "meals": [
    {{
      "name": "",
      "items": [],
      "total": {{
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0
      }}
    }}
  ],
  "supplements": []
}}
"""

    # =====================================================
    # STRUCTURE VALIDATION
    # =====================================================
    def validate_structure(self, plan_data):

        meals = plan_data.get("meals")

        if not isinstance(meals, list):
            return False

        for meal in meals:
            if not isinstance(meal, dict):
                return False

            if "name" not in meal:
                return False

            if "items" not in meal or not isinstance(meal["items"], list):
                return False

            if "total" not in meal or not isinstance(meal["total"], dict):
                return False

        return True

    # =====================================================
    # SAVE TO DATABASE
    # =====================================================
    def save_plan_to_db(self, db: Session, user_id, plan_data, target_macros):

        daily_plan = DailyMealPlan(
            user_id=user_id,
            plan_date=date.today(),
            target_calories=target_macros["calories"],
            target_protein=target_macros["protein"],
            target_carbs=target_macros["carbs"],
            target_fat=target_macros["fat"],
        )

        db.add(daily_plan)
        db.flush()

        meals = plan_data.get("meals", [])

        for meal_data in meals:

            if not isinstance(meal_data, dict):
                continue

            total = meal_data.get("total", {})

            meal = Meal(
                meal_plan_id=daily_plan.id,
                meal_name=meal_data.get("name") or "Unnamed Meal",
                meal_type=meal_data.get("name") or "meal",
                total_calories=total.get("calories", 0),
                total_protein=total.get("protein", 0),
                total_carbs=total.get("carbs", 0),
                total_fat=total.get("fat", 0),
            )

            db.add(meal)
            db.flush()

            items = meal_data.get("items", [])

            for item in items:
                if not isinstance(item, dict):
                    continue

                db.add(MealIngredient(
                    meal_id=meal.id,
                    ingredient_name=item.get("food") or "Unknown",
                    quantity_text=str(item.get("quantity")) if item.get("quantity") else None,
                    calories=item.get("calories") or 0,
                    protein=item.get("protein") or 0,
                    carbs=item.get("carbs") or 0,
                    fat=item.get("fat") or 0,
                ))

        db.commit()

    # =====================================================
    # SAFE JSON PARSER
    # =====================================================
    def safe_json_parse(self, response):

        if isinstance(response, dict):
            return response

        if not isinstance(response, str):
            return {}

        try:
            return json.loads(response)
        except:
            cleaned = response.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "")
                cleaned = cleaned.replace("```", "").strip()

            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]

            try:
                return json.loads(cleaned)
            except:
                return {}