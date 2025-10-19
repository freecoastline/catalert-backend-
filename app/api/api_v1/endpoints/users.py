"""
Users API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models import User, Cat
import structlog

logger = structlog.get_logger()
router = APIRouter()


class UserCreate(BaseModel):
    """User creation model"""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    timezone: str = "UTC"
    language: str = "zh-CN"


class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    notification_enabled: Optional[bool] = None
    ai_agent_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    timezone: str
    language: str
    notification_enabled: bool
    ai_agent_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        return user
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    try:
        # Check if username or email already exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists"
            )
        
        # Hash password (in production, use proper password hashing)
        hashed_password = f"hashed_{user_data.password}"  # Simplified for demo
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            timezone=user_data.timezone,
            language=user_data.language
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error creating user", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user information"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now()
        
        db.commit()
        db.refresh(user)
        
        return user
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error("Error updating user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}/cats")
async def get_user_cats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get cats owned by a user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)
        
        cats = db.query(Cat).filter(
            Cat.owner_id == user_id,
            Cat.is_active == True
        ).all()
        
        return {
            "user_id": user_id,
            "cats": [
                {
                    "id": str(cat.id),
                    "name": cat.name,
                    "breed": cat.breed,
                    "health_condition": cat.health_condition,
                    "created_at": cat.created_at.isoformat()
                }
                for cat in cats
            ],
            "total_count": len(cats)
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting user cats", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
