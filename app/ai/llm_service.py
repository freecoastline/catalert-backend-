"""
LLM Service for CatAlert AI Agent
"""
import openai
from typing import List, Dict, Any, Optional
import json
import time
import structlog

from app.core.config import settings
from app.core.exceptions import AIAgentError, ExternalServiceError

logger = structlog.get_logger()


class LLMService:
    """Large Language Model service for AI Agent"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.AI_AGENT_MODEL
        self.max_tokens = settings.AI_AGENT_MAX_TOKENS
        self.temperature = settings.AI_AGENT_TEMPERATURE
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """Perform chat completion with optional tool calling"""
        try:
            start_time = time.time()
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = tool_choice
            
            # Make API call
            response = self.client.chat.completions.create(**request_params)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Extract response
            choice = response.choices[0]
            result = {
                "content": choice.message.content,
                "role": choice.message.role,
                "tool_calls": choice.message.tool_calls,
                "finish_reason": choice.finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "processing_time_ms": int(processing_time)
            }
            
            logger.info(
                "LLM API call completed",
                model=self.model,
                tokens_used=result["usage"]["total_tokens"],
                processing_time_ms=result["processing_time_ms"]
            )
            
            return result
            
        except openai.APIError as e:
            logger.error("OpenAI API error", error=str(e))
            raise ExternalServiceError("OpenAI", str(e))
        except Exception as e:
            logger.error("LLM service error", error=str(e))
            raise AIAgentError(f"LLM service error: {str(e)}")
    
    async def analyze_cat_behavior(self, cat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cat behavior data using LLM"""
        prompt = f"""
        作为专业的猫咪健康顾问，请分析以下猫咪数据并提供专业建议：
        
        猫咪基本信息：
        - 姓名：{cat_data.get('name', '未知')}
        - 年龄：{cat_data.get('age', '未知')}岁
        - 品种：{cat_data.get('breed', '未知')}
        - 体重：{cat_data.get('weight', '未知')}kg
        
        最近7天活动数据：
        - 平均喂食次数：{cat_data.get('avg_feeding_frequency', 0)}次/天
        - 平均活动时长：{cat_data.get('avg_activity_duration', 0)}分钟/天
        - 任务完成率：{cat_data.get('completion_rate', 0):.1%}
        - 异常行为次数：{cat_data.get('anomaly_count', 0)}次
        
        请从以下角度进行分析：
        1. 整体健康状况评估
        2. 行为模式分析
        3. 潜在健康风险识别
        4. 具体改进建议
        5. 是否需要兽医咨询
        
        请以JSON格式返回分析结果，包含health_score(0-1)、risk_factors、recommendations等字段。
        """
        
        messages = [
            {"role": "system", "content": "你是一位专业的猫咪健康顾问，具有10年兽医经验。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages)
        
        try:
            # Parse JSON response
            analysis = json.loads(response["content"])
            return analysis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "health_score": 0.7,
                "risk_factors": [],
                "recommendations": [response["content"]],
                "requires_vet_consultation": False
            }
    
    async def generate_reminder_suggestions(
        self,
        cat_data: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized reminder suggestions"""
        prompt = f"""
        基于以下信息，为猫咪生成个性化的护理提醒建议：
        
        猫咪信息：
        - 年龄：{cat_data.get('age', '未知')}岁
        - 品种：{cat_data.get('breed', '未知')}
        - 健康状况：{cat_data.get('health_condition', '良好')}
        
        用户偏好：
        - 可用时间：{user_preferences.get('available_times', '全天')}
        - 提醒频率偏好：{user_preferences.get('frequency_preference', '适中')}
        - 特殊需求：{user_preferences.get('special_needs', '无')}
        
        请生成3-5个具体的提醒建议，包括：
        1. 提醒类型（喂食、换水、玩耍等）
        2. 建议时间
        3. 频率
        4. 理由说明
        
        以JSON数组格式返回，每个建议包含title、type、suggested_times、frequency、reason字段。
        """
        
        messages = [
            {"role": "system", "content": "你是猫咪护理专家，擅长制定个性化的护理计划。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages)
        
        try:
            suggestions = json.loads(response["content"])
            return suggestions
        except json.JSONDecodeError:
            return []
    
    async def detect_anomalies(self, activity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in cat activity data"""
        prompt = f"""
        分析以下猫咪活动数据，识别异常模式：
        
        活动数据：
        {json.dumps(activity_data, ensure_ascii=False, indent=2)}
        
        请识别以下类型的异常：
        1. 时间模式异常（如喂食时间突然改变）
        2. 频率异常（如活动频率显著下降）
        3. 行为异常（如完成率突然下降）
        4. 健康相关异常（如食欲不振、活动减少）
        
        以JSON格式返回异常检测结果，包含anomalies数组，每个异常包含type、severity、description、suggested_action字段。
        """
        
        messages = [
            {"role": "system", "content": "你是数据分析专家，擅长识别宠物行为中的异常模式。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages)
        
        try:
            result = json.loads(response["content"])
            return result.get("anomalies", [])
        except json.JSONDecodeError:
            return []
    
    async def generate_health_insights(
        self,
        cat_id: str,
        health_data: Dict[str, Any],
        time_period: str = "30d"
    ) -> Dict[str, Any]:
        """Generate health insights for a cat"""
        prompt = f"""
        基于{time_period}的健康数据，为猫咪生成健康洞察报告：
        
        健康数据：
        {json.dumps(health_data, ensure_ascii=False, indent=2)}
        
        请生成包含以下内容的洞察报告：
        1. 健康趋势分析
        2. 关键指标变化
        3. 风险因素识别
        4. 改进建议
        5. 下一步行动建议
        
        以JSON格式返回，包含trends、key_metrics、risk_factors、recommendations、next_actions字段。
        """
        
        messages = [
            {"role": "system", "content": "你是专业的宠物健康分析师，擅长解读健康数据并提供专业建议。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages)
        
        try:
            insights = json.loads(response["content"])
            return insights
        except json.JSONDecodeError:
            return {
                "trends": [],
                "key_metrics": {},
                "risk_factors": [],
                "recommendations": [],
                "next_actions": []
            }
