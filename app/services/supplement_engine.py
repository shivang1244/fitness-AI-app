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

        # 1️⃣ Fetch latest meal plan
        latest_plan = (
            db.query(DailyMealPlan)
            .filter(DailyMealPlan.user_id == user_id)
            .order_by(DailyMealPlan.plan_date.desc())
            .first()
        )

        if not latest_plan:
            return {
                "error": "No diet plan found. Generate diet plan first."
            }

        # 2️⃣ Fetch active goal
        goal = (
            db.query(GoalSettings)
            .filter(
                GoalSettings.user_id == user_id,
                GoalSettings.is_active.is_(True)
            )
            .first()
        )

        # 3️⃣ Fetch latest measurement
        measurement = (
            db.query(BodyMeasurement)
            .filter(BodyMeasurement.user_id == user_id)
            .order_by(BodyMeasurement.recorded_at.desc())
            .first()
        )

        # 4️⃣ Fetch health record
        health = (
            db.query(HealthRecord)
            .filter(HealthRecord.user_id == user_id)
            .first()
        )

        # 5️⃣ Build structured context
        context = {
            "goal_type": goal.goal_type if goal else None,
            "target_calories": latest_plan.target_calories,
            "target_protein": latest_plan.target_protein,
            "target_carbs": latest_plan.target_carbs,
            "target_fat": latest_plan.target_fat,
            # For now using target as actual (until food logging exists)
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
    # GPT PROMPT BUILDER
    # =====================================================
    def build_prompt(self, context):

        return f"""
You are a professional evidence-based supplement advisor.

Your role:
- Suggest supplements intelligently.
- Do NOT prescribe.
- Do NOT exaggerate benefits.
- Maintain educational tone.
- If diet already meets macro requirements, clearly mention that supplements are optional.

================ USER CONTEXT ================

Goal Type: {context.get("goal_type")}
Target Calories: {context.get("target_calories")}
Target Protein: {context.get("target_protein")}
Actual Protein Intake: {context.get("actual_protein")}
Body Fat %: {context.get("body_fat_percent")}
Monthly Supplement Budget: {context.get("monthly_supplement_budget")}

Health Conditions:
- Diabetes: {context["health_conditions"].get("has_diabetes")}
- High BP: {context["health_conditions"].get("has_bp")}
- Heart Condition: {context["health_conditions"].get("has_heart_conditions")}
- Pregnant: {context["health_conditions"].get("is_pregnant")}

=============================================

Rules:
- Consider budget if provided.
- Prioritize essential supplements if budget is limited.
- Avoid unsafe suggestions for listed medical conditions.
- Mention clearly when supplements are optional.
- Keep explanation practical and realistic.
- Do not push unnecessary supplementation.

Return STRICT JSON format only:

{{
  "summary_comment": "",
  "supplements": [
    {{
      "supplement_name": "",
      "category": "performance / recovery / health / general wellness",
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
    # SAFE JSON PARSER
    # =====================================================
    def safe_json_parse(self, response):

        try:
            return json.loads(response)
        except Exception:
            cleaned = response.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            return json.loads(cleaned[start:end])
