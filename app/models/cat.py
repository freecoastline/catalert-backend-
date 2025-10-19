"""
Cat model for CatAlert application
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Cat(Base):
    """Cat model - extends iOS CatModel"""
    __tablename__ = "cats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Basic information (from iOS CatModel)
    name = Column(String(100), nullable=False)
    gender = Column(String(10))  # "male", "female"
    breed = Column(String(100))  # "British short", etc.
    description = Column(Text)
    born_way = Column(String(50))  # "Breed", "Adopted", etc.
    
    # Extended information
    birth_date = Column(DateTime(timezone=True))
    weight = Column(Float)  # in kg
    color = Column(String(50))
    microchip_id = Column(String(50), unique=True)
    
    # Health information
    health_condition = Column(String(20), default="good")  # "excellent", "good", "fair", "poor"
    medical_notes = Column(Text)
    vaccination_records = Column(JSONB)
    
    # Images (stored as URLs or file paths)
    images = Column(JSONB)  # List of image URLs/paths
    avatar_url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User", back_populates="cats")
    reminders = relationship("Reminder", back_populates="cat", cascade="all, delete-orphan")
    activities = relationship("ActivityRecord", back_populates="cat", cascade="all, delete-orphan")
    health_records = relationship("HealthRecord", back_populates="cat", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cat(id={self.id}, name={self.name}, owner_id={self.owner_id})>"
    
    @property
    def age_in_months(self):
        """Calculate age in months"""
        if not self.birth_date:
            return None
        from datetime import datetime
        now = datetime.now()
        return (now.year - self.birth_date.year) * 12 + (now.month - self.birth_date.month)
    
    @property
    def age_in_years(self):
        """Calculate age in years"""
        if not self.birth_date:
            return None
        from datetime import datetime
        now = datetime.now()
        return now.year - self.birth_date.year
