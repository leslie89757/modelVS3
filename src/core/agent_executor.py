"""Agent 执行引擎"""

import json
import asyncio
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import yaml
import logging
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Agent, Run, Message, RunStatus, Model
from ..schemas import RunRequest
from .llm_adapters import llm_factory
from .tool_executor import ToolExecutor
from .memory import MemoryManager

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Agent 执行引擎"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.tool_executor = ToolExecutor()
        self.memory_manager = MemoryManager()
    
    async def execute_agent(
        self, 
        agent: Agent, 
        run_request: RunRequest,
        db_run: Run
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行 Agent"""
        
        try:
            # 解析 Agent 配置
            llm_config = agent.llm_config if isinstance(agent.llm_config, dict) else {}
            system_config = agent.system_config if isinstance(agent.system_config, dict) else {}
            tools_config = agent.tools_config if isinstance(agent.tools_config, dict) else {}
            
            # 获取模型配置（支持模型覆盖）
            # 优先使用请求中指定的模型，否则使用Agent配置的主要模型
            request_model_id = getattr(run_request, 'model_id', None)
            logger.info(f"🔍 请求中的model_id: {request_model_id}")
            logger.info(f"🔍 Agent配置中的primary_model_id: {llm_config.get('primary_model_id')}")
            
            if request_model_id:
                # 使用指定的模型ID（多模型对比测试）
                model_id = request_model_id
                logger.info(f"🎯 使用请求指定的模型: {model_id}")
            else:
                # 使用Agent配置的默认模型
                model_id = llm_config.get("primary_model_id")
                if not model_id:
                    raise ValueError("Agent 没有配置主要模型")
                logger.info(f"🎯 使用Agent默认模型: {model_id}")
            
            model_config = await self._get_model_config(model_id)
            
            # 获取 LLM 适配器
            llm_adapter = await llm_factory.get_adapter(
                model_name=model_config["name"],
                endpoint=model_config["endpoint"],
                provider=model_config["provider"],
                api_key=model_config.get("api_key"),
                custom_headers=model_config.get("custom_headers")
            )
            
            # 初始化对话历史
            messages = await self._prepare_messages(agent, run_request, str(db_run.id))
            
            # 执行推理循环
            max_iterations = system_config.get("max_context_turns", 6)
            current_iteration = 0
            run_start_time = time.time()  # 记录整个执行的开始时间
            
            while current_iteration < max_iterations:
                current_iteration += 1
                
                yield {
                    "type": "iteration_start",
                    "iteration": current_iteration,
                    "model": model_config["name"],
                    "provider": model_config["provider"],
                    "timestamp": datetime.now().isoformat()
                }
                
                # 调用 LLM
                start_time = time.time()
                
                try:
                    # 从临时配置、用户请求或 Agent 配置中获取参数
                    temp_config = getattr(run_request, 'temporary_config', None)
                    
                    # 安全获取临时配置参数
                    temp_temperature = getattr(temp_config, 'temperature', None) if temp_config else None
                    temp_max_tokens = getattr(temp_config, 'max_tokens', None) if temp_config else None
                    temp_top_p = getattr(temp_config, 'top_p', None) if temp_config else None
                    temp_frequency_penalty = getattr(temp_config, 'frequency_penalty', None) if temp_config else None
                    temp_presence_penalty = getattr(temp_config, 'presence_penalty', None) if temp_config else None
                    
                    request_params = {
                        "temperature": temp_temperature or run_request.temperature or llm_config.get("temperature", 0.7),
                        "max_tokens": temp_max_tokens or run_request.max_tokens or llm_config.get("max_tokens", 2000),
                        "top_p": temp_top_p or llm_config.get("top_p", 0.9),
                        "frequency_penalty": temp_frequency_penalty or llm_config.get("frequency_penalty", 0),
                        "presence_penalty": temp_presence_penalty or llm_config.get("presence_penalty", 0)
                    }
                    
                    # 获取工具列表（支持临时覆盖）
                    effective_tools_config = tools_config.copy()
                    temp_enabled_tools = getattr(temp_config, 'enabled_tools', None) if temp_config else None
                    
                    if temp_enabled_tools is not None:
                        # 使用临时配置的工具列表覆盖原始配置
                        effective_tools_config["enabled_tools"] = temp_enabled_tools
                        logger.info(f"🔧 使用临时工具配置: {temp_enabled_tools}")
                    
                    available_tools = await self._get_available_tools(effective_tools_config)
                    logger.info(f"🔧 工具配置: {tools_config}")
                    logger.info(f"📋 可用工具数量: {len(available_tools)}")
                    for tool in available_tools:
                        tool_name = tool.get("function", {}).get("name", "unknown")
                        logger.info(f"   - 工具: {tool_name}")
                    
                    logger.info(f"📨 调用LLM适配器，消息数量: {len(messages)}")
                    logger.info(f"💬 最后一条消息: {messages[-1] if messages else 'None'}")
                    
                    response = await llm_adapter.chat_completion(
                        messages=messages,
                        temperature=request_params["temperature"],
                        max_tokens=request_params["max_tokens"],
                        top_p=request_params.get("top_p"),
                        frequency_penalty=request_params.get("frequency_penalty"),
                        presence_penalty=request_params.get("presence_penalty"),
                        tools=available_tools
                    )
                    logger.info(f"🤖 LLM响应: {response}")
                    
                    # 检查响应中的工具调用
                    if response.get("tool_calls"):
                        logger.info(f"🔧 检测到工具调用: {len(response['tool_calls'])} 个")
                        for i, tool_call in enumerate(response["tool_calls"]):
                            logger.info(f"   工具调用 {i+1}: {tool_call.get('function', {}).get('name', 'unknown')}")
                    else:
                        logger.info("ℹ️  没有工具调用")
                    
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    yield {
                        "type": "llm_response",
                        "response": response,
                        "execution_time_ms": execution_time,
                        "model": response.get("model", model_config["name"]),
                        "usage": response.get("usage", {}),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # 添加助手回复到消息历史
                    assistant_message = {
                        "role": "assistant",
                        "content": response.get("content"),
                        "tool_calls": response.get("tool_calls")
                    }
                    messages.append(assistant_message)
                    
                    # 保存助手消息到数据库
                    if self.db:
                        from ..models import Message
                        db_message = Message(
                            run_id=db_run.id,
                            role="assistant",
                            content=response.get("content"),
                            tool_calls=response.get("tool_calls")
                        )
                        self.db.add(db_message)
                        self.db.commit()
                    
                    # 检查是否有工具调用
                    if response.get("tool_calls"):
                        # 执行工具调用
                        for tool_call in response["tool_calls"]:
                            start_time = int(time.time() * 1000)  # 毫秒时间戳
                            
                            # 发送工具调用开始事件
                            yield {
                                "type": "tool_call_start",
                                "tool_call": {
                                    **tool_call,
                                    "status": "running",
                                    "startTime": start_time
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            try:
                                # 执行Function Call工具
                                tool_name = tool_call["function"]["name"]
                                tool_args = json.loads(tool_call["function"]["arguments"])
                                
                                # 如果tool_name是UUID，需要映射到工具名称
                                actual_tool_name = await self._resolve_tool_name(tool_name)
                                
                                # 使用ToolExecutor执行工具
                                tool_result = await self.tool_executor.execute_tool(actual_tool_name, tool_args)
                                logger.info(f"✅ 使用ToolExecutor执行工具: {actual_tool_name} (原名: {tool_name})")
                                
                                end_time = int(time.time() * 1000)  # 毫秒时间戳
                                
                                # 发送工具调用成功事件
                                yield {
                                    "type": "tool_call_result",
                                    "tool_call": {
                                        **tool_call,
                                        "status": "success",
                                        "startTime": start_time,
                                        "endTime": end_time,
                                        "result": tool_result
                                    },
                                    "tool_call_id": tool_call["id"],
                                    "result": tool_result,
                                    "execution_time_ms": end_time - start_time,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # 添加工具结果到消息历史
                                # 提取可读的结果内容，避免JSON编码导致中文乱码
                                if isinstance(tool_result, dict) and "result" in tool_result:
                                    tool_content = tool_result["result"]
                                else:
                                    tool_content = str(tool_result)
                                
                                tool_message = {
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": tool_content
                                }
                                messages.append(tool_message)
                                
                                # 保存工具消息到数据库
                                if self.db:
                                    from ..models import Message
                                    db_tool_message = Message(
                                        run_id=db_run.id,
                                        role="tool",
                                        content=tool_content,  # 使用相同的可读内容
                                        tool_call_id=tool_call["id"]
                                    )
                                    self.db.add(db_tool_message)
                                    self.db.commit()
                                    logger.info(f"💾 已保存工具消息到数据库: {tool_call['id'][:8]}")
                                
                            except Exception as e:
                                logger.error(f"工具执行失败: {e}")
                                end_time = int(time.time() * 1000)  # 毫秒时间戳
                                
                                # 发送工具调用错误事件
                                yield {
                                    "type": "tool_call_error",
                                    "tool_call": {
                                        **tool_call,
                                        "status": "error",
                                        "startTime": start_time,
                                        "endTime": end_time,
                                        "error": str(e)
                                    },
                                    "tool_call_id": tool_call["id"],
                                    "error": str(e),
                                    "execution_time_ms": end_time - start_time,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # 添加错误信息到消息历史
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": f"工具执行失败: {str(e)}"
                                })
                    else:
                        # 没有工具调用，任务完成
                        yield {
                            "type": "final",
                            "data": {
                                "content": response.get("content"),
                                "usage": response.get("usage", {}),
                                "model": response.get("model", model_config["name"]),
                                "execution_time_ms": execution_time,
                                "iterations": current_iteration
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        break
                        
                except Exception as e:
                    logger.error(f"LLM 调用失败: {e}")
                    yield {
                        "type": "error",
                        "error": f"LLM 调用失败: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                    break
            
            # 如果循环正常结束（达到最大迭代次数），生成最终响应
            # 获取最后一条assistant消息作为最终回复
            last_assistant_message = None
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    last_assistant_message = msg
                    break
            
            if last_assistant_message:
                logger.info(f"🎯 循环结束，生成最终响应，tool_calls数量: {len(last_assistant_message.get('tool_calls', []))}")
                yield {
                    "type": "final",
                    "data": {
                        "content": last_assistant_message.get("content"),
                        "tool_calls": last_assistant_message.get("tool_calls", []),
                        "usage": {},  # 总usage统计可以后续优化
                        "model": model_config["name"],
                        "execution_time_ms": int((time.time() - run_start_time) * 1000),
                        "iterations": current_iteration
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("⚠️ 循环结束但没有找到assistant消息")
                yield {
                    "type": "final",
                    "data": {
                        "content": "执行完成但无响应内容",
                        "tool_calls": [],
                        "usage": {},
                        "model": model_config["name"],
                        "execution_time_ms": int((time.time() - run_start_time) * 1000),
                        "iterations": current_iteration
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            # 保存对话历史到记忆和数据库
            await self.memory_manager.save_conversation(
                agent_id=str(agent.id),
                run_id=str(db_run.id),
                messages=messages
            )
            
            # 直接保存所有消息到数据库
            if self.db:
                from ..models import Message
                for msg in messages:
                    # 跳过初始的系统消息
                    if msg.get("role") != "system":
                        db_message = Message(
                            run_id=str(db_run.id),
                            role=msg.get("role"),
                            content=msg.get("content"),
                            tool_calls=msg.get("tool_calls"),
                            tool_call_id=msg.get("tool_call_id")
                        )
                        self.db.add(db_message)
                try:
                    self.db.commit()
                    logger.info(f"✅ 保存了 {len([m for m in messages if m.get('role') != 'system'])} 条消息到数据库")
                except Exception as e:
                    logger.error(f"❌ 保存消息到数据库失败: {e}")
                    self.db.rollback()
            
            yield {
                "type": "execution_complete",
                "iterations": current_iteration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            yield {
                "type": "execution_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_model_config(self, model_identifier: str) -> Dict[str, Any]:
        """获取模型配置"""
        
        try:
            # 从数据库获取模型配置
            if self.db:
                # 尝试按ID查找
                try:
                    import uuid
                    model_id = uuid.UUID(model_identifier)
                    model = self.db.query(Model).filter(Model.id == model_id).first()
                except ValueError:
                    # 如果不是有效的UUID，按名称查找
                    model = self.db.query(Model).filter(Model.name == model_identifier).first()
                
                if model:
                    # 获取API key - 优先使用模型配置中的API key
                    provider = str(model.provider)
                    api_key = None
                    
                    # 首先尝试从模型配置中获取API key
                    if hasattr(model, 'api_key') and model.api_key:
                        api_key = model.api_key
                    else:
                        # 如果模型配置中没有，从环境变量获取
                        api_key = await self._get_api_key_for_provider(provider)
                    
                    # 获取自定义headers
                    custom_headers = {}
                    if hasattr(model, 'custom_headers') and model.custom_headers:
                        try:
                            custom_headers = json.loads(str(model.custom_headers))
                        except:
                            custom_headers = {}
                    
                    return {
                        "name": str(model.name),
                        "endpoint": str(getattr(model, 'endpoint', '')),
                        "provider": provider,
                        "api_key": api_key,
                        "custom_headers": custom_headers
                    }
            
            # 模型不存在，抛出错误
            raise ValueError(f"Model {model_identifier} not found in database")
            
        except Exception as e:
            logger.error(f"Failed to get model config: {e}")
            raise ValueError(f"无法获取模型配置: {str(e)}")
    
    async def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """获取提供商的 API key"""
        
        import os
        
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "azure": "AZURE_OPENAI_KEY"
        }
        
        env_var = key_mapping.get(provider)
        if env_var:
            return os.getenv(env_var)
        
        return None
    

    
    async def _prepare_messages(
        self, 
        agent: Agent, 
        run_request: RunRequest,
        run_id: str
    ) -> List[Dict[str, Any]]:
        """准备消息历史"""
        
        messages = []
        
        # 添加系统提示（支持临时覆盖）
        system_config = agent.system_config if isinstance(agent.system_config, dict) else {}
        temp_config = getattr(run_request, 'temporary_config', None)
        
        # 安全获取临时系统提示
        temp_system_prompt = getattr(temp_config, 'system_prompt', None) if temp_config else None
        
        # 优先使用临时配置的系统提示，否则使用Agent配置的系统提示
        system_prompt = temp_system_prompt or system_config.get("system_prompt", "你是一个有用的 AI 助手。")
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 加载历史记忆（如果配置了）
        if system_config.get("enable_memory", False):
            window_size = system_config.get("max_context_turns", 10)
            history = await self.memory_manager.get_conversation_history(
                agent_id=str(agent.id),
                limit=window_size
            )
            messages.extend(history)
        
        # 添加当前请求的消息并保存到数据库
        for msg in run_request.messages:
            # 转换MessageRequest对象为字典
            if hasattr(msg, 'model_dump'):
                msg_dict = msg.model_dump()
            else:
                msg_dict = {
                    "role": msg.role,
                    "content": msg.content
                }
            
            messages.append(msg_dict)
            
            # 保存用户消息到数据库
            if self.db:
                from ..models import Message
                db_message = Message(
                    run_id=run_id,
                    role=msg.role,
                    content=msg.content,
                    tool_calls=getattr(msg, 'tool_calls', None)
                )
                self.db.add(db_message)
        
        if self.db:
            self.db.commit()
        
        return messages
    
    async def _get_available_tools(self, tools_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        
        tools = []
        
        # 从 tools_config.enabled_tools 中获取工具ID列表
        enabled_tool_ids = tools_config.get("enabled_tools", [])
        
        if self.db:
            # 从数据库中查询工具信息
            from ..models import Tool
            
            for tool_id in enabled_tool_ids:
                try:
                    # 首先尝试通过名称查询，避免UUID转换错误
                    tool = self.db.query(Tool).filter(
                        Tool.name == tool_id
                    ).filter(Tool.enabled == True).first()
                    
                    # 如果通过名称找不到，再尝试通过UUID查询（如果tool_id是有效的UUID）
                    if not tool:
                        try:
                            import uuid
                            uuid.UUID(tool_id)  # 验证是否是有效的UUID
                            tool = self.db.query(Tool).filter(
                                Tool.id == tool_id
                            ).filter(Tool.enabled == True).first()
                        except ValueError:
                            # tool_id不是有效的UUID，跳过UUID查询
                            pass
                    
                    if tool:
                        # 将数据库中的schema转换为LLM工具格式
                        if tool.schema:
                            tool_schema = tool.schema.copy()  # 创建副本避免修改原始数据
                            # 确保schema格式正确
                            if isinstance(tool_schema, dict):
                                if "function" in tool_schema:
                                    # 确保function.name使用正确的工具名称
                                    tool_schema["function"]["name"] = tool.name
                                    tools.append(tool_schema)
                                elif "type" in tool_schema and tool_schema["type"] == "function":
                                    # 这种情况下整个schema就是function定义
                                    tool_schema["name"] = tool.name
                                    wrapped_schema = {
                                        "type": "function",
                                        "function": tool_schema
                                    }
                                    tools.append(wrapped_schema)
                                else:
                                    # 如果schema格式不标准，尝试包装
                                    tool_schema["name"] = tool.name
                                    wrapped_schema = {
                                        "type": "function", 
                                        "function": tool_schema
                                    }
                                    tools.append(wrapped_schema)
                            logger.info(f"✅ 加载工具: {tool.name}")
                        else:
                            logger.warning(f"⚠️ 工具 {tool.name} 没有有效的schema")
                    else:
                        logger.warning(f"⚠️ 找不到工具: {tool_id}")
                except Exception as e:
                    logger.error(f"❌ 加载工具 {tool_id} 失败: {e}")
        else:
            # 如果没有数据库连接，使用传统的工具注册方式（向后兼容）
            for tool_id in enabled_tool_ids:
                tool_schema = await self.tool_executor.get_tool_schema(tool_id)
                if tool_schema:
                    tools.append(tool_schema)
                    logger.info(f"✅ 从注册表加载工具: {tool_id}")
        
        logger.info(f"🔧 总共加载了 {len(tools)} 个工具")
        return tools
    
    async def _resolve_tool_name(self, tool_identifier: str) -> str:
        """将工具ID或名称解析为实际的工具名称"""
        
        if self.db:
            from ..models import Tool
            
            try:
                # 首先尝试按名称查询
                tool = self.db.query(Tool).filter(
                    Tool.name == tool_identifier
                ).filter(Tool.enabled == True).first()
                
                if tool:
                    return tool.name
                
                # 如果按名称找不到，尝试按UUID查询
                try:
                    import uuid
                    uuid.UUID(tool_identifier)  # 验证是否是有效的UUID
                    tool = self.db.query(Tool).filter(
                        Tool.id == tool_identifier
                    ).filter(Tool.enabled == True).first()
                    
                    if tool:
                        logger.info(f"🔄 工具ID映射: {tool_identifier} -> {tool.name}")
                        return tool.name
                except ValueError:
                    # 不是有效的UUID
                    pass
                    
            except Exception as e:
                logger.error(f"❌ 解析工具名称失败: {e}")
        
        # 如果数据库查询失败或没有数据库连接，返回原始标识符
        return tool_identifier 