"""
AI Agent API endpoints
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import AIAgentError, NotFoundError
from app.ai.agent import CatAlertAgent
from app.models import User, Cat
import structlog

logger = structlog.get_logger()
router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    user_id: str
    cat_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    success: bool
    message: str
    type: str
    session_id: str
    processing_time_ms: int
    suggestions: List[Dict[str, Any]] = []
    insights: List[Dict[str, Any]] = []


class InsightRequest(BaseModel):
    """Insight generation request model"""
    cat_id: str
    analysis_period: str = "7d"  # 1d, 7d, 30d


class InsightResponse(BaseModel):
    """Insight response model"""
    success: bool
    insights: List[Dict[str, Any]]
    generated_at: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with AI Agent"""
    try:
        # Validate user and cat exist
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise NotFoundError("User", request.user_id)
        
        cat = db.query(Cat).filter(Cat.id == request.cat_id).first()
        if not cat:
            raise NotFoundError("Cat", request.cat_id)
        
        # Initialize AI Agent
        agent = CatAlertAgent(db)
        
        # Process request
        result = await agent.process_user_request(
            user_id=request.user_id,
            cat_id=request.cat_id,
            user_input=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(**result)
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AIAgentError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Chat endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/insights", response_model=InsightResponse)
async def generate_insights(
    request: InsightRequest,
    db: Session = Depends(get_db)
):
    """Generate AI insights for a cat"""
    try:
        # Validate cat exists
        cat = db.query(Cat).filter(Cat.id == request.cat_id).first()
        if not cat:
            raise NotFoundError("Cat", request.cat_id)
        
        # Initialize AI Agent
        agent = CatAlertAgent(db)
        
        # Generate insights based on period
        if request.analysis_period == "1d":
            insights = await agent.generate_daily_insights(request.cat_id)
        else:
            # For other periods, use health trend analysis
            from app.ai.tools import CatCareTools
            tools = CatCareTools(db)
            days = int(request.analysis_period[:-1])  # Remove 'd' suffix
            health_trends = tools.analyze_health_trend(request.cat_id, days)
            
            insights = [{
                "type": "health_trend",
                "title": f"{request.analysis_period}健康趋势分析",
                "description": f"基于{request.analysis_period}数据的健康趋势分析",
                "data": health_trends,
                "priority": "medium"
            }]
        
        return InsightResponse(
            success=True,
            insights=[{
                "id": str(insight.id) if hasattr(insight, 'id') else None,
                "type": insight.insight_type if hasattr(insight, 'insight_type') else insight.get('type'),
                "title": insight.title if hasattr(insight, 'title') else insight.get('title'),
                "description": insight.description if hasattr(insight, 'description') else insight.get('description'),
                "priority": insight.priority if hasattr(insight, 'priority') else insight.get('priority'),
                "generated_at": insight.generated_at.isoformat() if hasattr(insight, 'generated_at') else None
            } for insight in insights],
            generated_at=datetime.now().isoformat()
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Insights endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cats/{cat_id}/analysis")
async def get_cat_analysis(
    cat_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get comprehensive cat analysis"""
    try:
        # Validate cat exists
        cat = db.query(Cat).filter(Cat.id == cat_id).first()
        if not cat:
            raise NotFoundError("Cat", cat_id)
        
        # Initialize AI Agent
        agent = CatAlertAgent(db)
        
        # Build context
        context = await agent._build_context(cat_id, "comprehensive analysis")
        
        # Perform analysis
        analysis = await agent.llm_service.analyze_cat_behavior(context.get('cat_data', {}))
        
        return {
            "success": True,
            "cat_id": cat_id,
            "analysis_period_days": days,
            "analysis": analysis,
            "context": context,
            "generated_at": datetime.now().isoformat()
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Analysis endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cats/{cat_id}/reminders/suggest")
async def suggest_reminders(
    cat_id: str,
    user_preferences: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Get AI-suggested reminders for a cat"""
    try:
        # Validate cat exists
        cat = db.query(Cat).filter(Cat.id == cat_id).first()
        if not cat:
            raise NotFoundError("Cat", cat_id)
        
        # Initialize AI Agent
        agent = CatAlertAgent(db)
        
        # Get cat data
        cat_data = agent.tools.get_cat_data(cat_id)
        
        # Generate suggestions
        suggestions = await agent.llm_service.generate_reminder_suggestions(
            cat_data, user_preferences
        )
        
        return {
            "success": True,
            "cat_id": cat_id,
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Reminder suggestions endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health-check")
async def health_check():
    """AI service health check"""
    return {
        "status": "healthy",
        "service": "AI Agent",
        "timestamp": datetime.now().isoformat()
    }
