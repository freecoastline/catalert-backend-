"""
Activity models for CatAlert application
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class ActivityStatus(enum.Enum):
    """Activity status enum"""
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ActivityRecord(Base):
    """Activity record model - extends iOS ActivityRecord"""
    __tablename__ = "activity_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reminder_id = Column(UUID(as_uuid=True), ForeignKey("reminders.id"), nullable=False)
    cat_id = Column(UUID(as_uuid=True), ForeignKey("cats.id"), nullable=False)
    
    # Basic information (from iOS ActivityRecord)
    type = Column(Enum(CatCareType), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    complete_time = Column(DateTime(timezone=True))
    status = Column(Enum(ActivityStatus), default=ActivityStatus.PENDING)
    
    # Extended information
    actual_duration = Column(Integer)  # actual duration in minutes
    notes = Column(Text)
    quality_rating = Column(Integer)  # 1-5 rating
    cat_behavior = Column(String(100))  # "cooperative", "resistant", etc.
    
    # AI analysis
    ai_analysis = Column(JSONB)  # AI analysis results
    anomaly_detected = Column(Boolean, default=False)
    health_indicators = Column(JSONB)  # health-related observations
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reminder = relationship("Reminder", back_populates="activities")
    cat = relationship("Cat", back_populates="activities")
    
    def __repr__(self):
        return f"<ActivityRecord(id={self.id}, type={self.type.value}, status={self.status.value})>"
    
    @property
    def type_string(self):
        """Get display name for activity type"""
        type_map = {
            CatCareType.FOOD: "喂食",
            CatCareType.WATER: "换水",
            CatCareType.PLAY: "玩耍",
            CatCareType.MEDICATION: "喂药",
            CatCareType.VET_VISIT: "看兽医",
            CatCareType.GROOMING: "美容"
        }
        return type_map.get(self.type, "未知")
    
    @property
    def is_overdue(self):
        """Check if activity is overdue"""
        if self.status != ActivityStatus.PENDING:
            return False
        from datetime import datetime
        return datetime.now() > self.scheduled_time
    
    @property
    def completion_delay_minutes(self):
        """Get completion delay in minutes"""
        if not self.complete_time or not self.scheduled_time:
            return None
        return (self.complete_time - self.scheduled_time).total_seconds() / 60
