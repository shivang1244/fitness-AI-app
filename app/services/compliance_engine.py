from datetime import date, timedelta
from typing import Dict
from statistics import mean

from sqlalchemy.orm import Session

from app.models.food_log import FoodLog
from app.models.meal_plan import DailyMealPlan


class ComplianceEngine:

    def analyze_compliance(
        self,
        db: Session,
        user_id,
        days: int = 7
    ) -> Dict:

        today = date.today()
        start_date = today - timedelta(days=days)

        # -------------------------------------------------
        # Fetch logs
        # -------------------------------------------------
        logs = (
            db.query(FoodLog)
            .filter(
                FoodLog.user_id == user_id,
                FoodLog.log_date >= start_date
            )
            .all()
        )

        if not logs:
            return {
                "status": "no_data",
                "message": "No food logs found."
            }

        # -------------------------------------------------
        # Fetch latest meal plan for targets
        # -------------------------------------------------
        plan = (
            db.query(DailyMealPlan)
            .filter(DailyMealPlan.user_id == user_id)
            .order_by(DailyMealPlan.plan_date.desc())
            .first()
        )

        if not plan:
            return {
                "status": "no_target",
                "message": "No diet plan found."
            }

        # -------------------------------------------------
        # Group logs per day
        # -------------------------------------------------
        daily_totals = {}

        for log in logs:
            if log.log_date not in daily_totals:
                daily_totals[log.log_date] = {
                    "calories": 0,
                    "protein": 0
                }

            daily_totals[log.log_date]["calories"] += log.calories
            daily_totals[log.log_date]["protein"] += log.protein

        # -------------------------------------------------
        # Compute compliance per day
        # -------------------------------------------------
        calorie_percentages = []
        protein_percentages = []

        under_eating_days = 0
        over_eating_days = 0
        low_protein_days = 0

        for day, values in daily_totals.items():

            calorie_pct = (
                values["calories"] / plan.target_calories
                if plan.target_calories else 0
            )

            protein_pct = (
                values["protein"] / plan.target_protein
                if plan.target_protein else 0
            )

            calorie_percentages.append(calorie_pct)
            protein_percentages.append(protein_pct)

            # Behavior detection
            if calorie_pct < 0.8:
                under_eating_days += 1

            if calorie_pct > 1.15:
                over_eating_days += 1

            if protein_pct < 0.7:
                low_protein_days += 1

        # -------------------------------------------------
        # Average compliance
        # -------------------------------------------------
        avg_calorie_compliance = round(mean(calorie_percentages) * 100, 2)
        avg_protein_compliance = round(mean(protein_percentages) * 100, 2)

        # -------------------------------------------------
        # Compliance Score
        # -------------------------------------------------
        compliance_score = (
            (avg_calorie_compliance * 0.6) +
            (avg_protein_compliance * 0.4)
        )

        compliance_score = round(min(compliance_score, 100), 2)

        # -------------------------------------------------
        # Behavioral Insights
        # -------------------------------------------------
        behavior_flags = {
            "under_eating_pattern": under_eating_days >= 3,
            "over_eating_pattern": over_eating_days >= 3,
            "low_protein_pattern": low_protein_days >= 3,
        }

        # -------------------------------------------------
        # Interpretation
        # -------------------------------------------------
        if compliance_score >= 85:
            status = "Excellent"
        elif compliance_score >= 70:
            status = "Good"
        elif compliance_score >= 55:
            status = "Moderate"
        else:
            status = "Needs Improvement"

        interpretation = self.generate_interpretation(
            compliance_score,
            behavior_flags
        )

        return {
            "status": "analyzed",
            "compliance_score": compliance_score,
            "avg_calorie_compliance_percent": avg_calorie_compliance,
            "avg_protein_compliance_percent": avg_protein_compliance,
            "behavior_patterns": behavior_flags,
            "interpretation": interpretation
        }

    # -------------------------------------------------
    # Interpretation Generator
    # -------------------------------------------------
    def generate_interpretation(self, score, flags):

        if flags["low_protein_pattern"]:
            return "Protein intake is consistently low. This may slow muscle recovery and progress."

        if flags["under_eating_pattern"]:
            return "You are consistently under-eating. This may affect metabolism and recovery."

        if flags["over_eating_pattern"]:
            return "Frequent calorie surplus detected. This may slow fat loss progress."

        if score >= 85:
            return "Excellent dietary compliance. Keep consistent."

        if score >= 70:
            return "Good consistency. Minor improvements can optimize results."

        return "Compliance needs improvement. Focus on consistent logging and macro accuracy."
