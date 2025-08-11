"""高级Agent管理路由"""

import uuid
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..database import get_db
from ..schemas_advanced import (
    AdvancedAgentCreate, AdvancedAgentUpdate, AdvancedAgentResponse,
    AgentSessionCreate, AgentSessionResponse, SendMessageRequest, SendMessageResponse,
    AdvancedToolResponse, AgentMemoryResponse, AgentKnowledgeResponse,
    BaseResponse, ErrorResponse, PaginatedResponse,
    AGENT_ROLES, AUTONOMY_LEVELS
)
from ..models_advanced import (
    AdvancedAgent, AgentSession, SessionMessage, AdvancedTool,
    AgentMemory, AgentKnowledgeBase, AgentPerformanceMetric,
    AdvancedAgentStatus, SessionStatus, MessageRole
)
from ..core.advanced_agent_executor import AdvancedAgentExecutor

router = APIRouter()


# 获取角色和自主水平定义
@router.get("/meta/roles", summary="获取Agent角色定义")
async def get_agent_roles():
    """获取Agent角色定义"""
    return AGENT_ROLES


@router.get("/meta/autonomy-levels", summary="获取自主水平定义")
async def get_autonomy_levels():
    """获取自主水平定义"""
    return AUTONOMY_LEVELS





@router.get("/", response_model=List[AdvancedAgentResponse], summary="获取高级Agent列表")
async def list_advanced_agents(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db)
):
    """获取高级Agent列表"""
    query = db.query(AdvancedAgent)
    
    if role:
        query = query.filter(AdvancedAgent.role == role)
    if status:
        query = query.filter(AdvancedAgent.status == status)
    
    agents = query.offset(skip).limit(limit).all()
    
    # 转换为响应格式
    result = []
    for agent in agents:
        agent_data = {
            "id": str(agent.id),
            "name": agent.name,
            "role": agent.role,
            "personality": agent.personality,
            "description": agent.description,
            "config": agent.config,
            "status": agent.status,
            "stats": agent.stats,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at
        }
        
        # 添加当前会话信息
        if agent.current_session_id:
            session = db.query(AgentSession).filter(AgentSession.id == agent.current_session_id).first()
            if session:
                agent_data["current_session"] = {
                    "id": str(session.id),
                    "agent_id": str(session.agent_id),
                    "status": session.status,
                    "current_step": session.current_step,
                    "progress": session.progress,
                    "confidence_score": session.confidence_score,
                    "reasoning_visible": session.reasoning_visible,
                    "total_messages": session.total_messages,
                    "total_tool_calls": session.total_tool_calls,
                    "execution_time_ms": session.execution_time_ms,
                    "tokens_used": session.tokens_used,
                    "cost_estimate": session.cost_estimate,
                    "messages": [],
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "completed_at": session.completed_at
                }
        
        result.append(AdvancedAgentResponse(**agent_data))
    
    return result


@router.post("/", response_model=AdvancedAgentResponse, summary="创建高级Agent", status_code=status.HTTP_201_CREATED)
async def create_advanced_agent(
    agent_data: AdvancedAgentCreate,
    db: Session = Depends(get_db)
):
    """创建新的高级Agent"""
    # 检查名称是否已存在
    existing_agent = db.query(AdvancedAgent).filter(AdvancedAgent.name == agent_data.name).first()
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent名称 '{agent_data.name}' 已存在"
        )
    
    # 验证角色是否有效
    valid_roles = [role["id"] for role in AGENT_ROLES]
    if agent_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色: {agent_data.role}"
        )
    
    # 验证自主水平是否有效
    valid_autonomy_levels = [level["value"] for level in AUTONOMY_LEVELS]
    if agent_data.config.autonomy_level not in valid_autonomy_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的自主水平: {agent_data.config.autonomy_level}"
        )
    
    # 创建Agent
    db_agent = AdvancedAgent(
        name=agent_data.name,
        role=agent_data.role,
        personality=agent_data.personality,
        description=agent_data.description,
        config=agent_data.config.model_dump(),
        status=AdvancedAgentStatus.IDLE,
        stats={
            "total_sessions": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "user_satisfaction": 0.0,
            "cost_efficiency": 0.0
        }
    )
    
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return AdvancedAgentResponse(
        id=str(db_agent.id),
        name=db_agent.name,
        role=db_agent.role,
        personality=db_agent.personality,
        description=db_agent.description,
        config=db_agent.config,
        status=db_agent.status,
        stats=db_agent.stats,
        created_at=db_agent.created_at,
        updated_at=db_agent.updated_at
    )


