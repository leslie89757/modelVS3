// 全局类型定义文件

// 扩展Window接口以支持gtag
declare global {
  interface Window {
    gtag?: (
      command: 'config' | 'event' | 'exception',
      targetId: string,
      config?: any
    ) => void
  }

  // 扩展ImportMeta接口以支持Vite环境变量
  interface ImportMeta {
    readonly env: ImportMetaEnv
  }

  interface ImportMetaEnv {
    readonly DEV: boolean
    readonly PROD: boolean
    readonly MODE: string
    readonly VITE_API_URL?: string
    readonly VITE_APP_TITLE?: string
    readonly BASE_URL: string
    // 其他环境变量可以在这里添加
  }
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: string
  timestamp?: string
}

// 分页响应类型
export interface PaginatedResponse<T> {
  data: T[]
  meta: {
    page: number
    per_page: number
    total: number
    pages: number
  }
}

// 用户类型
export interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  tenant_id?: string
  created_at: string
  updated_at?: string
}

// Agent类型
export interface Agent {
  id: string
  name: string
  description?: string
  avatar?: string
  category: string
  tags: string[]
  status: 'active' | 'paused' | 'draft' | 'archived'
  access_level: 'public' | 'private' | 'team'
  version?: number
  llm_config: {
    primary_model_id: string
    fallback_model_id?: string
    temperature?: number
    max_tokens?: number
    top_p?: number
    frequency_penalty?: number
    presence_penalty?: number
  }
  system_config: {
    system_prompt: string
    conversation_starters?: string[]
    response_style?: string
    max_context_turns?: number
    enable_memory?: boolean
  }
  tools_config?: {
    enabled_tools: string[]
    tool_configs: Record<string, any>
    custom_tools: any[]
  }
  knowledge_config?: {
    enabled: boolean
    documents: string[]
    retrieval_config: {
      top_k: number
      similarity_threshold: number
      rerank: boolean
    }
  }
  deployment_config?: {
    api_key?: string
    rate_limits: {
      requests_per_minute: number
      requests_per_day: number
    }
    webhook_url?: string
  }
  stats?: {
    total_conversations: number
    total_messages: number
    avg_response_time: number
    user_satisfaction: number
  }
  owner_id?: string
  created_at: string
  updated_at?: string
}

// 消息类型
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  tool_calls?: any[]
  tool_call_id?: string
  created_at: string
}

// 运行类型
export interface Run {
  id: string
  agent_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  run_metadata: {
    messages: Message[]
    stream: boolean
    max_tokens?: number
    temperature?: number
  }
  execution_time_ms?: number
  input_tokens?: number
  output_tokens?: number
  created_at: string
  completed_at?: string
  messages: Message[]
}

// 模型类型
export interface Model {
  id: string
  name: string
  provider: string
  endpoint: string
  context_len: number
  enabled: boolean
  api_key?: string
  custom_headers?: Record<string, string>
  created_at: string
  updated_at?: string
}

// 工具类型
export interface Tool {
  id: string
  name: string
  description: string
  schema: any
  endpoint?: string
  enabled: boolean
  created_at: string
  updated_at?: string
}

// 表单错误类型
export type FormErrors<T> = {
  [K in keyof T]?: string
}

// API错误类型
export interface ApiError {
  detail: string
  status_code?: number
  error_code?: string
}

export {} 