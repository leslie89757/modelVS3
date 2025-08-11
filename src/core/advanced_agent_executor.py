"""高级Agent执行引擎"""

import json
import asyncio
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from ..models_advanced import (
    AdvancedAgent, AgentSession, SessionMessage, AdvancedTool,
    AgentMemory, AgentKnowledgeBase, AdvancedAgentStatus
)
from ..models import Model
from .llm_adapters import llm_factory
from .advanced_tool_executor import AdvancedToolExecutor
from .advanced_memory_manager import AdvancedMemoryManager

logger = logging.getLogger(__name__)


class AdvancedAgentExecutor:
    """高级Agent执行引擎"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.tool_executor = AdvancedToolExecutor(db)
        self.memory_manager = AdvancedMemoryManager(db)
    
    async def process_message(
        self,
        agent: AdvancedAgent,
        session: AgentSession,
        message: str,
        message_history: List[Dict[str, Any]],
        include_reasoning: bool = True,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """处理用户消息，返回Agent响应"""
        
        try:
            # 获取Agent配置
            config = agent.config or {}
            autonomy_level = config.get("autonomy_level", "semi_autonomous")
            transparency = config.get("transparency", "high")
            memory_enabled = config.get("memory_enabled", True)
            
            # 获取模型配置
            model_id = config.get("primary_model")
            if not model_id:
                raise ValueError("Agent没有配置主要模型")
            
            model_config = await self._get_model_config(model_id)
            
            # 获取LLM适配器
            llm_adapter = await llm_factory.get_adapter(
                model_name=model_config["name"],
                endpoint=model_config["endpoint"],
                provider=model_config["provider"],
                api_key=model_config.get("api_key"),
                custom_headers=model_config.get("custom_headers")
            )
            
            # 准备对话上下文
            context = await self._prepare_context(agent, session, message_history, memory_enabled)
            
            # 执行ReAct循环
            result = await self._execute_react_loop(
                agent=agent,
                session=session,
                llm_adapter=llm_adapter,
                user_message=message,
                context=context,
                max_iterations=max_iterations,
                include_reasoning=include_reasoning,
                autonomy_level=autonomy_level
            )
            
            # 更新记忆（如果启用）
            if memory_enabled:
                await self._update_memory(agent, session, message, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Agent处理消息失败: {e}")
            return {
                "content": f"抱歉，处理您的请求时遇到错误: {str(e)}",
                "confidence": 0.1,
                "reasoning": f"系统错误: {str(e)}" if include_reasoning else None,
                "tool_calls": None,
                "metadata": {"error": True, "error_message": str(e)},
                "tokens_used": 0,
                "cost": 0.0
            }
    
    async def _execute_react_loop(
        self,
        agent: AdvancedAgent,
        session: AgentSession,
        llm_adapter: Any,
        user_message: str,
        context: Dict[str, Any],
        max_iterations: int,
        include_reasoning: bool,
        autonomy_level: str
    ) -> Dict[str, Any]:
        """执行ReAct推理循环"""
        
        iteration = 0
        total_tokens = 0
        total_cost = 0.0
        reasoning_steps = []
        tool_calls = []
        confidence_scores = []
        
        # 构建初始提示词
        system_prompt = self._build_system_prompt(agent, context, autonomy_level)
        
        # 初始化消息历史
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息
        for msg in context.get("recent_messages", []):
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 添加当前用户消息
        messages.append({
            "role": "user", 
            "content": user_message
        })
        
        while iteration < max_iterations:
            iteration += 1
            
            # 更新会话状态
            if self.db:
                session.current_step = f"推理循环 {iteration}/{max_iterations}"
                session.progress = int((iteration / max_iterations) * 80)  # 80%为推理进度
                self.db.commit()
            
            try:
                # 调用LLM进行推理
                logger.info(f"Agent {agent.name} - 推理循环 {iteration}")
                
                # 根据自主水平调整提示
                if autonomy_level == "guided":
                    prompt_suffix = "\n\n请逐步思考并明确说明每个步骤。如果需要使用工具，请详细说明原因。"
                elif autonomy_level == "semi_autonomous":
                    prompt_suffix = "\n\n请思考解决方案并在需要时使用适当的工具。"
                else:  # autonomous
                    prompt_suffix = "\n\n请自主分析并执行必要的操作来完成任务。"
                
                current_messages = messages + [{
                    "role": "user",
                    "content": f"当前是第{iteration}轮推理。{prompt_suffix}"
                }]
                
                # 获取可用工具
                available_tools = await self._get_available_tools(agent)
                
                response = await llm_adapter.chat_completion(
                    messages=current_messages,
                    temperature=0.7,
                    max_tokens=2000,
                    tools=available_tools if available_tools else None
                )
                
                total_tokens += response.get("usage", {}).get("total_tokens", 0)
                total_cost += response.get("cost", 0.0)
                
                # 解析响应
                content = response.get("content", "")
                tool_calls_in_response = response.get("tool_calls", [])
                
                # 记录推理步骤
                reasoning_step = {
                    "iteration": iteration,
                    "thought": content,
                    "tool_calls": tool_calls_in_response,
                    "timestamp": datetime.now().isoformat()
                }
                reasoning_steps.append(reasoning_step)
                
                # 添加助手响应到对话历史
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls_in_response
                })
                
                # 计算信心度
                confidence = self._calculate_confidence(content, tool_calls_in_response, iteration, max_iterations)
                confidence_scores.append(confidence)
                
                # 如果有工具调用，执行工具
                if tool_calls_in_response:
                    logger.info(f"执行 {len(tool_calls_in_response)} 个工具调用")
                    
                    for tool_call in tool_calls_in_response:
                        try:
                            # 执行工具
                            tool_result = await self.tool_executor.execute_tool(
                                tool_name=tool_call["function"]["name"],
                                parameters=json.loads(tool_call["function"]["arguments"]),
                                agent_id=str(agent.id)
                            )
                            
                            # 记录工具调用
                            tool_call_record = {
                                "id": tool_call["id"],
                                "name": tool_call["function"]["name"],
                                "arguments": json.loads(tool_call["function"]["arguments"]),
                                "result": tool_result,
                                "status": "success" if tool_result.get("success") else "error",
                                "execution_time": tool_result.get("execution_time", 0)
                            }
                            tool_calls.append(tool_call_record)
                            
                            # 添加工具结果到对话历史
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                            
                        except Exception as e:
                            logger.error(f"工具执行失败: {e}")
                            # 记录工具执行失败
                            tool_call_record = {
                                "id": tool_call["id"],
                                "name": tool_call["function"]["name"],
                                "arguments": json.loads(tool_call["function"]["arguments"]),
                                "result": {"error": str(e)},
                                "status": "error",
                                "execution_time": 0
                            }
                            tool_calls.append(tool_call_record)
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": f"工具执行失败: {str(e)}"
                            })
                    
                    # 如果是引导模式，在工具执行后暂停等待确认
                    if autonomy_level == "guided" and self.db:
                        session.current_step = "等待用户确认工具执行结果"
                        self.db.commit()
                
                else:
                    # 没有工具调用，检查是否已完成任务
                    if self._is_task_completed(content, iteration):
                        logger.info(f"任务完成于第{iteration}轮")
                        break
                
            except Exception as e:
                logger.error(f"推理循环第{iteration}轮失败: {e}")
                reasoning_steps.append({
                    "iteration": iteration,
                    "thought": f"推理失败: {str(e)}",
                    "error": True,
                    "timestamp": datetime.now().isoformat()
                })
                break
        
        # 生成最终响应
        final_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # 构建最终内容
        if reasoning_steps:
            last_step = reasoning_steps[-1]
            final_content = last_step.get("thought", "处理完成")
        else:
            final_content = "抱歉，无法处理您的请求。"
        
        # 构建推理过程总结
        reasoning_summary = None
        if include_reasoning and reasoning_steps:
            reasoning_summary = self._build_reasoning_summary(reasoning_steps, tool_calls)
        
        # 更新最终进度
        if self.db:
            session.current_step = "完成"
            session.progress = 100
            session.confidence_score = final_confidence
            self.db.commit()
        
        return {
            "content": final_content,
            "confidence": final_confidence,
            "reasoning": reasoning_summary,
            "tool_calls": tool_calls if tool_calls else None,
            "metadata": {
                "iterations": iteration,
                "total_reasoning_steps": len(reasoning_steps),
                "total_tool_calls": len(tool_calls),
                "autonomy_level": autonomy_level
            },
            "tokens_used": total_tokens,
            "cost": total_cost
        }
    
    def _build_system_prompt(self, agent: AdvancedAgent, context: Dict[str, Any], autonomy_level: str) -> str:
        """构建系统提示词"""
        
        # 获取角色信息
        from ..schemas_advanced import AGENT_ROLES
        role_info = next((r for r in AGENT_ROLES if r["id"] == agent.role), None)
        role_name = role_info["name"] if role_info else "AI助手"
        role_desc = role_info["description"] if role_info else "智能助手"
        
        # 基础提示词
        prompt = f"""你是{role_name}，{role_desc}。