@router.get("/{agent_id}", response_model=AdvancedAgentResponse, summary="获取高级Agent详情")
async def get_advanced_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取高级Agent详情"""
    agent = db.query(AdvancedAgent).filter(AdvancedAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent不存在"
        )
    
    agent_data = {
        "id": str(agent.id),
        "name": agent.name,
        "role": agent.role,
        "personality": agent.personality,
        "description": agent.description,
        "config": agent.config,
        "status": agent.status,
        "stats": agent.stats,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at
    }
    
    # 添加当前会话信息
    if agent.current_session_id:
        session = db.query(AgentSession).filter(AgentSession.id == agent.current_session_id).first()
        if session:
            # 获取会话消息
            messages = db.query(SessionMessage).filter(SessionMessage.session_id == session.id).order_by(SessionMessage.timestamp).all()
            session_messages = []
            for msg in messages:
                session_messages.append({
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "confidence": msg.confidence,
                    "reasoning": msg.reasoning,
                    "tool_calls": msg.tool_calls,
                    "message_metadata": msg.message_metadata
                })
            
            agent_data["current_session"] = {
                "id": str(session.id),
                "agent_id": str(session.agent_id),
                "status": session.status,
                "current_step": session.current_step,
                "progress": session.progress,
                "confidence_score": session.confidence_score,
                "reasoning_visible": session.reasoning_visible,
                "total_messages": session.total_messages,
                "total_tool_calls": session.total_tool_calls,
                "execution_time_ms": session.execution_time_ms,
                "tokens_used": session.tokens_used,
                "cost_estimate": session.cost_estimate,
                "messages": session_messages,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "completed_at": session.completed_at
            }
    
    return AdvancedAgentResponse(**agent_data)


@router.patch("/{agent_id}", response_model=AdvancedAgentResponse, summary="更新高级Agent")
async def update_advanced_agent(
    agent_id: uuid.UUID,
    agent_update: AdvancedAgentUpdate,
    db: Session = Depends(get_db)
):
    """更新高级Agent"""
    agent = db.query(AdvancedAgent).filter(AdvancedAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent不存在"
        )
    
    # 更新字段
    update_data = agent_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "config" and value:
            # 合并配置
            current_config = agent.config or {}
            current_config.update(value.model_dump())
            setattr(agent, field, current_config)
        else:
            setattr(agent, field, value)
    
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    
    return AdvancedAgentResponse(
        id=str(agent.id),
        name=agent.name,
        role=agent.role,
        personality=agent.personality,
        description=agent.description,
        config=agent.config,
        status=agent.status,
        stats=agent.stats,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )


@router.delete("/{agent_id}", response_model=BaseResponse, summary="删除高级Agent")
async def delete_advanced_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除高级Agent"""
    agent = db.query(AdvancedAgent).filter(AdvancedAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent不存在"
        )
    
    # 检查是否有活动会话
    active_session = db.query(AgentSession).filter(
        and_(AgentSession.agent_id == agent_id, AgentSession.status == SessionStatus.ACTIVE)
    ).first()
    
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除有活动会话的Agent，请先结束会话"
        )
    
    db.delete(agent)
    db.commit()
    
    return BaseResponse(message=f"Agent '{agent.name}' 已删除")


