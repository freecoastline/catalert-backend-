"""
Health records API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models import HealthRecord, Cat
import structlog

logger = structlog.get_logger()
router = APIRouter()


class HealthRecordCreate(BaseModel):
    """Health record creation model"""
    cat_id: str
    record_type: str
    value: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    appetite_level: Optional[int] = None
    activity_level: Optional[int] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None
    weight: Optional[float] = None
    body_condition_score: Optional[int] = None
    coat_condition: Optional[str] = None
    eye_condition: Optional[str] = None
    ear_condition: Optional[str] = None
    behavior_notes: Optional[str] = None


class HealthRecordUpdate(BaseModel):
    """Health record update model"""
    record_type: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    appetite_level: Optional[int] = None
    activity_level: Optional[int] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None
    weight: Optional[float] = None
    body_condition_score: Optional[int] = None
    coat_condition: Optional[str] = None
    eye_condition: Optional[str] = None
    ear_condition: Optional[str] = None
    behavior_notes: Optional[str] = None


class HealthRecordResponse(BaseModel):
    """Health record response model"""
    id: str
    cat_id: str
    record_type: str
    value: Optional[float]
    unit: Optional[str]
    notes: Optional[str]
    appetite_level: Optional[int]
    activity_level: Optional[int]
    mood: Optional[str]
    energy_level: Optional[int]
    weight: Optional[float]
    body_condition_score: Optional[int]
    coat_condition: Optional[str]
    eye_condition: Optional[str]
    ear_condition: Optional[str]
    behavior_notes: Optional[str]
    ai_health_score: Optional[float]
    anomaly_detected: bool
    recorded_at: datetime
    recorded_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[HealthRecordResponse])
async def get_health_records(
    cat_id: Optional[str] = None,
    record_type: Optional[str] = None,
    days: int = 30,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of health records"""
    try:
        from datetime import timedelta
        
        query = db.query(HealthRecord).filter(
            HealthRecord.created_at >= datetime.now() - timedelta(days=days)
        )
        
        if cat_id:
            query = query.filter(HealthRecord.cat_id == cat_id)
        if record_type:
            query = query.filter(HealthRecord.record_type == record_type)
        
        records = query.order_by(HealthRecord.recorded_at.desc()).offset(skip).limit(limit).all()
        
        return records
        
    except Exception as e:
        logger.error("Error getting health records", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{record_id}", response_model=HealthRecordResponse)
async def get_health_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """Get health record by ID"""
    try:
        record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
        if not record:
            raise NotFoundError("HealthRecord", record_id)
        
        return record
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting health record", record_id=record_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=HealthRecordResponse)
async def create_health_record(
    record_data: HealthRecordCreate,
    db: Session = Depends(get_db)
):
    """Create a new health record"""
    try:
        # Validate cat exists
        cat = db.query(Cat).filter(Cat.id == record_data.cat_id).first()
        if not cat:
            raise NotFoundError("Cat", record_data.cat_id)
        
        # Create health record
        record = HealthRecord(
            cat_id=record_data.cat_id,
            record_type=record_data.record_type,
            value=record_data.value,
            unit=record_data.unit,
            notes=record_data.notes,
            appetite_level=record_data.appetite_level,
            activity_level=record_data.activity_level,
            mood=record_data.mood,
            energy_level=record_data.energy_level,
            weight=record_data.weight,
            body_condition_score=record_data.body_condition_score,
            coat_condition=record_data.coat_condition,
            eye_condition=record_data.eye_condition,
            ear_condition=record_data.ear_condition,
            behavior_notes=record_data.behavior_notes,
            recorded_at=datetime.now(),
            recorded_by="user"
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return record
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error creating health record", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{record_id}", response_model=HealthRecordResponse)
async def update_health_record(
    record_id: str,
    record_data: HealthRecordUpdate,
    db: Session = Depends(get_db)
):
    """Update health record"""
    try:
        record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
        if not record:
            raise NotFoundError("HealthRecord", record_id)
        
        # Update fields
        update_data = record_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        record.updated_at = datetime.now()
        
        db.commit()
        db.refresh(record)
        
        return record
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error updating health record", record_id=record_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{record_id}")
async def delete_health_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """Delete a health record"""
    try:
        record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
        if not record:
            raise NotFoundError("HealthRecord", record_id)
        
        db.delete(record)
        db.commit()
        
        return {"message": "Health record deleted successfully"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error deleting health record", record_id=record_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cats/{cat_id}/trends")
async def get_health_trends(
    cat_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get health trends for a cat"""
    try:
        from datetime import timedelta
        
        # Validate cat exists
        cat = db.query(Cat).filter(Cat.id == cat_id).first()
        if not cat:
            raise NotFoundError("Cat", cat_id)
        
        # Get health records
        records = db.query(HealthRecord).filter(
            HealthRecord.cat_id == cat_id,
            HealthRecord.created_at >= datetime.now() - timedelta(days=days)
        ).order_by(HealthRecord.recorded_at).all()
        
        # Calculate trends
        trends = {
            "weight_trend": "stable",
            "activity_trend": "stable",
            "appetite_trend": "stable",
            "health_score_trend": "stable"
        }
        
        # Weight trend
        weight_records = [r for r in records if r.record_type == "weight" and r.value]
        if len(weight_records) >= 2:
            recent_weight = weight_records[-1].value
            older_weight = weight_records[0].value
            weight_change = (recent_weight - older_weight) / older_weight
            
            if weight_change > 0.05:
                trends["weight_trend"] = "increasing"
            elif weight_change < -0.05:
                trends["weight_trend"] = "decreasing"
        
        # Activity trend
        activity_records = [r for r in records if r.activity_level is not None]
        if len(activity_records) >= 2:
            recent_activity = activity_records[-1].activity_level
            older_activity = activity_records[0].activity_level
            
            if recent_activity > older_activity + 1:
                trends["activity_trend"] = "increasing"
            elif recent_activity < older_activity - 1:
                trends["activity_trend"] = "decreasing"
        
        # Appetite trend
        appetite_records = [r for r in records if r.appetite_level is not None]
        if len(appetite_records) >= 2:
            recent_appetite = appetite_records[-1].appetite_level
            older_appetite = appetite_records[0].appetite_level
            
            if recent_appetite > older_appetite + 1:
                trends["appetite_trend"] = "improving"
            elif recent_appetite < older_appetite - 1:
                trends["appetite_trend"] = "declining"
        
        return {
            "cat_id": cat_id,
            "analysis_period_days": days,
            "total_records": len(records),
            "trends": trends,
            "latest_health_score": records[-1].ai_health_score if records else None,
            "generated_at": datetime.now().isoformat()
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting health trends", cat_id=cat_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
