"""
Reminder models for CatAlert application
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class ReminderFrequency(enum.Enum):
    """Reminder frequency enum"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class CatCareType(enum.Enum):
    """Cat care type enum"""
    FOOD = "food"
    WATER = "water"
    PLAY = "play"
    MEDICATION = "medication"
    VET_VISIT = "vet_visit"
    GROOMING = "grooming"


class ReminderTime(Base):
    """Reminder time model"""
    __tablename__ = "reminder_times"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reminder_id = Column(UUID(as_uuid=True), ForeignKey("reminders.id"), nullable=False)
    hour = Column(Integer, nullable=False)  # 0-23
    minute = Column(Integer, nullable=False)  # 0-59
    day_of_week = Column(Integer)  # 0-6 (Monday-Sunday), None for daily
    is_enabled = Column(Boolean, default=True)
    
    # Relationships
    reminder = relationship("Reminder", back_populates="scheduled_times")
    
    def __repr__(self):
        return f"<ReminderTime(id={self.id}, time={self.hour:02d}:{self.minute:02d})>"


class Reminder(Base):
    """Reminder model - extends iOS CatReminder"""
    __tablename__ = "reminders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id = Column(UUID(as_uuid=True), ForeignKey("cats.id"), nullable=False)
    
    # Basic information (from iOS CatReminder)
    title = Column(String(200), nullable=False)
    type = Column(Enum(CatCareType), nullable=False)
    frequency = Column(Enum(ReminderFrequency), default=ReminderFrequency.DAILY)
    is_enabled = Column(Boolean, default=True)
    
    # Extended information
    description = Column(Text)
    priority = Column(Integer, default=1)  # 1-5 priority level
    estimated_duration = Column(Integer)  # in minutes
    
    # AI optimization
    ai_optimized = Column(Boolean, default=False)
    optimal_times = Column(JSONB)  # AI suggested optimal times
    completion_rate = Column(Float, default=0.0)  # 0.0-1.0
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered = Column(DateTime(timezone=True))
    
    # Relationships
    cat = relationship("Cat", back_populates="reminders")
    scheduled_times = relationship("ReminderTime", back_populates="reminder", cascade="all, delete-orphan")
    activities = relationship("ActivityRecord", back_populates="reminder")
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, title={self.title}, type={self.type.value})>"
    
    @property
    def display_frequency(self):
        """Get display name for frequency"""
        frequency_map = {
            ReminderFrequency.DAILY: "每天",
            ReminderFrequency.WEEKLY: "每周", 
            ReminderFrequency.MONTHLY: "每月",
            ReminderFrequency.CUSTOM: "自定义"
        }
        return frequency_map.get(self.frequency, "未知")
    
    @property
    def display_type(self):
        """Get display name for care type"""
        type_map = {
            CatCareType.FOOD: "喂食",
            CatCareType.WATER: "喂水",
            CatCareType.PLAY: "玩耍",
            CatCareType.MEDICATION: "喂药",
            CatCareType.VET_VISIT: "看兽医",
            CatCareType.GROOMING: "美容"
        }
        return type_map.get(self.type, "未知")