个性特点: {agent.personality}
用户对你的期望: {agent.description or '提供专业的帮助和建议'}

你的工作方式:
"""
        
        # 根据自主水平调整提示
        if autonomy_level == "guided":
            prompt += """
- 每一步都要详细说明你的思考过程
- 在使用任何工具前都要明确说明原因和目的
- 等待用户确认后再继续下一步
- 保持谨慎，避免做出可能影响用户的决策
"""
        elif autonomy_level == "semi_autonomous":
            prompt += """
- 可以自主分析问题并制定解决方案
- 在关键决策点会询问用户意见
- 使用工具时会说明目的和预期结果
- 在不确定时会寻求用户指导
"""
        else:  # autonomous
            prompt += """
- 完全自主分析和解决问题
- 根据需要选择和使用适当的工具
- 专注于高效完成用户的目标
- 在遇到重大问题时才会寻求帮助
"""
        
        # 添加记忆信息
        if context.get("relevant_memories"):
            prompt += f"\n\n相关记忆信息:\n{context['relevant_memories']}"
        
        # 添加知识库信息
        if context.get("knowledge_base"):
            prompt += f"\n\n专业知识:\n{context['knowledge_base']}"
        
        # 添加可用工具信息
        if context.get("available_tools"):
            prompt += f"\n\n可用工具: {', '.join(context['available_tools'])}"
        
        prompt += f"""

