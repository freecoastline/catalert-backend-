"""
AI Agent Tools for CatAlert application
"""
from typing import Dict, Any, List, Optional
import json
import structlog
from datetime import datetime, timedelta

from app.core.exceptions import AIAgentError
from app.models import Cat, Reminder, ActivityRecord, HealthRecord

logger = structlog.get_logger()


class CatCareTools:
    """Tools available to the AI Agent"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_cat_data(self, cat_id: str) -> Dict[str, Any]:
        """Get comprehensive cat data"""
        try:
            cat = self.db.query(Cat).filter(Cat.id == cat_id).first()
            if not cat:
                raise AIAgentError(f"Cat with id {cat_id} not found")
            
            # Get recent activities
            recent_activities = self.db.query(ActivityRecord).filter(
                ActivityRecord.cat_id == cat_id,
                ActivityRecord.created_at >= datetime.now() - timedelta(days=7)
            ).all()
            
            # Get health records
            health_records = self.db.query(HealthRecord).filter(
                HealthRecord.cat_id == cat_id,
                HealthRecord.created_at >= datetime.now() - timedelta(days=30)
            ).all()
            
            # Calculate statistics
            total_activities = len(recent_activities)
            completed_activities = len([a for a in recent_activities if a.status.value == "completed"])
            completion_rate = completed_activities / total_activities if total_activities > 0 else 0
            
            # Calculate average activity duration
            durations = [a.actual_duration for a in recent_activities if a.actual_duration]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "id": str(cat.id),
                "name": cat.name,
                "age": cat.age_in_years,
                "breed": cat.breed,
                "weight": cat.weight,
                "health_condition": cat.health_condition,
                "recent_activities": [
                    {
                        "type": a.type.value,
                        "scheduled_time": a.scheduled_time.isoformat(),
                        "status": a.status.value,
                        "duration": a.actual_duration
                    }
                    for a in recent_activities
                ],
                "health_records": [
                    {
                        "type": h.record_type,
                        "value": h.value,
                        "unit": h.unit,
                        "recorded_at": h.recorded_at.isoformat()
                    }
                    for h in health_records
                ],
                "statistics": {
                    "total_activities_7d": total_activities,
                    "completion_rate": completion_rate,
                    "avg_activity_duration": avg_duration,
                    "health_records_30d": len(health_records)
                }
            }
        except Exception as e:
            logger.error("Error getting cat data", cat_id=cat_id, error=str(e))
            raise AIAgentError(f"Failed to get cat data: {str(e)}")
    
    def create_reminder(
        self,
        cat_id: str,
        title: str,
        reminder_type: str,
        times: List[str],
        frequency: str = "daily",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new reminder for a cat"""
        try:
            from app.models import ReminderFrequency, CatCareType, ReminderTime
            
            # Validate cat exists
            cat = self.db.query(Cat).filter(Cat.id == cat_id).first()
            if not cat:
                raise AIAgentError(f"Cat with id {cat_id} not found")
            
            # Create reminder
            reminder = Reminder(
                cat_id=cat_id,
                title=title,
                type=CatCareType(reminder_type),
                frequency=ReminderFrequency(frequency),
                description=description,
                is_enabled=True
            )
            
            self.db.add(reminder)
            self.db.flush()  # Get the ID
            
            # Create reminder times
            for time_str in times:
                try:
                    hour, minute = map(int, time_str.split(":"))
                    reminder_time = ReminderTime(
                        reminder_id=reminder.id,
                        hour=hour,
                        minute=minute
                    )
                    self.db.add(reminder_time)
                except ValueError:
                    logger.warning("Invalid time format", time_str=time_str)
                    continue
            
            self.db.commit()
            
            return {
                "id": str(reminder.id),
                "title": reminder.title,
                "type": reminder.type.value,
                "frequency": reminder.frequency.value,
                "times": times,
                "created_at": reminder.created_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating reminder", error=str(e))
            raise AIAgentError(f"Failed to create reminder: {str(e)}")
    
    def analyze_health_trend(self, cat_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze health trends for a cat"""
        try:
            # Get health records
            health_records = self.db.query(HealthRecord).filter(
                HealthRecord.cat_id == cat_id,
                HealthRecord.created_at >= datetime.now() - timedelta(days=days)
            ).order_by(HealthRecord.recorded_at).all()
            
            # Get activity records
            activity_records = self.db.query(ActivityRecord).filter(
                ActivityRecord.cat_id == cat_id,
                ActivityRecord.created_at >= datetime.now() - timedelta(days=days)
            ).all()
            
            # Calculate trends
            trends = self._calculate_health_trends(health_records, activity_records)
            
            return {
                "cat_id": cat_id,
                "analysis_period_days": days,
                "health_records_count": len(health_records),
                "activity_records_count": len(activity_records),
                "trends": trends,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Error analyzing health trend", cat_id=cat_id, error=str(e))
            raise AIAgentError(f"Failed to analyze health trend: {str(e)}")
    
    def get_recent_activities(self, cat_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent activities for a cat"""
        try:
            activities = self.db.query(ActivityRecord).filter(
                ActivityRecord.cat_id == cat_id,
                ActivityRecord.created_at >= datetime.now() - timedelta(days=days)
            ).order_by(ActivityRecord.scheduled_time.desc()).all()
            
            return [
                {
                    "id": str(a.id),
                    "type": a.type.value,
                    "scheduled_time": a.scheduled_time.isoformat(),
                    "complete_time": a.complete_time.isoformat() if a.complete_time else None,
                    "status": a.status.value,
                    "duration": a.actual_duration,
                    "notes": a.notes,
                    "quality_rating": a.quality_rating
                }
                for a in activities
            ]
        except Exception as e:
            logger.error("Error getting recent activities", cat_id=cat_id, error=str(e))
            raise AIAgentError(f"Failed to get recent activities: {str(e)}")
    
    def update_activity_status(
        self,
        activity_id: str,
        status: str,
        notes: Optional[str] = None,
        quality_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update activity status"""
        try:
            from app.models import ActivityStatus
            
            activity = self.db.query(ActivityRecord).filter(
                ActivityRecord.id == activity_id
            ).first()
            
            if not activity:
                raise AIAgentError(f"Activity with id {activity_id} not found")
            
            activity.status = ActivityStatus(status)
            if status == "completed":
                activity.complete_time = datetime.now()
            if notes:
                activity.notes = notes
            if quality_rating:
                activity.quality_rating = quality_rating
            
            self.db.commit()
            
            return {
                "id": str(activity.id),
                "status": activity.status.value,
                "complete_time": activity.complete_time.isoformat() if activity.complete_time else None,
                "updated_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating activity status", activity_id=activity_id, error=str(e))
            raise AIAgentError(f"Failed to update activity status: {str(e)}")
    
    def create_health_record(
        self,
        cat_id: str,
        record_type: str,
        value: Optional[float] = None,
        unit: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a health record"""
        try:
            health_record = HealthRecord(
                cat_id=cat_id,
                record_type=record_type,
                value=value,
                unit=unit,
                notes=notes,
                recorded_at=datetime.now()
            )
            
            self.db.add(health_record)
            self.db.commit()
            
            return {
                "id": str(health_record.id),
                "record_type": health_record.record_type,
                "value": health_record.value,
                "unit": health_record.unit,
                "recorded_at": health_record.recorded_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating health record", error=str(e))
            raise AIAgentError(f"Failed to create health record: {str(e)}")
    
    def _calculate_health_trends(
        self,
        health_records: List[HealthRecord],
        activity_records: List[ActivityRecord]
    ) -> Dict[str, Any]:
        """Calculate health trends from records"""
        trends = {
            "weight_trend": "stable",
            "activity_trend": "stable",
            "completion_rate_trend": "stable",
            "health_score_trend": "stable"
        }
        
        # Calculate weight trend
        weight_records = [r for r in health_records if r.record_type == "weight" and r.value]
        if len(weight_records) >= 2:
            recent_weight = weight_records[-1].value
            older_weight = weight_records[0].value
            weight_change = (recent_weight - older_weight) / older_weight
            
            if weight_change > 0.05:
                trends["weight_trend"] = "increasing"
            elif weight_change < -0.05:
                trends["weight_trend"] = "decreasing"
        
        # Calculate activity trend
        if len(activity_records) >= 7:
            recent_activities = activity_records[-7:]
            older_activities = activity_records[:7]
            
            recent_avg_duration = sum(a.actual_duration or 0 for a in recent_activities) / len(recent_activities)
            older_avg_duration = sum(a.actual_duration or 0 for a in older_activities) / len(older_activities)
            
            if recent_avg_duration > older_avg_duration * 1.1:
                trends["activity_trend"] = "increasing"
            elif recent_avg_duration < older_avg_duration * 0.9:
                trends["activity_trend"] = "decreasing"
        
        # Calculate completion rate trend
        if len(activity_records) >= 14:
            recent_activities = activity_records[-7:]
            older_activities = activity_records[-14:-7]
            
            recent_completion = len([a for a in recent_activities if a.status.value == "completed"]) / len(recent_activities)
            older_completion = len([a for a in older_activities if a.status.value == "completed"]) / len(older_activities)
            
            if recent_completion > older_completion + 0.1:
                trends["completion_rate_trend"] = "improving"
            elif recent_completion < older_completion - 0.1:
                trends["completion_rate_trend"] = "declining"
        
        return trends
