"""高级Agent数据库模型"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class AdvancedAgentStatus(str, Enum):
    """高级Agent状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class AgentPersonality(str, Enum):
    """Agent个性类型"""
    FORMAL = "formal"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"


class AutonomyLevel(str, Enum):
    """自主水平"""
    GUIDED = "guided"
    SEMI_AUTONOMOUS = "semi_autonomous"
    AUTONOMOUS = "autonomous"


class TransparencyLevel(str, Enum):
    """透明度级别"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"


class ToolCallStatus(str, Enum):
    """工具调用状态"""
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


class AdvancedAgent(Base):
    """高级Agent表"""
    __tablename__ = "advanced_agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # research_assistant, creative_partner, etc.
    personality = Column(String, nullable=False, default=AgentPersonality.PROFESSIONAL)
    description = Column(Text, nullable=True)
    
    # 核心配置
    config = Column(JSON, nullable=False, default={
        "primary_model": "",
        "autonomy_level": AutonomyLevel.SEMI_AUTONOMOUS,
        "transparency": TransparencyLevel.HIGH,
        "max_iterations": 10,
        "tools": [],
        "memory_enabled": True,
        "knowledge_base_enabled": False
    })
    
    # 运行时状态
    status = Column(String, nullable=False, default=AdvancedAgentStatus.IDLE)
    current_session_id = Column(UUID(as_uuid=True), ForeignKey("agent_sessions.id"), nullable=True)
    
    # 统计信息
    stats = Column(JSON, nullable=False, default={
        "total_sessions": 0,
        "success_rate": 0.0,
        "avg_response_time": 0.0,
        "user_satisfaction": 0.0,
        "cost_efficiency": 0.0
    })
    
    # 元数据
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    sessions = relationship("AgentSession", back_populates="agent", cascade="all, delete-orphan", foreign_keys="AgentSession.agent_id")
    current_session = relationship("AgentSession", foreign_keys=[current_session_id], post_update=True)


class AgentSession(Base):
    """Agent会话表"""
    __tablename__ = "agent_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("advanced_agents.id"), nullable=False)
    
    # 会话状态
    status = Column(String, nullable=False, default=SessionStatus.ACTIVE)
    current_step = Column(String, nullable=True)
    progress = Column(Integer, default=0)  # 0-100
    confidence_score = Column(Float, default=0.0)  # 0.0-1.0
    reasoning_visible = Column(Boolean, default=True)
    
    # 会话配置
    session_config = Column(JSON, nullable=False, default={
        "max_messages": 100,
        "timeout_minutes": 30,
        "auto_save": True
    })
    
    # 统计信息
    total_messages = Column(Integer, default=0)
    total_tool_calls = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    agent = relationship("AdvancedAgent", back_populates="sessions", foreign_keys=[agent_id])
    messages = relationship("SessionMessage", back_populates="session", cascade="all, delete-orphan")


class SessionMessage(Base):
    """会话消息表"""
    __tablename__ = "session_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("agent_sessions.id"), nullable=False)
    
    # 消息内容
    role = Column(String, nullable=False)  # user, agent, system, tool
    content = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # Agent消息的信心度
    reasoning = Column(Text, nullable=True)  # 推理过程
    
    # 工具调用相关
    tool_calls = Column(JSON, nullable=True)  # 工具调用信息
    tool_results = Column(JSON, nullable=True)  # 工具执行结果
    
    # 元数据
    message_metadata = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    session = relationship("AgentSession", back_populates="messages")


class AdvancedTool(Base):
    """高级工具表"""
    __tablename__ = "advanced_tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    
    # 工具配置
    schema = Column(JSON, nullable=False)  # 工具参数schema
    implementation = Column(JSON, nullable=False)  # 实现配置
    
    # 元数据
    version = Column(String, default="1.0.0")
    enabled = Column(Boolean, default=True)
    required_params = Column(ARRAY(String), default=[])
    optional_params = Column(ARRAY(String), default=[])
    
    # 统计信息
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_execution_time = Column(Float, default=0.0)
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AgentMemory(Base):
    """Agent记忆表"""
    __tablename__ = "agent_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("advanced_agents.id"), nullable=False)
    
    # 记忆内容
    memory_type = Column(String, nullable=False)  # conversation, preference, fact, skill
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # 向量嵌入
    
    # 记忆元数据
    importance_score = Column(Float, default=0.5)  # 重要性评分
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # 关联信息
    source_session_id = Column(UUID(as_uuid=True), nullable=True)
    source_message_id = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(ARRAY(String), default=[])
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    agent = relationship("AdvancedAgent")


class AgentPerformanceMetric(Base):
    """Agent性能指标表"""
    __tablename__ = "agent_performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("advanced_agents.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("agent_sessions.id"), nullable=True)
    
    # 性能指标
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)
    
    # 上下文信息
    context = Column(JSON, nullable=True)
    measurement_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    agent = relationship("AdvancedAgent")
    session = relationship("AgentSession")


class AgentKnowledgeBase(Base):
    """Agent知识库表"""
    __tablename__ = "agent_knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("advanced_agents.id"), nullable=False)
    
    # 知识内容
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String, default="text")  # text, document, code, etc.
    
    # 索引信息
    embedding = Column(JSON, nullable=True)
    keywords = Column(ARRAY(String), default=[])
    categories = Column(ARRAY(String), default=[])
    
    # 元数据
    source_url = Column(String, nullable=True)
    source_type = Column(String, nullable=True)  # upload, web, api, etc.
    file_path = Column(String, nullable=True)
    
    # 访问统计
    access_count = Column(Integer, default=0)
    relevance_score = Column(Float, default=0.0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    agent = relationship("AdvancedAgent") 