# 会话管理
@router.post("/{agent_id}/sessions", response_model=AgentSessionResponse, summary="创建Agent会话")
async def create_agent_session(
    agent_id: uuid.UUID,
    session_data: AgentSessionCreate,
    db: Session = Depends(get_db)
):
    """创建Agent会话"""
    agent = db.query(AdvancedAgent).filter(AdvancedAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent不存在"
        )
    
    # 检查是否已有活动会话
    existing_session = db.query(AgentSession).filter(
        and_(AgentSession.agent_id == agent_id, AgentSession.status == SessionStatus.ACTIVE)
    ).first()
    
    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent已有活动会话"
        )
    
    # 创建新会话
    session_config = session_data.session_config.model_dump() if session_data.session_config else {
        "max_messages": 100,
        "timeout_minutes": 30,
        "auto_save": True
    }
    
    db_session = AgentSession(
        agent_id=agent_id,
        status=SessionStatus.ACTIVE,
        current_step="初始化",
        progress=0,
        confidence_score=1.0,
        reasoning_visible=agent.config.get("transparency", "high") == "high",
        session_config=session_config,
        total_messages=0,
        total_tool_calls=0,
        execution_time_ms=0,
        tokens_used=0,
        cost_estimate=0.0
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # 更新Agent的当前会话
    agent.current_session_id = db_session.id
    agent.status = AdvancedAgentStatus.IDLE
    db.commit()
    
    return AgentSessionResponse(
        id=str(db_session.id),
        agent_id=str(db_session.agent_id),
        status=db_session.status,
        current_step=db_session.current_step,
        progress=db_session.progress,
        confidence_score=db_session.confidence_score,
        reasoning_visible=db_session.reasoning_visible,
        total_messages=db_session.total_messages,
        total_tool_calls=db_session.total_tool_calls,
        execution_time_ms=db_session.execution_time_ms,
        tokens_used=db_session.tokens_used,
        cost_estimate=db_session.cost_estimate,
        messages=[],
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
        completed_at=db_session.completed_at
    )


@router.post("/{agent_id}/sessions/{session_id}/message", response_model=SendMessageResponse, summary="发送消息给Agent")
async def send_message_to_agent(
    agent_id: uuid.UUID,
    session_id: uuid.UUID,
    message_data: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """发送消息给Agent"""
    # 验证Agent和Session
    agent = db.query(AdvancedAgent).filter(AdvancedAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent不存在"
        )
    
    session = db.query(AgentSession).filter(
        and_(AgentSession.id == session_id, AgentSession.agent_id == agent_id)
    ).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会话未激活"
        )
    
    # 保存用户消息
    user_message = SessionMessage(
        session_id=session_id,
        role=MessageRole.USER,
        content=message_data.message,
        timestamp=datetime.utcnow()
    )
    db.add(user_message)
    
    # 更新会话统计
    session.total_messages += 1
    session.current_step = "处理用户输入"
    session.updated_at = datetime.utcnow()
    
    # 更新Agent状态
    agent.status = AdvancedAgentStatus.THINKING
    
    db.commit()
    
    # 执行Agent处理
    start_time = time.time()
    
    try:
        # 创建Agent执行器
        executor = AdvancedAgentExecutor(db)
        
        # 获取会话历史
        messages = db.query(SessionMessage).filter(SessionMessage.session_id == session_id).order_by(SessionMessage.timestamp).all()
        message_history = []
        for msg in messages:
            message_history.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })
        
        # 执行Agent推理
        result = await executor.process_message(
            agent=agent,
            session=session,
            message=message_data.message,
            message_history=message_history,
            include_reasoning=message_data.include_reasoning,
            max_iterations=message_data.max_iterations or agent.config.get("max_iterations", 10)
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # 保存Agent响应
        agent_message = SessionMessage(
            session_id=session_id,
            role=MessageRole.AGENT,
            content=result["content"],
            confidence=result.get("confidence", 0.8),
            reasoning=result.get("reasoning") if message_data.include_reasoning else None,
            tool_calls=result.get("tool_calls"),
            message_metadata=result.get("metadata"),
            tokens_used=result.get("tokens_used", 0),
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow()
        )
        
        db.add(agent_message)
        
        # 更新会话和Agent状态
        session.total_messages += 1
        session.confidence_score = result.get("confidence", session.confidence_score)
        session.current_step = "等待用户输入"
        session.execution_time_ms += execution_time
        session.tokens_used += result.get("tokens_used", 0)
        session.cost_estimate += result.get("cost", 0.0)
        session.updated_at = datetime.utcnow()
        
        if result.get("tool_calls"):
            session.total_tool_calls += len(result["tool_calls"])
        
        agent.status = AdvancedAgentStatus.IDLE
        
        db.commit()
        db.refresh(agent_message)
        
        return SendMessageResponse(
            id=str(agent_message.id),
            content=result["content"],
            confidence=result.get("confidence", 0.8),
            reasoning=result.get("reasoning") if message_data.include_reasoning else None,
            tool_calls=result.get("tool_calls"),
            timestamp=agent_message.timestamp,
            execution_time_ms=execution_time,
            tokens_used=result.get("tokens_used", 0)
        )
        
    except Exception as e:
        # 错误处理
        execution_time = int((time.time() - start_time) * 1000)
        
        error_message = SessionMessage(
            session_id=session_id,
            role=MessageRole.SYSTEM,
            content=f"处理失败: {str(e)}",
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow()
        )
        
        db.add(error_message)
        
        session.current_step = "错误"
        session.updated_at = datetime.utcnow()
        agent.status = AdvancedAgentStatus.ERROR
        
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent处理失败: {str(e)}"
        )


