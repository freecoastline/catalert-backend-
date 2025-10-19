"""
AI interaction models for CatAlert application
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AIInteraction(Base):
    """AI interaction model for tracking user-AI conversations"""
    __tablename__ = "ai_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cat_id = Column(UUID(as_uuid=True), ForeignKey("cats.id"))
    
    # Interaction details
    session_id = Column(String(100), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False)  # "chat", "analysis", "recommendation"
    user_input = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    # Context and metadata
    context = Column(JSONB)  # additional context data
    intent = Column(String(100))  # detected user intent
    confidence_score = Column(Float)  # AI confidence in response
    processing_time_ms = Column(Integer)  # response time in milliseconds
    
    # AI model information
    model_used = Column(String(100))  # "gpt-4", "gpt-3.5-turbo", etc.
    tokens_used = Column(Integer)
    cost = Column(Float)  # estimated cost in USD
    
    # User feedback
    user_rating = Column(Integer)  # 1-5 rating
    user_feedback = Column(Text)
    was_helpful = Column(Boolean)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ai_interactions")
    cat = relationship("Cat")
    
    def __repr__(self):
        return f"<AIInteraction(id={self.id}, type={self.interaction_type}, user_id={self.user_id})>"
    
    @property
    def response_quality(self):
        """Get response quality based on user feedback"""
        if self.user_rating is None:
            return "unknown"
        elif self.user_rating >= 4:
            return "excellent"
        elif self.user_rating >= 3:
            return "good"
        elif self.user_rating >= 2:
            return "fair"
        else:
            return "poor"


class AIInsight(Base):
    """AI insight model for storing generated insights"""
    __tablename__ = "ai_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id = Column(UUID(as_uuid=True), ForeignKey("cats.id"), nullable=False)
    
    # Insight details
    insight_type = Column(String(50), nullable=False)  # "health", "behavior", "pattern", "recommendation"
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float)  # 0.0-1.0
    
    # Data analysis
    analysis_period = Column(String(50))  # "7d", "30d", "90d"
    data_points_analyzed = Column(Integer)
    key_findings = Column(JSONB)
    supporting_evidence = Column(JSONB)
    
    # Recommendations
    recommendations = Column(JSONB)  # list of recommendations
    priority = Column(String(20))  # "low", "medium", "high", "urgent"
    actionable = Column(Boolean, default=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    user_notes = Column(Text)
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # when insight becomes stale
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cat = relationship("Cat")
    
    def __repr__(self):
        return f"<AIInsight(id={self.id}, type={self.insight_type}, cat_id={self.cat_id})>"
    
    @property
    def is_expired(self):
        """Check if insight is expired"""
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.now() > self.expires_at
