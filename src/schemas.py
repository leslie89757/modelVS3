"""Pydantic 模式定义"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, ConfigDict

from .models import ProviderType, AgentStatus, RouteStrategy, RunStatus


# 基础响应模式
class BaseResponse(BaseModel):
    """基础响应模式"""
    success: bool = True
    message: str = "操作成功"
    timestamp: datetime = Field(default_factory=datetime.now)


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int
    per_page: int
    total: int
    pages: int


class PaginatedResponse(BaseResponse):
    """分页响应"""
    meta: PaginationMeta
    data: List[Any]


# 模型相关 Schema
class ModelBase(BaseModel):
    """模型基础模式"""
    name: str = Field(..., description="模型名称")
    provider: ProviderType = Field(..., description="提供商")
    endpoint: str = Field(..., description="API 端点")
    context_len: int = Field(4096, description="上下文长度")
    enabled: bool = Field(True, description="是否启用")
    api_key: Optional[str] = Field(None, description="API密钥")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")


class ModelCreate(ModelBase):
    """创建模型"""
    pass


class ModelUpdate(BaseModel):
    """更新模型"""
    name: Optional[str] = None
    provider: Optional[ProviderType] = None
    endpoint: Optional[str] = None
    context_len: Optional[int] = None
    enabled: Optional[bool] = None
    api_key: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None


class ModelResponse(ModelBase):
    """模型响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# Agent 相关 Schema

class ModelConfig(BaseModel):
    """模型配置"""
    model_config = ConfigDict(protected_namespaces=())
    
    primary_model_id: str = Field(..., description="主要模型ID")
    fallback_model_id: Optional[str] = Field(None, description="备用模型ID")
    temperature: float = Field(0.7, ge=0, le=2, description="温度")
    max_tokens: int = Field(2000, gt=0, le=8000, description="最大令牌数")
    top_p: float = Field(0.9, ge=0, le=1, description="Top P")
    frequency_penalty: float = Field(0, ge=-2, le=2, description="频率惩罚")
    presence_penalty: float = Field(0, ge=-2, le=2, description="存在惩罚")


class SystemConfig(BaseModel):
    """系统配置"""
    system_prompt: str = Field(..., description="系统提示词")
    conversation_starters: List[str] = Field(default=[], description="对话开启语")
    response_style: str = Field("formal", description="响应风格")
    max_context_turns: int = Field(10, gt=0, description="最大上下文轮数")
    enable_memory: bool = Field(True, description="启用记忆")


class ToolsConfig(BaseModel):
    """工具配置"""
    enabled_tools: List[str] = Field(default=[], description="启用的工具列表")
    tool_configs: Dict[str, Any] = Field(default={}, description="工具特定配置")
    custom_tools: List[Dict[str, Any]] = Field(default=[], description="自定义工具")


class RetrievalConfig(BaseModel):
    """检索配置"""
    top_k: int = 5
    similarity_threshold: float = 0.7
    rerank: bool = True


class KnowledgeConfig(BaseModel):
    """知识库配置"""
    enabled: bool = False
    documents: List[str] = []
    retrieval_config: RetrievalConfig = Field(default_factory=RetrievalConfig)


class RateLimits(BaseModel):
    """速率限制"""
    requests_per_minute: int = 60
    requests_per_day: int = 1000


class DeploymentConfig(BaseModel):
    """部署配置"""
    api_key: Optional[str] = None
    rate_limits: RateLimits = Field(default_factory=RateLimits)
    webhook_url: Optional[str] = None


class AgentStats(BaseModel):
    """Agent统计"""
    total_conversations: int = 0
    total_messages: int = 0
    avg_response_time: float = 0
    user_satisfaction: float = 0


class AgentBase(BaseModel):
    """Agent 基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent 名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    avatar: Optional[str] = Field(None, description="头像URL")
    category: str = Field("其他", description="分类")
    tags: List[str] = Field(default=[], description="标签")
    access_level: str = Field("private", description="访问级别")
    
    llm_config: ModelConfig = Field(..., description="模型配置")
    system_config: SystemConfig = Field(..., description="系统配置")
    tools_config: ToolsConfig = Field(default_factory=ToolsConfig)
    knowledge_config: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    deployment_config: DeploymentConfig = Field(default_factory=DeploymentConfig)


class AgentCreate(AgentBase):
    """创建 Agent"""
    pass


class AgentUpdate(BaseModel):
    """更新 Agent"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    access_level: Optional[str] = None
    status: Optional[AgentStatus] = None
    
    llm_config: Optional[ModelConfig] = None
    system_config: Optional[SystemConfig] = None
    tools_config: Optional[ToolsConfig] = None
    knowledge_config: Optional[KnowledgeConfig] = None
    deployment_config: Optional[DeploymentConfig] = None


