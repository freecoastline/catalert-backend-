"""
API v1 router configuration
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import cats, reminders, activities, ai, health, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cats.router, prefix="/cats", tags=["cats"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
