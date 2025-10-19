"""
Health record models for CatAlert application
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class HealthRecord(Base):
    """Health record model for tracking cat health"""
    __tablename__ = "health_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id = Column(UUID(as_uuid=True), ForeignKey("cats.id"), nullable=False)
    
    # Basic health information
    record_type = Column(String(50), nullable=False)  # "weight", "temperature", "vaccination", etc.
    value = Column(Float)  # numeric value
    unit = Column(String(20))  # "kg", "°C", "ml", etc.
    notes = Column(Text)
    
    # Health indicators
    appetite_level = Column(Integer)  # 1-5 scale
    activity_level = Column(Integer)  # 1-5 scale
    mood = Column(String(50))  # "happy", "lethargic", "aggressive", etc.
    energy_level = Column(Integer)  # 1-5 scale
    
    # Physical observations
    weight = Column(Float)  # in kg
    body_condition_score = Column(Integer)  # 1-9 scale
    coat_condition = Column(String(50))  # "excellent", "good", "poor"
    eye_condition = Column(String(50))
    ear_condition = Column(String(50))
    
    # Behavioral observations
    behavior_notes = Column(Text)
    unusual_behaviors = Column(JSONB)  # list of unusual behaviors
    stress_indicators = Column(JSONB)  # stress-related observations
    
    # AI analysis
    ai_health_score = Column(Float)  # 0.0-1.0 overall health score
    ai_risk_factors = Column(JSONB)  # identified risk factors
    ai_recommendations = Column(JSONB)  # AI-generated recommendations
    anomaly_detected = Column(Boolean, default=False)
    
    # Metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    recorded_by = Column(String(100))  # "user", "ai", "vet"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cat = relationship("Cat", back_populates="health_records")
    
    def __repr__(self):
        return f"<HealthRecord(id={self.id}, cat_id={self.cat_id}, type={self.record_type})>"
    
    @property
    def health_status(self):
        """Get overall health status based on AI score"""
        if self.ai_health_score is None:
            return "unknown"
        elif self.ai_health_score >= 0.8:
            return "excellent"
        elif self.ai_health_score >= 0.6:
            return "good"
        elif self.ai_health_score >= 0.4:
            return "fair"
        else:
            return "poor"
