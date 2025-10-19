"""
Reminders API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models import Reminder, Cat, ReminderTime, ReminderFrequency, CatCareType
import structlog

logger = structlog.get_logger()
router = APIRouter()


class ReminderTimeCreate(BaseModel):
    """Reminder time creation model"""
    hour: int
    minute: int
    day_of_week: Optional[int] = None


class ReminderCreate(BaseModel):
    """Reminder creation model"""
    cat_id: str
    title: str
    type: str
    frequency: str = "daily"
    description: Optional[str] = None
    priority: int = 1
    scheduled_times: List[ReminderTimeCreate]


class ReminderUpdate(BaseModel):
    """Reminder update model"""
    title: Optional[str] = None
    type: Optional[str] = None
    frequency: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    is_enabled: Optional[bool] = None
    scheduled_times: Optional[List[ReminderTimeCreate]] = None


class ReminderResponse(BaseModel):
    """Reminder response model"""
    id: str
    cat_id: str
    title: str
    type: str
    frequency: str
    description: Optional[str]
    priority: int
    is_enabled: bool
    ai_optimized: bool
    completion_rate: float
    created_at: datetime
    updated_at: Optional[datetime]
    scheduled_times: List[dict]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ReminderResponse])
async def get_reminders(
    cat_id: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of reminders"""
    try:
        query = db.query(Reminder)
        
        if cat_id:
            query = query.filter(Reminder.cat_id == cat_id)
        if is_enabled is not None:
            query = query.filter(Reminder.is_enabled == is_enabled)
        
        reminders = query.offset(skip).limit(limit).all()
        
        # Add scheduled times to response
        result = []
        for reminder in reminders:
            reminder_dict = {
                "id": str(reminder.id),
                "cat_id": str(reminder.cat_id),
                "title": reminder.title,
                "type": reminder.type.value,
                "frequency": reminder.frequency.value,
                "description": reminder.description,
                "priority": reminder.priority,
                "is_enabled": reminder.is_enabled,
                "ai_optimized": reminder.ai_optimized,
                "completion_rate": reminder.completion_rate,
                "created_at": reminder.created_at,
                "updated_at": reminder.updated_at,
                "scheduled_times": [
                    {
                        "id": str(rt.id),
                        "hour": rt.hour,
                        "minute": rt.minute,
                        "day_of_week": rt.day_of_week,
                        "is_enabled": rt.is_enabled
                    }
                    for rt in reminder.scheduled_times
                ]
            }
            result.append(reminder_dict)
        
        return result
        
    except Exception as e:
        logger.error("Error getting reminders", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: str,
    db: Session = Depends(get_db)
):
    """Get reminder by ID"""
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            raise NotFoundError("Reminder", reminder_id)
        
        return {
            "id": str(reminder.id),
            "cat_id": str(reminder.cat_id),
            "title": reminder.title,
            "type": reminder.type.value,
            "frequency": reminder.frequency.value,
            "description": reminder.description,
            "priority": reminder.priority,
            "is_enabled": reminder.is_enabled,
            "ai_optimized": reminder.ai_optimized,
            "completion_rate": reminder.completion_rate,
            "created_at": reminder.created_at,
            "updated_at": reminder.updated_at,
            "scheduled_times": [
                {
                    "id": str(rt.id),
                    "hour": rt.hour,
                    "minute": rt.minute,
                    "day_of_week": rt.day_of_week,
                    "is_enabled": rt.is_enabled
                }
                for rt in reminder.scheduled_times
            ]
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting reminder", reminder_id=reminder_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ReminderResponse)
async def create_reminder(
    reminder_data: ReminderCreate,
    db: Session = Depends(get_db)
):
    """Create a new reminder"""
    try:
        # Validate cat exists
        cat = db.query(Cat).filter(Cat.id == reminder_data.cat_id).first()
        if not cat:
            raise NotFoundError("Cat", reminder_data.cat_id)
        
        # Create reminder
        reminder = Reminder(
            cat_id=reminder_data.cat_id,
            title=reminder_data.title,
            type=CatCareType(reminder_data.type),
            frequency=ReminderFrequency(reminder_data.frequency),
            description=reminder_data.description,
            priority=reminder_data.priority,
            is_enabled=True
        )
        
        db.add(reminder)
        db.flush()  # Get the ID
        
        # Create reminder times
        for time_data in reminder_data.scheduled_times:
            reminder_time = ReminderTime(
                reminder_id=reminder.id,
                hour=time_data.hour,
                minute=time_data.minute,
                day_of_week=time_data.day_of_week
            )
            db.add(reminder_time)
        
        db.commit()
        db.refresh(reminder)
        
        return {
            "id": str(reminder.id),
            "cat_id": str(reminder.cat_id),
            "title": reminder.title,
            "type": reminder.type.value,
            "frequency": reminder.frequency.value,
            "description": reminder.description,
            "priority": reminder.priority,
            "is_enabled": reminder.is_enabled,
            "ai_optimized": reminder.ai_optimized,
            "completion_rate": reminder.completion_rate,
            "created_at": reminder.created_at,
            "updated_at": reminder.updated_at,
            "scheduled_times": [
                {
                    "id": str(rt.id),
                    "hour": rt.hour,
                    "minute": rt.minute,
                    "day_of_week": rt.day_of_week,
                    "is_enabled": rt.is_enabled
                }
                for rt in reminder.scheduled_times
            ]
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error creating reminder", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: str,
    reminder_data: ReminderUpdate,
    db: Session = Depends(get_db)
):
    """Update reminder"""
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            raise NotFoundError("Reminder", reminder_id)
        
        # Update fields
        update_data = reminder_data.dict(exclude_unset=True, exclude={"scheduled_times"})
        for field, value in update_data.items():
            if field == "type" and value:
                setattr(reminder, field, CatCareType(value))
            elif field == "frequency" and value:
                setattr(reminder, field, ReminderFrequency(value))
            else:
                setattr(reminder, field, value)
        
        # Update scheduled times if provided
        if reminder_data.scheduled_times is not None:
            # Remove existing times
            db.query(ReminderTime).filter(ReminderTime.reminder_id == reminder_id).delete()
            
            # Add new times
            for time_data in reminder_data.scheduled_times:
                reminder_time = ReminderTime(
                    reminder_id=reminder.id,
                    hour=time_data.hour,
                    minute=time_data.minute,
                    day_of_week=time_data.day_of_week
                )
                db.add(reminder_time)
        
        reminder.updated_at = datetime.now()
        
        db.commit()
        db.refresh(reminder)
        
        return {
            "id": str(reminder.id),
            "cat_id": str(reminder.cat_id),
            "title": reminder.title,
            "type": reminder.type.value,
            "frequency": reminder.frequency.value,
            "description": reminder.description,
            "priority": reminder.priority,
            "is_enabled": reminder.is_enabled,
            "ai_optimized": reminder.ai_optimized,
            "completion_rate": reminder.completion_rate,
            "created_at": reminder.created_at,
            "updated_at": reminder.updated_at,
            "scheduled_times": [
                {
                    "id": str(rt.id),
                    "hour": rt.hour,
                    "minute": rt.minute,
                    "day_of_week": rt.day_of_week,
                    "is_enabled": rt.is_enabled
                }
                for rt in reminder.scheduled_times
            ]
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error updating reminder", reminder_id=reminder_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    db: Session = Depends(get_db)
):
    """Delete a reminder"""
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            raise NotFoundError("Reminder", reminder_id)
        
        # Delete reminder times first
        db.query(ReminderTime).filter(ReminderTime.reminder_id == reminder_id).delete()
        
        # Delete reminder
        db.delete(reminder)
        db.commit()
        
        return {"message": "Reminder deleted successfully"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error deleting reminder", reminder_id=reminder_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