请始终保持{agent.personality}的风格，用中文回复用户。
当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return prompt
    
    def _calculate_confidence(self, content: str, tool_calls: List[Dict], iteration: int, max_iterations: int) -> float:
        """计算信心度"""
        
        confidence = 0.5  # 基础信心度
        
        # 根据内容长度调整
        if len(content) > 100:
            confidence += 0.1
        if len(content) > 300:
            confidence += 0.1
        
        # 根据工具使用情况调整
        if tool_calls:
            confidence += 0.2  # 使用工具通常意味着更详细的处理
        
        # 根据迭代轮次调整
        if iteration <= max_iterations * 0.5:
            confidence += 0.1  # 早期完成任务通常意味着明确的解决方案
        
        # 检查是否包含不确定性词汇
        uncertainty_words = ["可能", "也许", "大概", "不确定", "不清楚", "可能需要"]
        for word in uncertainty_words:
            if word in content:
                confidence -= 0.1
                break
        
        # 检查是否包含肯定性词汇
        certainty_words = ["确定", "明确", "清楚", "肯定", "完成", "已解决"]
        for word in certainty_words:
            if word in content:
                confidence += 0.1
                break
        
        # 限制在0.1-1.0之间
        return max(0.1, min(1.0, confidence))
    
    def _is_task_completed(self, content: str, iteration: int) -> bool:
        """判断任务是否完成"""
        
        # 检查完成标志词
        completion_indicators = [
            "完成", "结束", "已解决", "已处理", "搞定", 
            "没有其他", "已经回答", "希望有帮助", "还有其他问题吗"
        ]
        
        for indicator in completion_indicators:
            if indicator in content:
                return True
        
        # 如果没有工具调用且内容较长，可能是最终回答
        if "工具" not in content and len(content) > 150:
            return True
        
        # 超过一定轮次且没有明确的下一步计划
        if iteration >= 5 and not any(word in content for word in ["接下来", "然后", "下一步", "需要"]):
            return True
        
        return False
    
    def _build_reasoning_summary(self, reasoning_steps: List[Dict], tool_calls: List[Dict]) -> str:
        """构建推理过程总结"""
        
        summary_parts = []
        
        # 添加思考过程
        summary_parts.append("🧠 思考过程:")
        for i, step in enumerate(reasoning_steps, 1):
            if not step.get("error"):
                summary_parts.append(f"{i}. {step['thought'][:100]}{'...' if len(step['thought']) > 100 else ''}")
        
        # 添加工具使用
        if tool_calls:
            summary_parts.append("\n🛠️ 工具使用:")
            for tool_call in tool_calls:
                status_icon = "✅" if tool_call["status"] == "success" else "❌"
                summary_parts.append(f"{status_icon} {tool_call['name']}: {tool_call.get('execution_time', 0)}ms")
        
        return "\n".join(summary_parts)
    
    async def _prepare_context(
        self, 
        agent: AdvancedAgent, 
        session: AgentSession, 
        message_history: List[Dict[str, Any]], 
        memory_enabled: bool
    ) -> Dict[str, Any]:
        """准备对话上下文"""
        
        context = {
            "recent_messages": message_history[-10:],  # 最近10条消息
            "available_tools": [],
            "relevant_memories": None,
            "knowledge_base": None
        }
        
        # 获取可用工具列表
        if self.db:
            tools = self.db.query(AdvancedTool).filter(
                AdvancedTool.enabled == True
            ).all()
            
            # 筛选Agent配置的工具
            agent_tools = agent.config.get("tools", [])
            available_tools = []
            
            for tool in tools:
                if tool.name in agent_tools:
                    available_tools.append(tool.name)
            
            context["available_tools"] = available_tools
        
        # 获取相关记忆
        if memory_enabled and self.db:
            try:
                memories = await self.memory_manager.get_relevant_memories(
                    agent_id=str(agent.id),
                    query=message_history[-1]["content"] if message_history else "",
                    limit=5
                )
                
                if memories:
                    memory_text = "\n".join([f"- {mem['content']}" for mem in memories])
                    context["relevant_memories"] = memory_text
            except Exception as e:
                logger.warning(f"获取记忆失败: {e}")
        
        # 获取知识库信息
        if agent.config.get("knowledge_base_enabled") and self.db:
            try:
                knowledge_items = self.db.query(AgentKnowledgeBase).filter(
                    AgentKnowledgeBase.agent_id == agent.id
                ).limit(5).all()
                
                if knowledge_items:
                    knowledge_text = "\n".join([f"- {item.title}: {item.content[:200]}..." for item in knowledge_items])
                    context["knowledge_base"] = knowledge_text
            except Exception as e:
                logger.warning(f"获取知识库失败: {e}")
        
        return context
    
    async def _get_available_tools(self, agent: AdvancedAgent) -> Optional[List[Dict[str, Any]]]:
        """获取Agent可用的工具定义"""
        
        if not self.db:
            return None
        
        agent_tools = agent.config.get("tools", [])
        if not agent_tools:
            return None
        
        tools = self.db.query(AdvancedTool).filter(
            AdvancedTool.name.in_(agent_tools),
            AdvancedTool.enabled == True
        ).all()
        
        tool_definitions = []
        for tool in tools:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.schema
                }
            }
            tool_definitions.append(tool_def)
        
        return tool_definitions if tool_definitions else None
    
    async def _get_model_config(self, model_id: str) -> Dict[str, Any]:
        """获取模型配置"""
        
        if not self.db:
            raise ValueError("数据库连接未初始化")
        
        model = self.db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise ValueError(f"模型不存在: {model_id}")
        
        return {
            "id": str(model.id),
            "name": model.name,
            "provider": model.provider,
            "endpoint": model.endpoint,
            "api_key": model.api_key,
            "custom_headers": model.custom_headers
        }
    
    async def _update_memory(
        self, 
        agent: AdvancedAgent, 
        session: AgentSession, 
        user_message: str, 
        agent_response: Dict[str, Any]
    ):
        """更新Agent记忆"""
        
        try:
            # 保存对话记忆
            await self.memory_manager.save_conversation_memory(
                agent_id=str(agent.id),
                session_id=str(session.id),
                user_message=user_message,
                agent_response=agent_response["content"],
                confidence=agent_response.get("confidence", 0.5)
            )
            
            # 如果使用了工具，保存技能记忆
            if agent_response.get("tool_calls"):
                for tool_call in agent_response["tool_calls"]:
                    if tool_call["status"] == "success":
                        await self.memory_manager.save_skill_memory(
                            agent_id=str(agent.id),
                            tool_name=tool_call["name"],
                            usage_context=user_message,
                            success=True
                        )
        
        except Exception as e:
            logger.warning(f"更新记忆失败: {e}") 