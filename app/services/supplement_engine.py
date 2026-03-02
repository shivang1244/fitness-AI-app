import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.meal_plan import DailyMealPlan
from app.models.goal_settings import GoalSettings
from app.models.body_measurements import BodyMeasurement
from app.models.health_records import HealthRecord


class SupplementEngine:

    # =====================================================
    # MAIN ENTRY
    # =====================================================
    def generate_supplements(
        self,
        db: Session,
        user_id,
        gpt_client,
        monthly_budget: Optional[float] = None
    ) -> Dict[str, Any]:

        latest_plan = (
            db.query(DailyMealPlan)
            .filter(DailyMealPlan.user_id == user_id)
            .order_by(DailyMealPlan.plan_date.desc())
            .first()
        )

        if not latest_plan:
            return {"error": "No diet plan found. Generate diet plan first."}

        goal = (
            db.query(GoalSettings)
            .filter(
                GoalSettings.user_id == user_id,
                GoalSettings.is_active.is_(True)
            )
            .first()
        )

        measurement = (
            db.query(BodyMeasurement)
            .filter(BodyMeasurement.user_id == user_id)
            .order_by(BodyMeasurement.recorded_at.desc())
            .first()
        )

        health = (
            db.query(HealthRecord)
            .filter(HealthRecord.user_id == user_id)
            .first()
        )

        context = {
            "goal_type": goal.goal_type if goal else None,
            "target_calories": latest_plan.target_calories,
            "target_protein": latest_plan.target_protein,
            "actual_protein": latest_plan.target_protein,
            "body_fat_percent": measurement.body_fat_percent if measurement else None,
            "monthly_supplement_budget": monthly_budget,
            "health_conditions": {
                "has_diabetes": health.has_diabetes if health else None,
                "has_bp": health.has_bp if health else None,
                "has_heart_conditions": health.has_heart_conditions if health else None,
                "is_pregnant": health.is_pregnant if health else None,
            }
        }

        prompt = self.build_prompt(context)

        response = gpt_client(prompt)

        return self.safe_json_parse(response)

    # =====================================================
    # PROMPT
    # =====================================================
    def build_prompt(self, context):

        return f"""
You are a professional evidence-based supplement advisor.

Goal Type: {context.get("goal_type")}
Target Calories: {context.get("target_calories")}
Target Protein: {context.get("target_protein")}
Actual Protein Intake: {context.get("actual_protein")}
Body Fat %: {context.get("body_fat_percent")}
Monthly Supplement Budget: {context.get("monthly_supplement_budget")}

Return STRICT JSON:

{{
  "summary_comment": "",
  "supplements": [
    {{
      "supplement_name": "",
      "category": "",
      "why_recommended": "",
      "benefits": "",
      "dosage": "",
      "timing": "",
      "who_should_avoid": "",
      "estimated_monthly_cost": ""
    }}
  ]
}}
"""

    # =====================================================
    # SAFE JSON PARSER (UPDATED)
    # =====================================================
    def safe_json_parse(self, response):

        # If LLMClient already returned dict
        if isinstance(response, dict):
            return response

        if not isinstance(response, str):
            return {"error": "Invalid GPT response type"}

        try:
            return json.loads(response)
        except Exception:
            cleaned = response.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "")
                cleaned = cleaned.replace("```", "").strip()

            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]

            return json.loads(cleaned)