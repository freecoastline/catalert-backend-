"""
Activities API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models import ActivityRecord, Cat, ActivityStatus, CatCareType
import structlog

logger = structlog.get_logger()
router = APIRouter()


class ActivityCreate(BaseModel):
    """Activity creation model"""
    reminder_id: str
    cat_id: str
    type: str
    scheduled_time: datetime
    notes: Optional[str] = None


class ActivityUpdate(BaseModel):
    """Activity update model"""
    status: Optional[str] = None
    notes: Optional[str] = None
    quality_rating: Optional[int] = None
    actual_duration: Optional[int] = None
    cat_behavior: Optional[str] = None


class ActivityResponse(BaseModel):
    """Activity response model"""
    id: str
    reminder_id: str
    cat_id: str
    type: str
    scheduled_time: datetime
    complete_time: Optional[datetime]
    status: str
    actual_duration: Optional[int]
    notes: Optional[str]
    quality_rating: Optional[int]
    cat_behavior: Optional[str]
    anomaly_detected: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ActivityResponse])
async def get_activities(
    cat_id: Optional[str] = None,
    status: Optional[str] = None,
    days: int = 30,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of activities"""
    try:
        from datetime import timedelta
        
        query = db.query(ActivityRecord).filter(
            ActivityRecord.created_at >= datetime.now() - timedelta(days=days)
        )
        
        if cat_id:
            query = query.filter(ActivityRecord.cat_id == cat_id)
        if status:
            query = query.filter(ActivityRecord.status == ActivityStatus(status))
        
        activities = query.order_by(ActivityRecord.scheduled_time.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": str(activity.id),
                "reminder_id": str(activity.reminder_id),
                "cat_id": str(activity.cat_id),
                "type": activity.type.value,
                "scheduled_time": activity.scheduled_time,
                "complete_time": activity.complete_time,
                "status": activity.status.value,
                "actual_duration": activity.actual_duration,
                "notes": activity.notes,
                "quality_rating": activity.quality_rating,
                "cat_behavior": activity.cat_behavior,
                "anomaly_detected": activity.anomaly_detected,
                "created_at": activity.created_at,
                "updated_at": activity.updated_at
            }
            for activity in activities
        ]
        
    except Exception as e:
        logger.error("Error getting activities", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    db: Session = Depends(get_db)
):
    """Get activity by ID"""
    try:
        activity = db.query(ActivityRecord).filter(ActivityRecord.id == activity_id).first()
        if not activity:
            raise NotFoundError("Activity", activity_id)
        
        return {
            "id": str(activity.id),
            "reminder_id": str(activity.reminder_id),
            "cat_id": str(activity.cat_id),
            "type": activity.type.value,
            "scheduled_time": activity.scheduled_time,
            "complete_time": activity.complete_time,
            "status": activity.status.value,
            "actual_duration": activity.actual_duration,
            "notes": activity.notes,
            "quality_rating": activity.quality_rating,
            "cat_behavior": activity.cat_behavior,
            "anomaly_detected": activity.anomaly_detected,
            "created_at": activity.created_at,
            "updated_at": activity.updated_at
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting activity", activity_id=activity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ActivityResponse)
async def create_activity(
    activity_data: ActivityCreate,
    db: Session = Depends(get_db)
):
    """Create a new activity"""
    try:
        # Validate cat exists
        cat = db.query(Cat).filter(Cat.id == activity_data.cat_id).first()
        if not cat:
            raise NotFoundError("Cat", activity_data.cat_id)
        
        # Create activity
        activity = ActivityRecord(
            reminder_id=activity_data.reminder_id,
            cat_id=activity_data.cat_id,
            type=CatCareType(activity_data.type),
            scheduled_time=activity_data.scheduled_time,
            status=ActivityStatus.PENDING,
            notes=activity_data.notes
        )
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        return {
            "id": str(activity.id),
            "reminder_id": str(activity.reminder_id),
            "cat_id": str(activity.cat_id),
            "type": activity.type.value,
            "scheduled_time": activity.scheduled_time,
            "complete_time": activity.complete_time,
            "status": activity.status.value,
            "actual_duration": activity.actual_duration,
            "notes": activity.notes,
            "quality_rating": activity.quality_rating,
            "cat_behavior": activity.cat_behavior,
            "anomaly_detected": activity.anomaly_detected,
            "created_at": activity.created_at,
            "updated_at": activity.updated_at
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error creating activity", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
    activity_data: ActivityUpdate,
    db: Session = Depends(get_db)
):
    """Update activity"""
    try:
        activity = db.query(ActivityRecord).filter(ActivityRecord.id == activity_id).first()
        if not activity:
            raise NotFoundError("Activity", activity_id)
        
        # Update fields
        update_data = activity_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value:
                setattr(activity, field, ActivityStatus(value))
                if value == "completed" and not activity.complete_time:
                    activity.complete_time = datetime.now()
            else:
                setattr(activity, field, value)
        
        activity.updated_at = datetime.now()
        
        db.commit()
        db.refresh(activity)
        
        return {
            "id": str(activity.id),
            "reminder_id": str(activity.reminder_id),
            "cat_id": str(activity.cat_id),
            "type": activity.type.value,
            "scheduled_time": activity.scheduled_time,
            "complete_time": activity.complete_time,
            "status": activity.status.value,
            "actual_duration": activity.actual_duration,
            "notes": activity.notes,
            "quality_rating": activity.quality_rating,
            "cat_behavior": activity.cat_behavior,
            "anomaly_detected": activity.anomaly_detected,
            "created_at": activity.created_at,
            "updated_at": activity.updated_at
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error updating activity", activity_id=activity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{activity_id}/complete")
async def complete_activity(
    activity_id: str,
    notes: Optional[str] = None,
    quality_rating: Optional[int] = None,
    actual_duration: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Mark activity as completed"""
    try:
        activity = db.query(ActivityRecord).filter(ActivityRecord.id == activity_id).first()
        if not activity:
            raise NotFoundError("Activity", activity_id)
        
        activity.status = ActivityStatus.COMPLETED
        activity.complete_time = datetime.now()
        
        if notes:
            activity.notes = notes
        if quality_rating:
            activity.quality_rating = quality_rating
        if actual_duration:
            activity.actual_duration = actual_duration
        
        activity.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Activity completed successfully",
            "activity_id": activity_id,
            "complete_time": activity.complete_time.isoformat()
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error completing activity", activity_id=activity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cats/{cat_id}/today")
async def get_today_activities(
    cat_id: str,
    db: Session = Depends(get_db)
):
    """Get today's activities for a cat"""
    try:
        from datetime import timedelta
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        
        activities = db.query(ActivityRecord).filter(
            ActivityRecord.cat_id == cat_id,
            ActivityRecord.scheduled_time >= today_start,
            ActivityRecord.scheduled_time < tomorrow_start
        ).order_by(ActivityRecord.scheduled_time).all()
        
        return {
            "cat_id": cat_id,
            "date": today_start.date().isoformat(),
            "activities": [
                {
                    "id": str(activity.id),
                    "type": activity.type.value,
                    "scheduled_time": activity.scheduled_time.isoformat(),
                    "complete_time": activity.complete_time.isoformat() if activity.complete_time else None,
                    "status": activity.status.value,
                    "notes": activity.notes,
                    "quality_rating": activity.quality_rating
                }
                for activity in activities
            ],
            "total_count": len(activities),
            "completed_count": len([a for a in activities if a.status == ActivityStatus.COMPLETED]),
            "pending_count": len([a for a in activities if a.status == ActivityStatus.PENDING])
        }
        
    except Exception as e:
        logger.error("Error getting today's activities", cat_id=cat_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
