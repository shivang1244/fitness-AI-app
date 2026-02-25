from datetime import timedelta
from statistics import mean
from typing import List, Dict

from app.models.body_measurements import BodyMeasurement
from app.models.goal_settings import GoalSettings


class ProgressEngine:

    @staticmethod
    def analyze_progress(
        measurements: List[BodyMeasurement],
        active_goal: GoalSettings
    ) -> Dict:

        if len(measurements) < 2:
            return {
                "status": "insufficient_data",
                "message": "Not enough data to analyze progress"
            }

        # Sort newest first
        measurements = sorted(
            measurements,
            key=lambda x: x.recorded_at,
            reverse=True
        )

        today = measurements[0].recorded_at.date()
        latest_measurement_date = measurements[0].recorded_at.date()

        # --------------------------
        # Weekly Check-in Enforcement
        # --------------------------
        days_since_last = (today - latest_measurement_date).days
        weekly_checkin_required = days_since_last >= 7

        fourteen_days_ago = today - timedelta(days=14)
        seven_days_ago = today - timedelta(days=7)

        last_14_days = [
            m for m in measurements
            if m.recorded_at.date() >= fourteen_days_ago
        ]

        last_7_days = [
            m for m in measurements
            if m.recorded_at.date() >= seven_days_ago
        ]

        if len(last_14_days) < 2:
            return {
                "status": "insufficient_recent_data",
                "message": "Need at least 2 measurements in last 14 days",
                "weekly_checkin_required": weekly_checkin_required,
                "days_since_last_measurement": days_since_last
            }

        # --------------------------
        # Current & Start Values
        # --------------------------
        start = last_14_days[-1]
        current = last_14_days[0]

        start_weight = start.weight_kg
        current_weight = current.weight_kg

        start_bf = start.body_fat_percent
        current_bf = current.body_fat_percent

        # --------------------------
        # Weight Trend
        # --------------------------
        weight_change_14d = current_weight - start_weight
        weekly_weight_change = weight_change_14d / 2

        avg_7d_weight = mean([m.weight_kg for m in last_7_days])

        # --------------------------
        # Body Fat Trend
        # --------------------------
        bodyfat_change_14d = current_bf - start_bf
        weekly_bodyfat_change = bodyfat_change_14d / 2

        # --------------------------
        # Fat & Lean Mass
        # --------------------------
        start_fat_mass = start_weight * (start_bf / 100)
        current_fat_mass = current_weight * (current_bf / 100)

        start_lean_mass = start_weight - start_fat_mass
        current_lean_mass = current_weight - current_fat_mass

        fat_mass_change = current_fat_mass - start_fat_mass
        lean_mass_change = current_lean_mass - start_lean_mass

        # --------------------------
        # Required Weekly Change
        # --------------------------
        days_remaining = (active_goal.target_date - today).days

        if days_remaining <= 0:
            return {
                "status": "goal_expired",
                "weekly_checkin_required": weekly_checkin_required,
                "days_since_last_measurement": days_since_last
            }

        total_weight_change_needed = active_goal.goal_weight - current_weight
        required_weekly_change = (
            total_weight_change_needed / days_remaining
        ) * 7

        # --------------------------
        # Plateau Detection
        # --------------------------
        plateau_weight_only = abs(weight_change_14d) < 0.2
        plateau_true = plateau_weight_only and abs(bodyfat_change_14d) < 0.3

        # --------------------------
        # On Track
        # --------------------------
        if active_goal.goal_type == "fat_loss":
            on_track = weekly_weight_change <= required_weekly_change
        elif active_goal.goal_type == "muscle_gain":
            on_track = weekly_weight_change >= required_weekly_change
        else:
            on_track = True

        # --------------------------
        # Muscle Loss Warning
        # --------------------------
        muscle_loss_warning = (
            active_goal.goal_type == "fat_loss"
            and lean_mass_change < -0.5
        )

        # --------------------------
        # Metabolic Adaptation
        # --------------------------
        metabolic_adaptation_detected = (
            active_goal.goal_type == "fat_loss"
            and plateau_true
            and not muscle_loss_warning
            and weekly_weight_change > -0.2
        )

        # --------------------------
        # Advanced Adjustment Strategy
        # --------------------------
        required_daily_adjustment = 0
        safe_recommended_adjustment = 0
        suggest_extend_goal = False
        recommended_new_goal_date = None
        estimated_weeks_needed = None

        deviation = 0

        if active_goal.goal_type == "fat_loss":
            deviation = weekly_weight_change - required_weekly_change
        elif active_goal.goal_type == "muscle_gain":
            deviation = required_weekly_change - weekly_weight_change

        if deviation > 0:
            kcal_gap_per_week = abs(deviation) * 7700
            required_daily_adjustment = round(kcal_gap_per_week / 7)

            safe_recommended_adjustment = round(required_daily_adjustment * 0.35)

            if active_goal.goal_type == "fat_loss":
                safe_recommended_adjustment *= -1

            # Cap safe adjustment
            safe_recommended_adjustment = max(-300, min(300, safe_recommended_adjustment))

            # Suggest timeline extension if aggressive
            if abs(required_daily_adjustment) > 400:
                suggest_extend_goal = True

                realistic_weekly_change = abs(weekly_weight_change)
                if realistic_weekly_change < 0.2:
                    realistic_weekly_change = 0.25

                total_remaining = abs(active_goal.goal_weight - current_weight)
                estimated_weeks_needed = round(
                    total_remaining / realistic_weekly_change, 1
                )

                recommended_new_goal_date = today + timedelta(
                    weeks=estimated_weeks_needed
                )

        # --------------------------
        # Progress Score
        # --------------------------
        progress_score = 50

        if on_track:
            progress_score += 25
        if not plateau_true:
            progress_score += 10
        if not muscle_loss_warning:
            progress_score += 15

        progress_score = max(0, min(100, progress_score))

        if progress_score >= 80:
            progress_status = "Excellent"
        elif progress_score >= 65:
            progress_status = "Good"
        elif progress_score >= 50:
            progress_status = "Moderate"
        else:
            progress_status = "Needs Adjustment"

        # --------------------------
        # Interpretation
        # --------------------------
        if muscle_loss_warning:
            interpretation = "Lean mass is decreasing. Increase protein or reduce deficit."
        elif metabolic_adaptation_detected:
            interpretation = "Metabolic adaptation suspected. Small calorie adjustment may help."
        elif plateau_true:
            interpretation = "Progress has stalled. Minor adjustment recommended."
        elif on_track:
            interpretation = "You are on track toward your goal. Stay consistent."
        else:
            interpretation = "Progress slower than expected. Review nutrition and training."

        return {
            "status": "analyzed",
            "progress_score": progress_score,
            "progress_status": progress_status,
            "interpretation": interpretation,
            "metabolic_adaptation_detected": metabolic_adaptation_detected,

            "current_weight": round(current_weight, 2),
            "avg_7d_weight": round(avg_7d_weight, 2),
            "weekly_weight_change": round(weekly_weight_change, 3),
            "required_weekly_change": round(required_weekly_change, 3),

            "weekly_bodyfat_change": round(weekly_bodyfat_change, 3),
            "fat_mass_change_14d": round(fat_mass_change, 2),
            "lean_mass_change_14d": round(lean_mass_change, 2),

            "plateau_detected": plateau_true,
            "on_track": on_track,
            "muscle_loss_warning": muscle_loss_warning,

            "required_daily_adjustment": required_daily_adjustment,
            "safe_recommended_adjustment": safe_recommended_adjustment,
            "suggest_extend_goal": suggest_extend_goal,
            "estimated_weeks_needed": estimated_weeks_needed,
            "recommended_new_goal_date": str(recommended_new_goal_date) if recommended_new_goal_date else None,

            "weekly_checkin_required": weekly_checkin_required,
            "days_since_last_measurement": days_since_last
        }
