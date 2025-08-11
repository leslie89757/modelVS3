"""数据库模型"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class ProviderType(str, Enum):
    """LLM 提供商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    OLLAMA = "ollama"
    LOCALAI = "localai"
    VLLM = "vllm"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent 状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class RouteStrategy(str, Enum):
    """路由策略"""
    FIXED = "fixed"
    LATENCY_FIRST = "latency_first"
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCE = "load_balance"


class RunStatus(str, Enum):
    """运行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Model(Base):
    """LLM 模型表"""
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    provider = Column(String, nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    context_len = Column(Integer, nullable=False, default=4096)
    enabled = Column(Boolean, nullable=False, default=True)
    api_key = Column(String, nullable=True)  # API密钥
    custom_headers = Column(JSON, nullable=True)  # 自定义请求头
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    routes_primary = relationship("Route", foreign_keys="Route.primary_model_id", back_populates="primary_model")
    runs = relationship("Run", back_populates="model")


class Agent(Base):
    """Agent 配置表"""
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    avatar = Column(String, nullable=True)  # 头像URL
    category = Column(String, nullable=False, default="其他")
    tags = Column(ARRAY(String), nullable=True, default=[])
    status = Column(String, nullable=False, default=AgentStatus.DRAFT, index=True)
    access_level = Column(String, nullable=False, default="private")  # public, private, team
    version = Column(Integer, nullable=False, default=1)
    
    # 模型配置
    llm_config = Column(JSON, nullable=False)  # 包含primary_model_id, fallback_model_id等
    
    # 系统配置
    system_config = Column(JSON, nullable=False)  # 系统提示词、对话风格等
    
    # 工具配置
    tools_config = Column(JSON, nullable=False, default={})  # 启用的工具和配置
    
    # 知识库配置
    knowledge_config = Column(JSON, nullable=False, default={})  # 知识库设置
    
    # 部署配置
    deployment_config = Column(JSON, nullable=False, default={})  # 部署相关设置
    
    # 统计信息
    stats = Column(JSON, nullable=False, default={
        "total_conversations": 0,
        "total_messages": 0,
        "avg_response_time": 0,
        "user_satisfaction": 0
    })
    
    # 元数据
    owner_id = Column(UUID(as_uuid=True), nullable=True)  # 创建者 ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    runs = relationship("Run", back_populates="agent", cascade="all, delete-orphan")


class Route(Base):
    """路由配置表"""
    __tablename__ = "routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    prompt_type = Column(String, nullable=True)  # general, code, etc.
    strategy = Column(String, nullable=False, default=RouteStrategy.FIXED)
    primary_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)
    backup_model_ids = Column(ARRAY(UUID), nullable=True)  # 备份模型列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    primary_model = relationship("Model", foreign_keys=[primary_model_id], back_populates="routes_primary")


class Tool(Base):
    """工具注册表"""
    __tablename__ = "tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    schema = Column(JSON, nullable=False)  # OpenAI Function Schema
    endpoint = Column(String, nullable=True)  # HTTP endpoint
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Run(Base):
    """执行记录表"""
    __tablename__ = "runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=True, index=True)
    status = Column(String, nullable=False, default=RunStatus.PENDING)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    run_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    agent = relationship("Agent", back_populates="runs")
    model = relationship("Model", back_populates="runs")
    messages = relationship("Message", back_populates="run", cascade="all, delete-orphan")


class Message(Base):
    """消息记录表"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=True)
    tool_calls = Column(JSON, nullable=True)  # OpenAI tool call format
    tool_call_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    run = relationship("Run", back_populates="messages")


class Usage(Base):
    """使用统计表"""
    __tablename__ = "usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    request_count = Column(Integer, nullable=False, default=0)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    
    # 关系
    model = relationship("Model")


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, default="新对话")
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    model_type = Column(String(10), nullable=False, default="model")
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # 未来支持用户系统
    is_pinned = Column(Boolean, nullable=False, default=False)
    tags = Column(ARRAY(String), nullable=True, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    model = relationship("Model")
    agent = relationship("Agent")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=True)  # 允许为空，因为工具调用消息可能没有文本内容
    model_used = Column(String, nullable=True)  # 记录使用的模型
    tool_calls = Column(JSON, nullable=True)  # OpenAI tool call format
    tool_call_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    session = relationship("ChatSession", back_populates="messages")


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 