class AgentResponse(AgentBase):
    """Agent 响应"""
    model_config = {"from_attributes": True}
    
    id: uuid.UUID
    status: AgentStatus
    version: int = 1
    stats: AgentStats = Field(default_factory=AgentStats)
    owner_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# 工具相关 Schema
class ToolBase(BaseModel):
    """工具基础模式"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="描述")
    schema: Dict[str, Any] = Field(..., description="工具 Schema")
    endpoint: Optional[str] = Field(None, description="HTTP 端点")
    enabled: bool = Field(True, description="是否启用")


class ToolCreate(ToolBase):
    """创建工具"""
    model_config = ConfigDict(protected_namespaces=())
    pass


class ToolUpdate(BaseModel):
    """更新工具"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: Optional[str] = None
    description: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    endpoint: Optional[str] = None
    enabled: Optional[bool] = None


class ToolResponse(ToolBase):
    """工具响应"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# 执行相关 Schema
class MessageRequest(BaseModel):
    """消息请求"""
    role: str = Field(..., description="消息角色 (user, assistant, system)")
    content: str = Field(..., description="消息内容")


class TemporaryConfig(BaseModel):
    """临时配置覆盖"""
    system_prompt: Optional[str] = Field(None, description="临时系统提示")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="临时温度")
    max_tokens: Optional[int] = Field(None, gt=0, le=8000, description="临时最大令牌数")
    top_p: Optional[float] = Field(None, ge=0, le=1, description="临时Top P")
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2, description="临时频率惩罚")
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2, description="临时存在惩罚")
    enabled_tools: Optional[List[str]] = Field(None, description="临时启用的工具列表")


class RunRequest(BaseModel):
    """执行请求"""
    agent_id: uuid.UUID = Field(..., description="Agent ID")
    messages: List[MessageRequest] = Field(..., description="消息列表")
    stream: bool = Field(False, description="是否流式响应")
    max_tokens: Optional[int] = Field(None, description="最大 tokens")
    temperature: Optional[float] = Field(None, description="温度参数")
    protocol: str = Field("FunctionCall", description="工具调用协议 (仅支持 FunctionCall)")
    temporary_config: Optional[TemporaryConfig] = Field(None, description="临时配置覆盖")
    model_id: Optional[str] = Field(None, description="指定使用的模型ID（用于多模型对比测试）")


class MultiModelRunRequest(BaseModel):
    """多模型批量执行请求"""
    model_config = {"protected_namespaces": ()}
    
    agent_id: uuid.UUID = Field(..., description="Agent ID")
    messages: List[MessageRequest] = Field(..., description="消息列表")
    model_ids: List[str] = Field(..., min_items=1, max_items=20, description="要执行的模型ID列表")
    stream: bool = Field(False, description="是否流式响应")
    max_tokens: Optional[int] = Field(None, description="最大 tokens")
    temperature: Optional[float] = Field(None, description="温度参数")
    protocol: str = Field("FunctionCall", description="工具调用协议 (仅支持 FunctionCall)")
    temporary_config: Optional[TemporaryConfig] = Field(None, description="临时配置覆盖")
    max_concurrent: int = Field(5, ge=1, le=10, description="最大并发数")


class MultiModelRunResponse(BaseModel):
    """多模型执行响应"""
    success: bool = Field(True, description="整体执行是否成功")
    message: str = Field("多模型执行完成", description="执行消息")
    total_models: int = Field(..., description="总模型数")
    successful_models: int = Field(..., description="成功执行的模型数")
    failed_models: int = Field(..., description="失败的模型数")
    execution_time_ms: float = Field(..., description="总执行时间(毫秒)")
    results: Dict[str, Any] = Field(..., description="每个模型的执行结果")
    run_ids: Dict[str, uuid.UUID] = Field(..., description="每个模型对应的run_id")


class MessageResponse(BaseModel):
    """消息响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    created_at: datetime


