from fastapi import FastAPI
from app.core.database import engine, Base
from app.models.users import User
from app.api.v1.endpoints.compliance import router as compliance_router
from app.models.user_profile import UserProfile
from app.models.body_measurements import BodyMeasurement
from app.models.goal_settings import GoalSettings
from app.models.health_records import HealthRecord
from app.models.lifestyle_preferences import LifestylePreference
from app.models.behavior_engagement import BehaviorEngagement
from app.models.subscriptions import Subscription
from app.models.health_risk_scores import HealthRiskScore
from app.models.productivity_scores import ProductivityScore
from app.models.manual_activity import ManualActivity
from app.api.v1.endpoints.manual_activity import router as manual_activity_router
from app.api.v1.endpoints.health_records import router as health_router
from app.models.device_connections import DeviceConnection
from app.api.v1.endpoints.device_connections import router as device_router
from app.api.v1.endpoints.wearable_daily_stats import router as wearable_router
from app.models.wearable_daily_stats import WearableDailyStat
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.profile import router as profile_router
from app.api.v1.endpoints.body_measurements import router as measurement_router
from app.api.v1.endpoints.goal_settings import router as goal_router  # ✅ ADD THIS
from app.api.v1.endpoints.progress import router as progress_router
from app.api.v1.endpoints.nutrition import router as nutrition_router
from app.models.food_log import FoodLog
from app.api.v1.endpoints.food_log import router as food_log_router
from app.api.v1.endpoints.food import router as food_router
app = FastAPI(
    title="Fitness AI Backend",
    description="AI Human Optimization Platform Backend",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)
app.include_router(food_router, prefix="/api/v1", tags=["Food"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/api/v1", tags=["Profile"])
app.include_router(measurement_router, prefix="/api/v1", tags=["Measurements"])
app.include_router(goal_router, prefix="/api/v1", tags=["Goal"])  # ✅ ADD THIS
app.include_router(manual_activity_router, prefix="/api/v1", tags=["Manual Activity"])
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(device_router, prefix="/api/v1", tags=["Device"])
app.include_router(wearable_router, prefix="/api/v1", tags=["Wearable"])
app.include_router(progress_router, prefix="/api/v1", tags=["Progress"])
app.include_router(nutrition_router, prefix="/api/v1", tags=["Nutrition"])
app.include_router(food_log_router, prefix="/api/v1", tags=["Food Log"])
app.include_router(compliance_router, prefix="/api/v1", tags=["Compliance"])

@app.get("/")
def root():
    return {"message": "Fitness AI Backend is running successfully 🚀"}
