import json
from typing import Dict, Any
from datetime import date
from sqlalchemy.orm import Session

from app.models.meal_plan import DailyMealPlan, Meal, MealIngredient


TOLERANCE_PERCENT = 0.05
MAX_ITERATIONS = 5


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

        iteration = 0

        plan_data = self.generate_initial_plan(
            target_macros,
            user_context,
            gpt_client
        )

        while iteration < MAX_ITERATIONS:

            # 1️⃣ STRUCTURE VALIDATION
            if not self.validate_structure(plan_data):
                plan_data = self.generate_initial_plan(
                    target_macros,
                    user_context,
                    gpt_client
                )
                iteration += 1
                continue

            # 2️⃣ SAFETY VALIDATION
            safety = self.enforce_safety_rules(plan_data, user_context)
            if not safety["is_safe"]:
                plan_data = self.generate_initial_plan(
                    target_macros,
                    user_context,
                    gpt_client
                )
                iteration += 1
                continue

            # 3️⃣ MACRO VALIDATION
            validation = self.validate_plan(plan_data, target_macros)
            if validation["is_valid"]:
                plan_data = self.enforce_macro_balance(plan_data, target_macros)
                break

            # 4️⃣ ADJUSTMENT LOOP
            delta = validation["delta"]

            plan_data = self.adjust_plan(
                plan_data,
                delta,
                user_context,
                gpt_client
            )

            iteration += 1

        # Final normalization
        plan_data = self.final_normalization(plan_data, target_macros)

        # Save
        self.save_plan_to_db(db, user_id, plan_data, target_macros)

        return plan_data

    # =====================================================
    # 🔥 REGENERATE PLAN
    # =====================================================
    def regenerate_plan(
        self,
        db: Session,
        user_id,
        target_macros: Dict[str, float],
        user_context: Dict[str, Any],
        gpt_client
    ) -> Dict[str, Any]:

        last_plan = (
            db.query(DailyMealPlan)
            .filter(DailyMealPlan.user_id == user_id)
            .order_by(DailyMealPlan.plan_date.desc())
            .first()
        )

        avoid_meals = []

        if last_plan:
            for meal in last_plan.meals:
                avoid_meals.append(meal.meal_name)

        user_context = dict(user_context)
        user_context["avoid_meals"] = avoid_meals

        return self.generate_daily_plan(
            db=db,
            user_id=user_id,
            target_macros=target_macros,
            user_context=user_context,
            gpt_client=gpt_client
        )

    # =====================================================
    # 🔥 MODIFY PLAN (Phase 3 Step 14–16)
    # =====================================================
    def modify_plan(
        self,
        db: Session,
        user_id,
        action: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:

        plan = (
            db.query(DailyMealPlan)
            .filter(DailyMealPlan.user_id == user_id)
            .order_by(DailyMealPlan.plan_date.desc())
            .first()
        )

        if not plan:
            return {"error": "No active plan found"}

        # REMOVE MEAL
        if action == "remove":
            meal_id = payload.get("meal_id")
            meal = (
                db.query(Meal)
                .filter(Meal.id == meal_id,
                        Meal.meal_plan_id == plan.id)
                .first()
            )
            if meal:
                db.delete(meal)
                db.commit()

        # ADD CUSTOM MEAL
        if action == "add_custom":
            meal = Meal(
                meal_plan_id=plan.id,
                meal_name=payload.get("meal_name"),
                meal_type=payload.get("meal_type"),
                total_calories=payload.get("calories"),
                total_protein=payload.get("protein"),
                total_carbs=payload.get("carbs"),
                total_fat=payload.get("fat"),
            )
            db.add(meal)
            db.commit()

        return self.recalculate_totals_only(db, plan.id)

    # =====================================================
    # RECALCULATE TOTALS ONLY
    # =====================================================
    def recalculate_totals_only(self, db: Session, plan_id):

        meals = db.query(Meal).filter(Meal.meal_plan_id == plan_id).all()

        totals = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0
        }

        for meal in meals:
            totals["calories"] += meal.total_calories
            totals["protein"] += meal.total_protein
            totals["carbs"] += meal.total_carbs
            totals["fat"] += meal.total_fat

        return {"updated_totals": totals}

    # =====================================================
    # INITIAL GPT GENERATION
    # =====================================================
    def generate_initial_plan(self, target_macros, user_context, gpt_client):
        prompt = self.build_initial_prompt(target_macros, user_context)
        response = gpt_client(prompt)
        return self.safe_json_parse(response)

    # =====================================================
    # PROMPT BUILDER
    # =====================================================
    def build_initial_prompt(self, target_macros, user_context):

        return f"""
You are a professional AI nutrition planner.

TARGET MACROS:
Calories: {target_macros['calories']}
Protein: {target_macros['protein']}g
Carbs: {target_macros['carbs']}g
Fat: {target_macros['fat']}g

Diet Type: {user_context.get("diet_type")}
Allergies: {user_context.get("allergies")}
Medical: {user_context.get("medical_conditions")}

Avoid repeating these meals:
{user_context.get("avoid_meals", [])}

Rules:
- Decide optimal number of meals required.
- Avoid repeating listed meals.
- Respect diet preference strictly.
- Respect medical restrictions.
- Include 2 alternatives per meal.
- Stay within ±5% macro tolerance.
- Return STRICT JSON only.

JSON FORMAT:
{{
  "meals": [],
  "supplements": []
}}
"""

    # =====================================================
    # STRUCTURE VALIDATION
    # =====================================================
    def validate_structure(self, plan_data):

        if "meals" not in plan_data or not isinstance(plan_data["meals"], list):
            return False

        for meal in plan_data["meals"]:

            if "meal_type" not in meal:
                return False

            if "primary" not in meal:
                return False

            if "alternatives" not in meal:
                return False

            if not isinstance(meal["alternatives"], list):
                return False

            if len(meal["alternatives"]) != 2:
                return False

            if not self.validate_meal_block(meal["primary"]):
                return False

            for alt in meal["alternatives"]:
                if not self.validate_meal_block(alt):
                    return False
                if alt.get("meal_name") == meal["primary"].get("meal_name"):
                    return False

        return True

    def validate_meal_block(self, meal_block):

        required_fields = [
            "meal_name",
            "ingredients",
            "total_calories",
            "total_protein",
            "total_carbs",
            "total_fat"
        ]

        for field in required_fields:
            if field not in meal_block:
                return False

        if not isinstance(meal_block["ingredients"], list):
            return False

        return True

    # =====================================================
    # SAFETY VALIDATION
    # =====================================================
    def enforce_safety_rules(self, plan_data, user_context):

        diet_type = user_context.get("diet_type")
        allergies = user_context.get("allergies", [])
        medical = user_context.get("medical_conditions", {})

        unsafe_keywords = []

        if diet_type == "vegan":
            unsafe_keywords += ["chicken", "fish", "egg", "milk", "cheese"]

        if diet_type == "vegetarian":
            unsafe_keywords += ["chicken", "fish", "mutton", "beef"]

        unsafe_keywords += allergies

        for meal in plan_data.get("meals", []):
            blocks = [meal.get("primary")] + meal.get("alternatives", [])

            for block in blocks:
                for ing in block.get("ingredients", []):
                    name = ing.get("ingredient_name", "").lower()

                    for unsafe in unsafe_keywords:
                        if unsafe in name:
                            return {"is_safe": False}

        return {"is_safe": True}

    # =====================================================
    # MACRO VALIDATION
    # =====================================================
    def validate_plan(self, plan_data, target_macros):

        totals = self.calculate_totals(plan_data)

        delta = {
            "calories": target_macros["calories"] - totals["calories"],
            "protein": target_macros["protein"] - totals["protein"],
            "carbs": target_macros["carbs"] - totals["carbs"],
            "fat": target_macros["fat"] - totals["fat"],
        }

        is_valid = all(
            abs(delta[k]) <= target_macros[k] * TOLERANCE_PERCENT
            for k in delta
        )

        return {"is_valid": is_valid, "delta": delta}

    # =====================================================
    # SMART MACRO BALANCING
    # =====================================================
    def enforce_macro_balance(self, plan_data, target_macros):

        meals = plan_data.get("meals", [])
        if not meals:
            return plan_data

        total_calories = target_macros["calories"]
        max_limit = total_calories * 0.40
        min_limit = total_calories * 0.10

        for meal in meals:
            primary = meal.get("primary", {})
            cal = primary.get("total_calories", 0)

            if cal > max_limit:
                primary["total_calories"] = max_limit

            if cal < min_limit:
                primary["total_calories"] = min_limit

        return plan_data

    # =====================================================
    # ADJUSTMENT
    # =====================================================
    def adjust_plan(self, plan_data, delta, user_context, gpt_client):
        prompt = f"""
Adjust this plan slightly to fix macro imbalance.

Delta:
{delta}

Keep structure same.
Return FULL JSON only.
"""
        response = gpt_client(prompt)
        return self.safe_json_parse(response)

    # =====================================================
    # TOTALS
    # =====================================================
    def calculate_totals(self, plan_data):

        totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

        for meal in plan_data.get("meals", []):
            primary = meal.get("primary", {})
            for k in totals:
                totals[k] += primary.get(f"total_{k}", 0)

        return totals

    # =====================================================
    # NORMALIZATION
    # =====================================================
    def final_normalization(self, plan_data, target_macros):

        totals = self.calculate_totals(plan_data)

        for key in ["calories", "protein", "carbs", "fat"]:
            diff = target_macros[key] - totals[key]
            if abs(diff) > target_macros[key] * TOLERANCE_PERCENT:
                plan_data["meals"][0]["primary"][f"total_{key}"] += diff

        return plan_data

    # =====================================================
    # SAVE
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

        for meal_data in plan_data.get("meals", []):
            primary = meal_data.get("primary", {})

            meal = Meal(
                meal_plan_id=daily_plan.id,
                meal_name=primary.get("meal_name"),
                meal_type=meal_data.get("meal_type"),
                total_calories=primary.get("total_calories"),
                total_protein=primary.get("total_protein"),
                total_carbs=primary.get("total_carbs"),
                total_fat=primary.get("total_fat"),
            )

            db.add(meal)
            db.flush()

            for ingredient in primary.get("ingredients", []):
                db.add(MealIngredient(
                    meal_id=meal.id,
                    ingredient_name=ingredient.get("ingredient_name"),
                    quantity_grams=ingredient.get("quantity_grams"),
                    calories=ingredient.get("calories"),
                    protein=ingredient.get("protein"),
                    carbs=ingredient.get("carbs"),
                    fat=ingredient.get("fat"),
                ))

        db.commit()

    # =====================================================
    # SAFE JSON PARSER
    # =====================================================
    def safe_json_parse(self, response):
        try:
            return json.loads(response)
        except:
            cleaned = response.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            return json.loads(cleaned[start:end])
