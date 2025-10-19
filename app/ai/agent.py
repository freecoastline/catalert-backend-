"""
Main AI Agent for CatAlert application
"""
from typing import Dict, Any, List, Optional
import json
import uuid
import structlog
from datetime import datetime, timedelta

from app.ai.llm_service import LLMService
from app.ai.tools import CatCareTools
from app.core.exceptions import AIAgentError
from app.models import AIInteraction, AIInsight

logger = structlog.get_logger()


class CatAlertAgent:
    """Main AI Agent for CatAlert application"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.llm_service = LLMService()
        self.tools = CatCareTools(db_session)
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI Agent"""
        return """
        你是CatAlert的智能猫咪护理助手，具有以下专业能力：
        
        1. 健康监测：分析猫咪的日常数据，识别健康异常和趋势
        2. 行为分析：理解猫咪的行为模式，提供个性化建议
        3. 提醒优化：根据猫咪和主人的习惯优化提醒时间
        4. 异常检测：识别异常行为模式并发出预警
        5. 个性化推荐：基于猫咪特点提供定制化护理建议
        
        你的工作原则：
        - 基于数据事实进行分析，避免主观臆测
        - 提供具体可操作的建议
        - 保持专业和友好的语调
        - 在不确定时建议咨询专业兽医
        - 优先考虑猫咪的健康和福祉
        
        你可以使用以下工具：
        - get_cat_data: 获取猫咪的详细数据
        - create_reminder: 创建新的护理提醒
        - analyze_health_trend: 分析健康趋势
        - get_recent_activities: 获取最近的活动记录
        - update_activity_status: 更新活动状态
        - create_health_record: 创建健康记录
        """
    
    async def process_user_request(
        self,
        user_id: str,
        cat_id: str,
        user_input: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user request and generate response"""
        try:
            start_time = datetime.now()
            
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Classify request type
            request_type = await self._classify_request(user_input)
            
            # Build context
            context = await self._build_context(cat_id, user_input)
            
            # Process based on request type
            if request_type == "simple_query":
                response = await self._handle_simple_query(user_input, context, cat_id)
            elif request_type == "complex_analysis":
                response = await self._handle_complex_analysis(user_input, context, cat_id)
            elif request_type == "reminder_management":
                response = await self._handle_reminder_management(user_input, context, cat_id)
            elif request_type == "health_consultation":
                response = await self._handle_health_consultation(user_input, context, cat_id)
            else:
                response = await self._handle_general_query(user_input, context, cat_id)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Store interaction
            await self._store_interaction(
                user_id=user_id,
                cat_id=cat_id,
                session_id=session_id,
                interaction_type=request_type,
                user_input=user_input,
                ai_response=response["message"],
                context=context,
                processing_time_ms=int(processing_time)
            )
            
            return {
                "success": True,
                "message": response["message"],
                "type": request_type,
                "session_id": session_id,
                "processing_time_ms": int(processing_time),
                "suggestions": response.get("suggestions", []),
                "insights": response.get("insights", [])
            }
            
        except Exception as e:
            logger.error("Error processing user request", error=str(e))
            return {
                "success": False,
                "message": f"处理请求时发生错误：{str(e)}",
                "type": "error"
            }
    
    async def _classify_request(self, user_input: str) -> str:
        """Classify the type of user request"""
        classification_prompt = f"""
        将以下用户请求分类为以下类型之一：
        1. simple_query - 简单查询（如"今天喂了几次？"、"胡胡的体重是多少？"）
        2. complex_analysis - 复杂分析（如"分析胡胡的健康状况"、"最近有什么异常吗？"）
        3. reminder_management - 提醒管理（如"帮我设置喂食提醒"、"调整提醒时间"）
        4. health_consultation - 健康咨询（如"胡胡最近不爱吃饭怎么办？"、"需要看兽医吗？"）
        5. general - 一般对话
        
        用户请求：{user_input}
        
        只返回类型名称，不要其他内容。
        """
        
        messages = [
            {"role": "user", "content": classification_prompt}
        ]
        
        response = await self.llm_service.chat_completion(messages)
        return response["content"].strip().lower()
    
    async def _build_context(self, cat_id: str, user_input: str) -> Dict[str, Any]:
        """Build context for the request"""
        try:
            # Get cat data
            cat_data = self.tools.get_cat_data(cat_id)
            
            # Get recent activities
            recent_activities = self.tools.get_recent_activities(cat_id, days=7)
            
            # Get health trends
            health_trends = self.tools.analyze_health_trend(cat_id, days=30)
            
            return {
                "cat_data": cat_data,
                "recent_activities": recent_activities,
                "health_trends": health_trends,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning("Failed to build context", error=str(e))
            return {"error": str(e)}
    
    async def _handle_simple_query(
        self,
        user_input: str,
        context: Dict[str, Any],
        cat_id: str
    ) -> Dict[str, Any]:
        """Handle simple queries"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""
            用户问题：{user_input}
            
            猫咪数据：
            {json.dumps(context.get('cat_data', {}), ensure_ascii=False, indent=2)}
            
            请基于数据回答用户问题，提供准确、简洁的回答。
            """}
        ]
        
        response = await self.llm_service.chat_completion(messages)
        
        return {
            "message": response["content"],
            "type": "simple_query"
        }
    
    async def _handle_complex_analysis(
        self,
        user_input: str,
        context: Dict[str, Any],
        cat_id: str
    ) -> Dict[str, Any]:
        """Handle complex analysis requests"""
        # Use LLM to analyze the data
        analysis = await self.llm_service.analyze_cat_behavior(context.get('cat_data', {}))
        
        # Generate insights
        insights = await self._generate_insights(cat_id, analysis)
        
        # Format response
        response_message = f"""
        基于数据分析，我为您提供以下洞察：
        
        📊 健康评分：{analysis.get('health_score', 0.7):.1%}
        
        🔍 主要发现：
        {chr(10).join([f"• {finding}" for finding in analysis.get('key_findings', [])])}
        
        ⚠️ 风险因素：
        {chr(10).join([f"• {risk}" for risk in analysis.get('risk_factors', [])])}
        
        💡 建议：
        {chr(10).join([f"• {rec}" for rec in analysis.get('recommendations', [])])}
        """
        
        return {
            "message": response_message,
            "type": "complex_analysis",
            "insights": insights,
            "analysis_data": analysis
        }
    
    async def _handle_reminder_management(
        self,
        user_input: str,
        context: Dict[str, Any],
        cat_id: str
    ) -> Dict[str, Any]:
        """Handle reminder management requests"""
        # Get current reminders
        cat_data = context.get('cat_data', {})
        
        # Generate reminder suggestions
        suggestions = await self.llm_service.generate_reminder_suggestions(
            cat_data,
            {"available_times": "全天", "frequency_preference": "适中"}
        )
        
        response_message = f"""
        基于{cat_data.get('name', '您的猫咪')}的情况，我建议以下提醒设置：
        
        {chr(10).join([f"• {s['title']} - {s['reason']}" for s in suggestions])}
        
        您希望我帮您创建这些提醒吗？
        """
        
        return {
            "message": response_message,
            "type": "reminder_management",
            "suggestions": suggestions
        }
    
    async def _handle_health_consultation(
        self,
        user_input: str,
        context: Dict[str, Any],
        cat_id: str
    ) -> Dict[str, Any]:
        """Handle health consultation requests"""
        # Analyze for potential health issues
        cat_data = context.get('cat_data', {})
        health_trends = context.get('health_trends', {})
        
        # Check for urgent issues
        urgent_issues = []
        if cat_data.get('statistics', {}).get('completion_rate', 1) < 0.5:
            urgent_issues.append("任务完成率显著下降，可能存在健康问题")
        
        if health_trends.get('trends', {}).get('weight_trend') == 'decreasing':
            urgent_issues.append("体重持续下降，建议尽快咨询兽医")
        
        if urgent_issues:
            response_message = f"""
            ⚠️ 检测到以下需要关注的问题：
            
            {chr(10).join([f"• {issue}" for issue in urgent_issues])}
            
            建议您：
            1. 密切观察猫咪的行为变化
            2. 记录详细的症状和异常
            3. 尽快联系专业兽医进行咨询
            
            如果情况紧急，请立即联系24小时宠物医院。
            """
        else:
            response_message = """
            根据当前数据分析，您的猫咪健康状况良好。
            
            建议继续维持现有的护理计划，并定期观察猫咪的行为变化。
            如有任何异常情况，请及时咨询专业兽医。
            """
        
        return {
            "message": response_message,
            "type": "health_consultation",
            "urgent_issues": urgent_issues
        }
    
    async def _handle_general_query(
        self,
        user_input: str,
        context: Dict[str, Any],
        cat_id: str
    ) -> Dict[str, Any]:
        """Handle general queries"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self.llm_service.chat_completion(messages)
        
        return {
            "message": response["content"],
            "type": "general"
        }
    
    async def _generate_insights(self, cat_id: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI insights based on analysis"""
        insights = []
        
        # Health score insight
        health_score = analysis.get('health_score', 0.7)
        if health_score < 0.6:
            insights.append({
                "type": "health",
                "title": "健康评分偏低",
                "description": f"当前健康评分为{health_score:.1%}，建议关注猫咪的健康状况",
                "priority": "high",
                "actionable": True
            })
        
        # Risk factors insights
        risk_factors = analysis.get('risk_factors', [])
        for risk in risk_factors:
            insights.append({
                "type": "risk",
                "title": f"风险因素：{risk}",
                "description": f"检测到风险因素：{risk}，建议采取相应措施",
                "priority": "medium",
                "actionable": True
            })
        
        return insights
    
    async def _store_interaction(
        self,
        user_id: str,
        cat_id: str,
        session_id: str,
        interaction_type: str,
        user_input: str,
        ai_response: str,
        context: Dict[str, Any],
        processing_time_ms: int
    ):
        """Store AI interaction in database"""
        try:
            interaction = AIInteraction(
                user_id=user_id,
                cat_id=cat_id,
                session_id=session_id,
                interaction_type=interaction_type,
                user_input=user_input,
                ai_response=ai_response,
                context=context,
                processing_time_ms=processing_time_ms,
                model_used=self.llm_service.model
            )
            
            self.db.add(interaction)
            self.db.commit()
            
        except Exception as e:
            logger.error("Failed to store interaction", error=str(e))
            self.db.rollback()
    
    async def generate_daily_insights(self, cat_id: str) -> List[Dict[str, Any]]:
        """Generate daily insights for a cat"""
        try:
            # Get cat data and recent activities
            cat_data = self.tools.get_cat_data(cat_id)
            recent_activities = self.tools.get_recent_activities(cat_id, days=1)
            health_trends = self.tools.analyze_health_trend(cat_id, days=7)
            
            # Generate insights using LLM
            insights_data = await self.llm_service.generate_health_insights(
                cat_id, {
                    "cat_data": cat_data,
                    "recent_activities": recent_activities,
                    "health_trends": health_trends
                }, "1d"
            )
            
            # Create insight records
            insights = []
            for insight_data in insights_data.get('recommendations', []):
                insight = AIInsight(
                    cat_id=cat_id,
                    insight_type="daily",
                    title=insight_data.get('title', '每日洞察'),
                    description=insight_data.get('description', ''),
                    confidence_score=insight_data.get('confidence', 0.8),
                    analysis_period="1d",
                    recommendations=insight_data.get('actions', []),
                    priority=insight_data.get('priority', 'medium'),
                    expires_at=datetime.now() + timedelta(days=1)
                )
                
                self.db.add(insight)
                insights.append(insight)
            
            self.db.commit()
            return insights
            
        except Exception as e:
            logger.error("Failed to generate daily insights", cat_id=cat_id, error=str(e))
            self.db.rollback()
            return []
