"""
Database models for CatAlert application
"""
from app.models.user import User
from app.models.cat import Cat
from app.models.reminder import Reminder, ReminderTime, ReminderFrequency, CatCareType
from app.models.activity import ActivityRecord, ActivityStatus
from app.models.health import HealthRecord
from app.models.ai_interaction import AIInteraction, AIInsight

__all__ = [
    "User",
    "Cat", 
    "Reminder",
    "ReminderTime",
    "ReminderFrequency",
    "CatCareType",
    "ActivityRecord",
    "ActivityStatus",
    "HealthRecord",
    "AIInteraction",
    "AIInsight"
]