@router.post("/{agent_id}/sessions/{session_id}/pause", response_model=BaseResponse, summary="暂停Agent会话")
async def pause_agent_session(
    agent_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """暂停Agent会话"""
    session = db.query(AgentSession).filter(
        and_(AgentSession.id == session_id, AgentSession.agent_id == agent_id)
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能暂停活动会话"
        )
    
    session.status = SessionStatus.PAUSED
    session.current_step = "已暂停"
    session.updated_at = datetime.utcnow()
    
    # 更新Agent状态
    agent = db.query(AdvancedAgent).filter(AdvancedAgent.id == agent_id).first()
    if agent:
        agent.status = AdvancedAgentStatus.WAITING
    
    db.commit()
    
    return BaseResponse(message="会话已暂停")


@router.post("/{agent_id}/sessions/{session_id}/stop", response_model=BaseResponse, summary="结束Agent会话")
async def stop_agent_session(
    agent_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """结束Agent会话"""
    session = db.query(AgentSession).filter(
        and_(AgentSession.id == session_id, AgentSession.agent_id == agent_id)
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    session.status = SessionStatus.COMPLETED
    session.current_step = "已完成"
    session.completed_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    
    # 更新Agent状态
    agent = db.query(AdvancedAgent).filter(AdvancedAgent.id == agent_id).first()
    if agent:
        agent.status = AdvancedAgentStatus.IDLE
        agent.current_session_id = None
        
        # 更新统计信息
        stats = agent.stats or {}
        stats["total_sessions"] = stats.get("total_sessions", 0) + 1
        
        # 计算成功率（这里简单设为100%，实际应根据会话质量评估）
        total_sessions = stats["total_sessions"]
        success_rate = stats.get("success_rate", 0.0)
        stats["success_rate"] = (success_rate * (total_sessions - 1) + 1.0) / total_sessions
        
        # 计算平均响应时间
        if session.total_messages > 0:
            avg_time = session.execution_time_ms / session.total_messages
            current_avg = stats.get("avg_response_time", 0.0)
            stats["avg_response_time"] = (current_avg * (total_sessions - 1) + avg_time) / total_sessions
        
        agent.stats = stats
    
    db.commit()
    
    return BaseResponse(message="会话已结束")


# 工具管理
@router.get("/tools", response_model=List[AdvancedToolResponse], summary="获取高级工具列表")
async def list_advanced_tools(
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    category: Optional[str] = Query(None, description="按分类筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取高级工具列表"""
    query = db.query(AdvancedTool)
    
    if enabled is not None:
        query = query.filter(AdvancedTool.enabled == enabled)
    if category:
        query = query.filter(AdvancedTool.category == category)
    
    tools = query.offset(skip).limit(limit).all()
    
    result = []
    for tool in tools:
        result.append(AdvancedToolResponse(
            id=str(tool.id),
            name=tool.name,
            description=tool.description,
            category=tool.category,
            schema=tool.schema,
            implementation=tool.implementation,
            version=tool.version,
            enabled=tool.enabled,
            required_params=tool.required_params,
            optional_params=tool.optional_params,
            usage_count=tool.usage_count,
            success_rate=tool.success_rate,
            avg_execution_time=tool.avg_execution_time,
            created_at=tool.created_at,
            updated_at=tool.updated_at
        ))
    
    return result 