class RunResponse(BaseModel):
    """执行响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    agent_id: uuid.UUID
    model_id: Optional[uuid.UUID] = None
    status: RunStatus
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # 新字段：AI回复（推荐使用） - 支持字典格式
    response: Optional[Dict[str, Any]] = Field(None, description="AI的回复消息")
    
    # 完整消息历史（包含工具调用和工具结果）
    messages: Optional[List[Dict[str, Any]]] = Field(None, description="完整的消息历史记录")


# 路由相关 Schema
class RouteBase(BaseModel):
    """路由基础模式"""
    model_config = ConfigDict(protected_namespaces=())
    
    tenant_id: Optional[uuid.UUID] = Field(None, description="租户 ID")
    prompt_type: Optional[str] = Field(None, description="提示类型")
    strategy: RouteStrategy = Field(RouteStrategy.FIXED, description="路由策略")
    primary_model_id: uuid.UUID = Field(..., description="主模型 ID")
    backup_model_ids: Optional[List[uuid.UUID]] = Field(None, description="备份模型 ID 列表")


class RouteCreate(RouteBase):
    """创建路由"""
    pass


class RouteUpdate(BaseModel):
    """更新路由"""
    tenant_id: Optional[uuid.UUID] = None
    prompt_type: Optional[str] = None
    strategy: Optional[RouteStrategy] = None
    primary_model_id: Optional[uuid.UUID] = None
    backup_model_ids: Optional[List[uuid.UUID]] = None


class RouteResponse(RouteBase):
    """路由响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# 用户相关 Schema
class UserBase(BaseModel):
    """用户基础模式"""
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    is_active: bool = Field(True, description="是否激活")
    tenant_id: Optional[uuid.UUID] = Field(None, description="租户 ID")


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """更新用户"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    is_superuser: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


# 认证相关 Schema
class Token(BaseModel):
    """令牌"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据"""
    user_id: Optional[uuid.UUID] = None


class LoginRequest(BaseModel):
    """登录请求"""
    email: str
    password: str


# 统计相关 Schema
class UsageStats(BaseModel):
    """使用统计"""
    model_config = ConfigDict(from_attributes=True)
    
    date: datetime
    request_count: int
    input_tokens: int
    output_tokens: int
    cost_usd: float = 0.0


class DashboardStats(BaseModel):
    """仪表板统计"""
    total_runs: int
    active_agents: int
    total_cost_usd: float = 0.0
    avg_response_time_ms: float
    daily_usage: List[UsageStats]


# OpenAI 兼容 Schema
class ChatCompletionMessage(BaseModel):
    """聊天完成消息"""
    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """聊天完成请求"""
    model: str
    messages: List[ChatCompletionMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None


class ChatCompletionResponse(BaseModel):
    """聊天完成响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class ChatSessionBase(BaseModel):
    """聊天会话基础模式"""
    model_config = ConfigDict(protected_namespaces=())
    
    title: str = Field(..., description="会话标题")
    model_id: Optional[uuid.UUID] = Field(None, description="模型ID")
    agent_id: Optional[uuid.UUID] = Field(None, description="Agent ID")
    model_type: str = Field("model", description="类型：model或agent")
    is_pinned: bool = Field(False, description="是否置顶")
    tags: List[str] = Field(default=[], description="标签")


class ChatSessionCreate(ChatSessionBase):
    """创建聊天会话"""
    pass


class ChatSessionUpdate(BaseModel):
    """更新聊天会话"""
    title: Optional[str] = None
    model_id: Optional[uuid.UUID] = None
    agent_id: Optional[uuid.UUID] = None
    model_type: Optional[str] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None


class ChatSessionResponse(ChatSessionBase):
    """聊天会话响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ChatMessageBase(BaseModel):
    """聊天消息基础模式"""
    model_config = ConfigDict(protected_namespaces=())
    
    role: str = Field(..., description="消息角色")
    content: Optional[str] = Field(None, description="消息内容")
    model_used: Optional[str] = Field(None, description="使用的模型")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用")
    tool_call_id: Optional[str] = Field(None, description="工具调用ID")


class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息"""
    session_id: uuid.UUID = Field(..., description="会话ID")


class ChatMessageResponse(ChatMessageBase):
    """聊天消息响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime 