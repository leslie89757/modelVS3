"""高级Agent的Schema定义"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid


# 基础类型
class ToolCall(BaseModel):
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    status: str = "pending"  # pending, success, error
    execution_time: Optional[int] = None


class SessionMessage(BaseModel):
    """会话消息"""
    id: str
    role: str  # user, agent, system, tool
    content: str
    timestamp: datetime
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    message_metadata: Optional[Dict[str, Any]] = None


# Agent配置相关
class AgentConfig(BaseModel):
    """Agent配置"""
    primary_model: str
    autonomy_level: str = "semi_autonomous"  # guided, semi_autonomous, autonomous
    transparency: str = "high"  # high, medium, low
    max_iterations: int = 10
    tools: List[str] = []
    memory_enabled: bool = True
    knowledge_base_enabled: bool = False


class AgentStats(BaseModel):
    """Agent统计信息"""
    total_sessions: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    user_satisfaction: float = 0.0
    cost_efficiency: float = 0.0


# 创建和更新Schema
class AdvancedAgentCreate(BaseModel):
    """创建高级Agent"""
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., description="Agent角色")
    personality: str = "professional"  # formal, friendly, professional, creative
    description: Optional[str] = None
    config: AgentConfig


class AdvancedAgentUpdate(BaseModel):
    """更新高级Agent"""
    name: Optional[str] = None
    role: Optional[str] = None
    personality: Optional[str] = None
    description: Optional[str] = None
    config: Optional[AgentConfig] = None


class AdvancedAgentResponse(BaseModel):
    """高级Agent响应"""
    id: str
    name: str
    role: str
    personality: str
    description: Optional[str]
    config: AgentConfig
    status: str
    current_session: Optional[Dict[str, Any]] = None
    stats: AgentStats
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 会话相关
class SessionConfig(BaseModel):
    """会话配置"""
    max_messages: int = 100
    timeout_minutes: int = 30
    auto_save: bool = True


class AgentSessionCreate(BaseModel):
    """创建Agent会话"""
    session_config: Optional[SessionConfig] = None


class AgentSessionResponse(BaseModel):
    """Agent会话响应"""
    id: str
    agent_id: str
    status: str
    current_step: Optional[str]
    progress: int
    confidence_score: float
    reasoning_visible: bool
    total_messages: int
    total_tool_calls: int
    execution_time_ms: int
    tokens_used: int
    cost_estimate: float
    messages: List[SessionMessage] = []
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str = Field(..., min_length=1)
    include_reasoning: bool = True
    max_iterations: Optional[int] = None


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    id: str
    content: str
    confidence: float
    reasoning: Optional[str]
    tool_calls: Optional[List[ToolCall]]
    timestamp: datetime
    execution_time_ms: int
    tokens_used: int


# 工具相关
class AdvancedToolSchema(BaseModel):
    """高级工具Schema"""
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str] = []


class AdvancedToolImplementation(BaseModel):
    """工具实现配置"""
    type: str  # function, api, script
    endpoint: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    code: Optional[str] = None
    timeout: int = 30


class AdvancedToolCreate(BaseModel):
    """创建高级工具"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    category: str
    schema: AdvancedToolSchema
    implementation: AdvancedToolImplementation
    required_params: List[str] = []
    optional_params: List[str] = []


class AdvancedToolResponse(BaseModel):
    """高级工具响应"""
    id: str
    name: str
    description: str
    category: str
    schema: AdvancedToolSchema
    implementation: AdvancedToolImplementation
    version: str
    enabled: bool
    required_params: List[str]
    optional_params: List[str]
    usage_count: int
    success_rate: float
    avg_execution_time: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 记忆相关
class AgentMemoryCreate(BaseModel):
    """创建Agent记忆"""
    memory_type: str  # conversation, preference, fact, skill
    content: str
    importance_score: float = 0.5
    tags: List[str] = []
    expires_at: Optional[datetime] = None


class AgentMemoryResponse(BaseModel):
    """Agent记忆响应"""
    id: str
    agent_id: str
    memory_type: str
    content: str
    importance_score: float
    access_count: int
    last_accessed: Optional[datetime]
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# 知识库相关
class AgentKnowledgeCreate(BaseModel):
    """创建Agent知识"""
    title: str
    content: str
    content_type: str = "text"
    keywords: List[str] = []
    categories: List[str] = []
    source_url: Optional[str] = None
    source_type: Optional[str] = None


class AgentKnowledgeResponse(BaseModel):
    """Agent知识响应"""
    id: str
    agent_id: str
    title: str
    content: str
    content_type: str
    keywords: List[str]
    categories: List[str]
    source_url: Optional[str]
    source_type: Optional[str]
    access_count: int
    relevance_score: float
    last_accessed: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 性能指标相关
class AgentMetricCreate(BaseModel):
    """创建性能指标"""
    metric_name: str
    metric_value: float
    metric_unit: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentMetricResponse(BaseModel):
    """性能指标响应"""
    id: str
    agent_id: str
    session_id: Optional[str]
    metric_name: str
    metric_value: float
    metric_unit: Optional[str]
    context: Optional[Dict[str, Any]]
    measurement_time: datetime

    class Config:
        from_attributes = True


# 通用响应
class BaseResponse(BaseModel):
    """基础响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# 分页相关
class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# 预定义角色
AGENT_ROLES = [
    {
        "id": "research_assistant",
        "name": "研究助手",
        "description": "专业的信息收集和分析专家",
        "icon": "🔍",
        "suggested_tools": ["web_search", "document_analysis", "data_processing"]
    },
    {
        "id": "creative_partner",
        "name": "创意伙伴",
        "description": "富有想象力的内容创作助手",
        "icon": "🎨",
        "suggested_tools": ["image_generation", "text_enhancement", "brainstorming"]
    },
    {
        "id": "technical_expert",
        "name": "技术专家",
        "description": "代码分析和技术问题解决专家",
        "icon": "⚙️",
        "suggested_tools": ["code_analyzer", "api_tools", "debug_assistant"]
    },
    {
        "id": "business_advisor",
        "name": "商业顾问",
        "description": "商业策略和决策支持专家",
        "icon": "📊",
        "suggested_tools": ["market_analysis", "financial_calculator", "trend_analysis"]
    }
]

# 自主水平定义
AUTONOMY_LEVELS = [
    {
        "value": "guided",
        "label": "引导模式",
        "description": "每步都需要用户确认",
        "icon": "🤝"
    },
    {
        "value": "semi_autonomous",
        "label": "半自主模式",
        "description": "关键决策需要确认",
        "icon": "⚡"
    },
    {
        "value": "autonomous",
        "label": "自主模式",
        "description": "完全自主执行",
        "icon": "🚀"
    }
] 