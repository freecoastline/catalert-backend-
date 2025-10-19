"""
Cats API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models import Cat, User
import structlog

logger = structlog.get_logger()
router = APIRouter()


class CatCreate(BaseModel):
    """Cat creation model"""
    name: str
    gender: Optional[str] = None
    breed: Optional[str] = None
    description: Optional[str] = None
    birth_date: Optional[datetime] = None
    weight: Optional[float] = None
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    health_condition: str = "good"
    medical_notes: Optional[str] = None


class CatUpdate(BaseModel):
    """Cat update model"""
    name: Optional[str] = None
    gender: Optional[str] = None
    breed: Optional[str] = None
    description: Optional[str] = None
    birth_date: Optional[datetime] = None
    weight: Optional[float] = None
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    health_condition: Optional[str] = None
    medical_notes: Optional[str] = None


class CatResponse(BaseModel):
    """Cat response model"""
    id: str
    name: str
    gender: Optional[str]
    breed: Optional[str]
    description: Optional[str]
    birth_date: Optional[datetime]
    weight: Optional[float]
    color: Optional[str]
    microchip_id: Optional[str]
    health_condition: str
    medical_notes: Optional[str]
    age_in_years: Optional[int]
    age_in_months: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CatResponse])
async def get_cats(
    owner_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of cats"""
    try:
        query = db.query(Cat).filter(Cat.is_active == True)
        
        if owner_id:
            query = query.filter(Cat.owner_id == owner_id)
        
        cats = query.offset(skip).limit(limit).all()
        
        return cats
        
    except Exception as e:
        logger.error("Error getting cats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{cat_id}", response_model=CatResponse)
async def get_cat(
    cat_id: str,
    db: Session = Depends(get_db)
):
    """Get cat by ID"""
    try:
        cat = db.query(Cat).filter(Cat.id == cat_id, Cat.is_active == True).first()
        if not cat:
            raise NotFoundError("Cat", cat_id)
        
        return cat
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting cat", cat_id=cat_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=CatResponse)
async def create_cat(
    cat_data: CatCreate,
    owner_id: str,
    db: Session = Depends(get_db)
):
    """Create a new cat"""
    try:
        # Validate owner exists
        owner = db.query(User).filter(User.id == owner_id).first()
        if not owner:
            raise NotFoundError("User", owner_id)
        
        # Create cat
        cat = Cat(
            owner_id=owner_id,
            name=cat_data.name,
            gender=cat_data.gender,
            breed=cat_data.breed,
            description=cat_data.description,
            birth_date=cat_data.birth_date,
            weight=cat_data.weight,
            color=cat_data.color,
            microchip_id=cat_data.microchip_id,
            health_condition=cat_data.health_condition,
            medical_notes=cat_data.medical_notes
        )
        
        db.add(cat)
        db.commit()
        db.refresh(cat)
        
        return cat
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error creating cat", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{cat_id}", response_model=CatResponse)
async def update_cat(
    cat_id: str,
    cat_data: CatUpdate,
    db: Session = Depends(get_db)
):
    """Update cat information"""
    try:
        cat = db.query(Cat).filter(Cat.id == cat_id, Cat.is_active == True).first()
        if not cat:
            raise NotFoundError("Cat", cat_id)
        
        # Update fields
        update_data = cat_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cat, field, value)
        
        cat.updated_at = datetime.now()
        
        db.commit()
        db.refresh(cat)
        
        return cat
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error updating cat", cat_id=cat_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{cat_id}")
async def delete_cat(
    cat_id: str,
    db: Session = Depends(get_db)
):
    """Delete a cat (soft delete)"""
    try:
        cat = db.query(Cat).filter(Cat.id == cat_id, Cat.is_active == True).first()
        if not cat:
            raise NotFoundError("Cat", cat_id)
        
        # Soft delete
        cat.is_active = False
        cat.updated_at = datetime.now()
        
        db.commit()
        
        return {"message": "Cat deleted successfully"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error deleting cat", cat_id=cat_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{cat_id}/stats")
async def get_cat_stats(
    cat_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get cat statistics"""
    try:
        cat = db.query(Cat).filter(Cat.id == cat_id, Cat.is_active == True).first()
        if not cat:
            raise NotFoundError("Cat", cat_id)
        
        from app.models import ActivityRecord, HealthRecord
        from datetime import timedelta
        
        # Get recent activities
        recent_activities = db.query(ActivityRecord).filter(
            ActivityRecord.cat_id == cat_id,
            ActivityRecord.created_at >= datetime.now() - timedelta(days=days)
        ).all()
        
        # Get health records
        health_records = db.query(HealthRecord).filter(
            HealthRecord.cat_id == cat_id,
            HealthRecord.created_at >= datetime.now() - timedelta(days=days)
        ).all()
        
        # Calculate statistics
        total_activities = len(recent_activities)
        completed_activities = len([a for a in recent_activities if a.status.value == "completed"])
        completion_rate = completed_activities / total_activities if total_activities > 0 else 0
        
        # Calculate average activity duration
        durations = [a.actual_duration for a in recent_activities if a.actual_duration]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "cat_id": cat_id,
            "period_days": days,
            "statistics": {
                "total_activities": total_activities,
                "completed_activities": completed_activities,
                "completion_rate": completion_rate,
                "avg_activity_duration_minutes": avg_duration,
                "health_records_count": len(health_records)
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting cat stats", cat_id=cat_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
