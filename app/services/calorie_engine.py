from app.models.user_profile import UserProfile
from app.models.body_measurements import BodyMeasurement
from typing import Optional
from datetime import date


class CalorieEngine:
    # -------------------------
    # Manual Activity Calories (MET based)
    # -------------------------
    @staticmethod
    def calculate_manual_activity_calories(
        activities: list,
        weight_kg: float
    ) -> float:

        total_calories = 0.0

        for activity in activities:
            duration_hours = activity.duration_minutes / 60
            calories = activity.met_value * weight_kg * duration_hours
            total_calories += calories

        return round(total_calories, 2)


    # -------------------------
    # BMR
    # -------------------------
    @staticmethod
    def calculate_bmr(profile: UserProfile, measurement: BodyMeasurement) -> float:

        if not profile.date_of_birth:
            raise ValueError("Date of birth is required to calculate BMR")

        if not profile.gender:
            raise ValueError("Gender is required to calculate BMR")

        weight = measurement.weight_kg
        height = measurement.height_cm

        today = date.today()
        age = today.year - profile.date_of_birth.year - (
            (today.month, today.day)
            < (profile.date_of_birth.month, profile.date_of_birth.day)
        )

        if profile.gender.lower() == "male":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        elif profile.gender.lower() == "female":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        else:
            raise ValueError("Invalid gender for BMR calculation")

        return round(bmr, 2)

    # -------------------------
    # Step Calories
    # -------------------------
    @staticmethod
    def estimate_step_calories(steps: int, weight_kg: float) -> float:
        if not steps:
            return 0.0

        base_factor = 0.04
        adjusted_factor = base_factor * (weight_kg / 70)

        return round(steps * adjusted_factor, 2)

    # -------------------------
    # TDEE Hybrid
    # -------------------------
    @staticmethod
    def calculate_tdee(
        bmr: float,
        weight_kg: float,
        activity_level: Optional[str] = None,
        steps: Optional[int] = None,
        wearable_active_calories: Optional[float] = None,
        wearable_total_calories: Optional[float] = None,
    ) -> float:

        if wearable_total_calories:
            return round(wearable_total_calories, 2)

        if wearable_active_calories:
            return round(bmr + wearable_active_calories, 2)

        if steps:
            step_calories = CalorieEngine.estimate_step_calories(
                steps=steps,
                weight_kg=weight_kg
            )
            return round(bmr + step_calories, 2)

        multiplier_map = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "high": 1.725,
            "athlete": 1.9
        }

        multiplier = multiplier_map.get(activity_level, 1.2)

        return round(bmr * multiplier, 2)

    # -------------------------
    # Hybrid Goal Engine (TIME + SAFETY)
    # -------------------------
    @staticmethod
    def calculate_hybrid_goal_calories(
        tdee: float,
        current_weight: float,
        body_fat: float,
        goal_weight: float,
        goal_type: str,
        target_date: date
    ):

        today = date.today()
        days_remaining = (target_date - today).days

        if days_remaining <= 0:
            return {
                "calories": tdee,
                "warning": "Target date already passed"
            }

        weight_diff = current_weight - goal_weight

        if goal_type == "fat_loss":

            total_kcal = weight_diff * 7700
            daily_required = total_kcal / days_remaining
            time_based_target = tdee - daily_required

            max_safe_deficit = tdee * 0.25
            safe_target = tdee - max_safe_deficit

            warning = None
            if daily_required > max_safe_deficit:
                warning = "Aggressive fat loss timeline. Risk of muscle loss."

            final_target = max(time_based_target, safe_target)

        elif goal_type == "muscle_gain":

            total_kcal = abs(weight_diff) * 7500
            daily_required = total_kcal / days_remaining
            time_based_target = tdee + daily_required

            max_safe_surplus = tdee * 0.15
            safe_target = tdee + max_safe_surplus

            warning = None
            if daily_required > max_safe_surplus:
                warning = "Aggressive muscle gain timeline. Risk of fat gain."

            final_target = min(time_based_target, safe_target)

        else:
            return {
                "calories": tdee,
                "warning": None
            }

        return {
            "calories": round(final_target, 2),
            "required_daily_adjustment": round(daily_required, 2),
            "warning": warning
        }

    # -------------------------
    # Macro Split
    # -------------------------
    @staticmethod
    def calculate_macros(target_calories: float, weight_kg: float, goal_type: str):

        if goal_type == "fat_loss":
            protein_per_kg = 2.2
        elif goal_type == "muscle_gain":
            protein_per_kg = 2.0
        elif goal_type == "maintain":
            protein_per_kg = 1.6
        elif goal_type == "yoga":
            protein_per_kg = 1.4
        elif goal_type == "calisthenics":
            protein_per_kg = 1.8
        else:
            protein_per_kg = 1.6

        protein_grams = weight_kg * protein_per_kg
        protein_calories = protein_grams * 4

        fat_calories = target_calories * 0.25
        fat_grams = fat_calories / 9

        remaining_calories = target_calories - (protein_calories + fat_calories)
        carbs_grams = remaining_calories / 4

        return {
            "calories": round(target_calories, 2),
            "protein_g": round(protein_grams, 2),
            "fat_g": round(fat_grams, 2),
            "carbs_g": round(carbs_grams, 2)
        }
