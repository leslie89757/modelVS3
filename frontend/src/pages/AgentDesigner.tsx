import { useState, useEffect, useRef } from 'react'
import { 
  Save, 
  Settings,
  Brain,
  Zap,
  MessageSquare,
  User,
  Bot,
  Send,
  ChevronDown,
  ChevronUp,
  Loader2,
  Clock,
  CheckCircle,
  AlertCircle,
  Wrench,
  Database,

} from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { processMessages } from '../utils/messageProcessor'
import { ToolCallDisplay } from '../components/ToolCallDisplay'

// 接口定义
interface Agent {
  id?: string
  name: string
  description: string
  category: string
  tags: string[]
  status: 'active' | 'paused' | 'draft'
  access_level: 'public' | 'private' | 'team'
  
  llm_config: {
    primary_model_id: string
    fallback_model_id?: string
    temperature: number
    max_tokens: number
    top_p: number
    frequency_penalty: number
    presence_penalty: number
  }
  
  system_config: {
    system_prompt: string
    conversation_starters: string[]
    response_style: 'formal' | 'casual' | 'technical' | 'creative'
    max_context_turns: number
    enable_memory: boolean
  }
  
  tools_config: {
    enabled_tools: string[]
    tool_configs: Record<string, any>
    custom_tools: any[]
  }
  
  knowledge_config: {
    enabled: boolean
    documents: string[]
    retrieval_config: {
      top_k: number
      similarity_threshold: number
      rerank: boolean
    }
  }
  
  deployment_config: {
    api_key?: string
    rate_limits: {
      requests_per_minute: number
      requests_per_day: number
    }
    webhook_url?: string
  }
}

interface Model {
  id: string
  name: string
  provider: string
  context_len: number
}

interface Tool {
  id: string
  name: string
  description: string
  category: string
  parameters: any
  schema?: any
}

interface DebugMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: Date
  isStreaming?: boolean
  tool_calls?: ToolCall[]
  execution_time?: number
  confidence?: number
}

interface ToolCall {
  id: string
  name: string
  arguments: any
  result?: any
  status: 'pending' | 'running' | 'success' | 'error'
  execution_time?: number
  error_message?: string
}

const categories = [
  '客户服务', '数据分析', '内容创作', '编程助手', 
  '教育培训', '销售营销', '项目管理', '法律咨询',
  '医疗健康', '金融理财', '设计创意', '其他'
]

const responseStyles = [
  { value: 'formal', label: '正式专业', desc: '使用正式、专业的语言风格' },
  { value: 'casual', label: '轻松友好', desc: '使用轻松、友好的对话风格' },
  { value: 'technical', label: '技术专业', desc: '注重技术细节和准确性' },
  { value: 'creative', label: '创意灵活', desc: '富有创意和想象力的表达' }
]

export default function AgentDesigner() {
  // 基础数据状态
  const [models, setModels] = useState<Model[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  
  // Agent配置状态
  const [agentConfig, setAgentConfig] = useState<Agent>({
    name: '',
    description: '',
    category: categories[0],
    tags: [],
    status: 'active',
    access_level: 'private',
    llm_config: {
      primary_model_id: '',
      temperature: 0.7,
      max_tokens: 2000,
      top_p: 0.9,
      frequency_penalty: 0,
      presence_penalty: 0
    },
    system_config: {
      system_prompt: '',
      conversation_starters: [],
      response_style: 'formal',
      max_context_turns: 10,
      enable_memory: true
    },
    tools_config: {
      enabled_tools: [],
      tool_configs: {},
      custom_tools: []
    },
    knowledge_config: {
      enabled: false,
      documents: [],
      retrieval_config: {
        top_k: 5,
        similarity_threshold: 0.7,
        rerank: true
      }
    },
    deployment_config: {
      rate_limits: {
        requests_per_minute: 60,
        requests_per_day: 1000
      }
    }
  })

  // 调试对话状态
  const [debugMessages, setDebugMessages] = useState<DebugMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isDebugging, setIsDebugging] = useState(false)
  const [currentAgentId, setCurrentAgentId] = useState<string | null>(null)
  
  // UI状态
  const [activeSection, setActiveSection] = useState('basic')
  const [showToolDetails, setShowToolDetails] = useState<Record<string, boolean>>({})
  const [isSaving, setIsSaving] = useState(false)
  const [autoSave, setAutoSave] = useState(true)
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 初始化加载数据
  useEffect(() => {
    loadModels()
    loadTools()
    
    // 检查URL参数是否有agent ID
    const urlParams = new URLSearchParams(window.location.search)
    const agentId = urlParams.get('id')
    if (agentId) {
      loadExistingAgent(agentId)
    }
  }, [])

  // 自动滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [debugMessages])

  // 自动保存
  useEffect(() => {
    if (autoSave && agentConfig.name && agentConfig.system_config.system_prompt && currentAgentId) {
      const timeout = setTimeout(() => {
        saveAgent(false) // 静默保存
      }, 2000)
      return () => clearTimeout(timeout)
    }
  }, [agentConfig, autoSave, currentAgentId])

  const loadModels = async () => {
    try {
      const response = await fetch('/api/v1/models?enabled=true')
      if (response.ok) {
        const data = await response.json()
        setModels(data)
        if (data.length > 0 && !agentConfig.llm_config.primary_model_id) {
          setAgentConfig(prev => ({
            ...prev,
            llm_config: {
              ...prev.llm_config,
              primary_model_id: data[0].id
            }
          }))
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      console.error('加载模型失败:', error)
      toast.error('加载模型列表失败，请刷新页面重试')
    }
  }

  const loadTools = async () => {
    try {
      const response = await fetch('/api/v1/tools')
      if (response.ok) {
        const data = await response.json()
        setTools(data)
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      console.error('加载工具失败:', error)
      toast.error('加载工具列表失败，请刷新页面重试')
    }
  }

  const loadExistingAgent = async (agentId: string) => {
    try {
      console.log('🔄 加载现有Agent:', agentId)
      const response = await fetch(`/api/v1/agents/${agentId}`)
      if (response.ok) {
        const agent = await response.json()
        console.log('✅ 成功加载Agent:', agent)
        
        // 更新Agent配置
        setAgentConfig({
          name: agent.name || '',
          description: agent.description || '',
          category: agent.category || categories[0],
          tags: agent.tags || [],
          status: agent.status || 'active',
          access_level: agent.access_level || 'private',
          llm_config: {
            primary_model_id: agent.llm_config?.primary_model_id || '',
            fallback_model_id: agent.llm_config?.fallback_model_id || '',
            temperature: agent.llm_config?.temperature || 0.7,
            max_tokens: agent.llm_config?.max_tokens || 2000,
            top_p: agent.llm_config?.top_p || 0.9,
            frequency_penalty: agent.llm_config?.frequency_penalty || 0,
            presence_penalty: agent.llm_config?.presence_penalty || 0
          },
          system_config: {
            system_prompt: agent.system_config?.system_prompt || '',
            conversation_starters: agent.system_config?.conversation_starters || [],
            response_style: agent.system_config?.response_style || 'formal',
            max_context_turns: agent.system_config?.max_context_turns || 10,
            enable_memory: agent.system_config?.enable_memory !== false
          },
          tools_config: {
            enabled_tools: agent.tools_config?.enabled_tools || [],
            tool_configs: agent.tools_config?.tool_configs || {},
            custom_tools: agent.tools_config?.custom_tools || []
          },
          knowledge_config: {
            enabled: agent.knowledge_config?.enabled || false,
            documents: agent.knowledge_config?.documents || [],
            retrieval_config: {
              top_k: agent.knowledge_config?.retrieval_config?.top_k || 5,
              similarity_threshold: agent.knowledge_config?.retrieval_config?.similarity_threshold || 0.7,
              rerank: agent.knowledge_config?.retrieval_config?.rerank !== false
            }
          },
          deployment_config: {
            api_key: agent.deployment_config?.api_key || '',
            rate_limits: {
              requests_per_minute: agent.deployment_config?.rate_limits?.requests_per_minute || 60,
              requests_per_day: agent.deployment_config?.rate_limits?.requests_per_day || 1000
            },
            webhook_url: agent.deployment_config?.webhook_url || ''
          }
        })
        
        setCurrentAgentId(agent.id)
        toast.success(`已加载Agent: ${agent.name}`)
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      console.error('加载Agent失败:', error)
      toast.error('加载Agent失败，请检查Agent ID是否正确')
    }
  }

  const saveAgent = async (showToast = true) => {
    if (!agentConfig.name.trim() || !agentConfig.system_config.system_prompt.trim()) {
      if (showToast) toast.error('请填写Agent名称和系统提示词')
      return
    }
    
    if (!agentConfig.llm_config.primary_model_id) {
      if (showToast) toast.error('请选择主要模型')
      return
    }

    setIsSaving(true)
    try {
      const url = currentAgentId 
        ? `/api/v1/agents/${currentAgentId}`
        : '/api/v1/agents'
      
      const method = currentAgentId ? 'PATCH' : 'POST'
      
      // 格式化数据以匹配后端 Pydantic 模式
      const payload = {
        name: agentConfig.name,
        description: agentConfig.description || null,
        category: agentConfig.category,
        tags: agentConfig.tags,
        access_level: agentConfig.access_level,
        status: 'active', // 保存时自动设置为激活状态以便调试
        llm_config: {
          primary_model_id: agentConfig.llm_config.primary_model_id,
          fallback_model_id: agentConfig.llm_config.fallback_model_id || null,
          temperature: agentConfig.llm_config.temperature,
          max_tokens: agentConfig.llm_config.max_tokens,
          top_p: agentConfig.llm_config.top_p,
          frequency_penalty: agentConfig.llm_config.frequency_penalty,
          presence_penalty: agentConfig.llm_config.presence_penalty
        },
        system_config: {
          system_prompt: agentConfig.system_config.system_prompt,
          conversation_starters: agentConfig.system_config.conversation_starters,
          response_style: agentConfig.system_config.response_style,
          max_context_turns: agentConfig.system_config.max_context_turns,
          enable_memory: agentConfig.system_config.enable_memory
        },
        tools_config: {
          enabled_tools: agentConfig.tools_config.enabled_tools,
          tool_configs: agentConfig.tools_config.tool_configs,
          custom_tools: agentConfig.tools_config.custom_tools
        },
        knowledge_config: {
          enabled: agentConfig.knowledge_config.enabled,
          documents: agentConfig.knowledge_config.documents,
          retrieval_config: {
            top_k: agentConfig.knowledge_config.retrieval_config.top_k,
            similarity_threshold: agentConfig.knowledge_config.retrieval_config.similarity_threshold,
            rerank: agentConfig.knowledge_config.retrieval_config.rerank
          }
        },
        deployment_config: {
          api_key: agentConfig.deployment_config.api_key || null,
          rate_limits: {
            requests_per_minute: agentConfig.deployment_config.rate_limits.requests_per_minute,
            requests_per_day: agentConfig.deployment_config.rate_limits.requests_per_day
          },
          webhook_url: agentConfig.deployment_config.webhook_url || null
        }
      }
      
      console.log('🚀 保存Agent请求:', {
        url,
        method,
        payload: JSON.stringify(payload, null, 2)
      })
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      console.log('📡 响应状态:', response.status, response.statusText)

      if (response.ok) {
        const savedAgent = await response.json()
        console.log('✅ 保存成功:', savedAgent)
        setCurrentAgentId(savedAgent.id)
        if (showToast) toast.success(currentAgentId ? '更新成功' : '创建成功')
      } else {
        let errorMessage = '保存失败'
        let errorDetail = null
        
        try {
          const errorData = await response.json()
          console.error('❌ 服务器错误响应:', {
            status: response.status,
            statusText: response.statusText,
            error: errorData
          })
          
          // 处理验证错误
          if (response.status === 422 && errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              const validationErrors = errorData.detail.map((err: any) => 
                `${err.loc?.join('.') || 'Unknown field'}: ${err.msg}`
              ).join('; ')
              errorDetail = `验证错误: ${validationErrors}`
            } else {
              errorDetail = `验证错误: ${errorData.detail}`
            }
          } else {
            errorDetail = errorData.detail || errorData.message || JSON.stringify(errorData)
          }
        } catch (parseError) {
          console.error('❌ 解析错误响应失败:', parseError)
          const textError = await response.text()
          console.error('❌ 原始错误响应:', textError)
          errorDetail = `HTTP ${response.status}: ${response.statusText}`
        }
        
        throw new Error(errorDetail || errorMessage)
      }
    } catch (error) {
      console.error('❌ 保存Agent失败:', error)
      const errorMessage = error instanceof Error ? error.message : String(error)
      console.error('❌ 错误详情:', errorMessage)
      
      if (showToast) {
        toast.error(`保存失败: ${errorMessage}`)
      }
    } finally {
      setIsSaving(false)
    }
  }

  const sendDebugMessage = async () => {
    if (!inputMessage.trim() || isDebugging) return

    // 必须先保存Agent
    if (!currentAgentId) {
      console.log('🔄 Agent未保存，正在保存...')
      await saveAgent(false)
      if (!currentAgentId) {
        console.error('❌ Agent保存失败，无法调试')
        toast.error('请先保存Agent配置')
        return
      }
    }
    
    console.log('🎯 开始调试，Agent ID:', currentAgentId)

    const userMessage: DebugMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setDebugMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsDebugging(true)

    // 创建助手消息占位符
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: DebugMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    }

    setDebugMessages(prev => [...prev, assistantMessage])

    try {
      const startTime = Date.now()
      
      // 准备请求数据
      const requestData = {
        agent_id: currentAgentId,
        messages: [...debugMessages, userMessage]
          .filter(msg => msg.role === 'user' || msg.role === 'assistant')
          .map(msg => ({
            role: msg.role,
            content: msg.content
          })),
        stream: false,
        temperature: agentConfig.llm_config.temperature,
        max_tokens: agentConfig.llm_config.max_tokens
      }
      
      console.log('🚀 调试请求数据:', {
        url: '/api/v1/runs/',
        data: requestData
      })
      
      // 调用Agent API（确保URL有尾部斜杠）
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000) // 5分钟超时
      
      const response = await fetch('/api/v1/runs/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
        signal: controller.signal
      })
      clearTimeout(timeoutId)

      if (response.ok) {
        const result = await response.json()
        const executionTime = Date.now() - startTime

        console.log('🔧 API响应详情:', result)
        console.log('🔧 messages数量:', result.messages?.length || 0)
        console.log('🔧 messages内容:', result.messages)
        
        // 特别调试工具调用相关的消息
        if (result.messages) {
          result.messages.forEach((msg: any, index: number) => {
            console.log(`🔧 消息${index}:`, {
              id: msg.id,
              role: msg.role,
              tool_calls: msg.tool_calls,
              tool_call_id: msg.tool_call_id,
              content_preview: msg.content?.substring(0, 200)
            })
          })
        }

        // 移除占位符消息
        setDebugMessages(prev => prev.filter(msg => msg.id !== assistantMessageId))

        // 🔄 使用统一的消息处理器处理完整的消息历史
        if (result.messages && result.messages.length > 0) {
          console.log('🔧 [AgentDesigner] 使用统一消息处理器处理消息')
          
          // 获取所有新的消息（排除用户消息）
          const existingMessageIds = new Set(debugMessages.map(m => m.id))
          const newRawMessages = result.messages.filter((msg: any) => 
            !existingMessageIds.has(msg.id) && msg.role !== 'user'
          )
          
          console.log('🔧 [AgentDesigner] 新消息数:', newRawMessages.length)
          
          // 使用统一的消息处理器
          const processedNewMessages = processMessages(newRawMessages)
          
          // 转换为DebugMessage格式
          const debugMessages_new = processedNewMessages.map(msg => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
            tool_calls: msg.tool_calls,
            execution_time: msg.role === 'assistant' ? executionTime : undefined
          } as DebugMessage))
          
          console.log('🔧 [AgentDesigner] 处理后的调试消息数:', debugMessages_new.length)
          
          setDebugMessages(prev => [...prev, ...debugMessages_new])
        } else if (result.response) {
          // 兼容旧格式：只有单个response
          const assistantMsg: DebugMessage = {
            id: assistantMessageId,
            role: 'assistant',
            content: result.response.content || '无回复内容',
            timestamp: new Date(),
            isStreaming: false,
            execution_time: executionTime,
            tool_calls: result.response.tool_calls ? result.response.tool_calls.map((toolCall: any) => ({
              id: toolCall.id,
              name: toolCall.function?.name || toolCall.name,
              arguments: typeof toolCall.function?.arguments === 'string' 
                ? JSON.parse(toolCall.function.arguments)
                : toolCall.function?.arguments || toolCall.arguments,
              result: toolCall.result,
              status: toolCall.status || 'success',
              execution_time: toolCall.execution_time,
              error_message: toolCall.error_message
            })) : []
          }
          
          setDebugMessages(prev => [...prev, assistantMsg])
        }

      } else {
        let errorMessage = `API调用失败: ${response.status}`
        try {
          // 先获取文本内容，避免重复读取Response body
          const textError = await response.text()
          console.error('❌ 调试API错误文本:', textError)
          
          // 尝试解析为JSON
          try {
            const errorData = JSON.parse(textError)
            console.error('❌ 调试API错误响应:', errorData)
            errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData)
          } catch (jsonError) {
            // 如果不是JSON格式，直接使用文本内容
            errorMessage = textError || errorMessage
          }
        } catch (e) {
          console.error('❌ 获取错误响应失败:', e)
          errorMessage = `API调用失败: ${response.status}`
        }
        throw new Error(errorMessage)
      }
    } catch (error) {
      console.error('调试消息发送失败:', error)
      
      // 更新错误消息
      setDebugMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? { 
              ...msg, 
              content: '抱歉，调试过程中出现错误: ' + (error instanceof Error ? error.message : '未知错误'),
              isStreaming: false
            }
          : msg
      ))
      
      toast.error('调试失败')
    } finally {
      setIsDebugging(false)
    }
  }


  const clearDebugSession = () => {
    setDebugMessages([])
    toast.success('调试会话已清空')
  }

  const updateAgentConfig = (path: string, value: any) => {
    setAgentConfig(prev => {
      const newConfig = { ...prev }
      const keys = path.split('.')
      let current: any = newConfig
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]]
      }
      
      current[keys[keys.length - 1]] = value
      return newConfig
    })
  }

  const toggleToolDetails = (toolId: string) => {
    setShowToolDetails(prev => ({
      ...prev,
      [toolId]: !prev[toolId]
    }))
  }

  // 渲染配置面板
  const renderConfigPanel = () => {
    const sections = [
      { id: 'basic', label: '基本信息', icon: Brain },
      { id: 'model', label: '模型配置', icon: Settings },
      { id: 'system', label: '系统设置', icon: MessageSquare },
      { id: 'tools', label: '工具配置', icon: Zap },
      { id: 'knowledge', label: '知识库', icon: Database }
    ]

    return (
      <div className="h-full flex flex-col bg-white">
        {/* 头部 */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Agent 设计器</h1>
              <p className="text-sm text-gray-500 mt-1">实时设计和调试您的AI助手</p>
            </div>
            <div className="flex items-center space-x-2">
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={autoSave}
                  onChange={(e) => setAutoSave(e.target.checked)}
                  className="rounded"
                />
                <span>自动保存</span>
              </label>
              <button
                onClick={() => saveAgent(true)}
                disabled={isSaving}
                className="btn-primary flex items-center space-x-2"
              >
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                <span>保存</span>
              </button>
            </div>
          </div>
        </div>

        {/* 导航标签 */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex space-x-1">
            {sections.map(section => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSection === section.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <section.icon className="h-4 w-4" />
                <span>{section.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 配置内容 */}
        <div className="flex-1 p-6 overflow-y-auto">
          {activeSection === 'basic' && renderBasicConfig()}
          {activeSection === 'model' && renderModelConfig()}
          {activeSection === 'system' && renderSystemConfig()}
          {activeSection === 'tools' && renderToolsConfig()}
          {activeSection === 'knowledge' && renderKnowledgeConfig()}
        </div>
      </div>
    )
  }

  const renderBasicConfig = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Agent名称 *
        </label>
        <input
          type="text"
          value={agentConfig.name}
          onChange={(e) => updateAgentConfig('name', e.target.value)}
          className="input w-full"
          placeholder="输入Agent名称"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          描述
        </label>
        <textarea
          value={agentConfig.description}
          onChange={(e) => updateAgentConfig('description', e.target.value)}
          className="input w-full"
          rows={3}
          placeholder="描述Agent的功能和用途"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            分类
          </label>
          <select
            value={agentConfig.category}
            onChange={(e) => updateAgentConfig('category', e.target.value)}
            className="input w-full"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            访问权限
          </label>
          <select
            value={agentConfig.access_level}
            onChange={(e) => updateAgentConfig('access_level', e.target.value)}
            className="input w-full"
          >
            <option value="private">私有</option>
            <option value="team">团队</option>
            <option value="public">公开</option>
          </select>
        </div>
      </div>
    </div>
  )

  const renderModelConfig = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          主要模型 *
        </label>
        <select
          value={agentConfig.llm_config.primary_model_id}
          onChange={(e) => updateAgentConfig('llm_config.primary_model_id', e.target.value)}
          className="input w-full"
        >
          {models.map(model => (
            <option key={model.id} value={model.id}>
              {model.name} ({model.provider})
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            温度 (Temperature): {agentConfig.llm_config.temperature}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={agentConfig.llm_config.temperature}
            onChange={(e) => updateAgentConfig('llm_config.temperature', parseFloat(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            最大令牌数
          </label>
          <input
            type="number"
            value={agentConfig.llm_config.max_tokens}
            onChange={(e) => updateAgentConfig('llm_config.max_tokens', parseInt(e.target.value))}
            className="input w-full"
            min="1"
            max="8000"
          />
        </div>
      </div>
    </div>
  )

  const renderSystemConfig = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          系统提示词 *
        </label>
        <textarea
          value={agentConfig.system_config.system_prompt}
          onChange={(e) => updateAgentConfig('system_config.system_prompt', e.target.value)}
          className="input w-full"
          rows={8}
          placeholder="定义Agent的角色、行为和能力..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          对话风格
        </label>
        <div className="grid grid-cols-2 gap-3">
          {responseStyles.map(style => (
            <label key={style.value} className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="response_style"
                value={style.value}
                checked={agentConfig.system_config.response_style === style.value}
                onChange={(e) => updateAgentConfig('system_config.response_style', e.target.value)}
                className="text-blue-600"
              />
              <div>
                <div className="font-medium text-sm">{style.label}</div>
                <div className="text-xs text-gray-500">{style.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  )

  const renderToolsConfig = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">可用工具</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {tools.map(tool => (
            <div key={tool.id} className="border border-gray-200 rounded-lg">
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-3 cursor-pointer flex-1">
                    <input
                      type="checkbox"
                      checked={agentConfig.tools_config.enabled_tools.includes(tool.id)}
                      onChange={(e) => {
                        const enabledTools = agentConfig.tools_config.enabled_tools
                        if (e.target.checked) {
                          updateAgentConfig('tools_config.enabled_tools', [...enabledTools, tool.id])
                        } else {
                          updateAgentConfig('tools_config.enabled_tools', enabledTools.filter(id => id !== tool.id))
                        }
                      }}
                      className="text-blue-600"
                    />
                    <div className="flex-1">
                      <div className="font-medium">{tool.name}</div>
                      <div className="text-sm text-gray-500">{tool.description}</div>
                      <div className="text-xs text-gray-400 mt-1">类别: {tool.category}</div>
                    </div>
                  </label>
                  
                  <button
                    onClick={() => toggleToolDetails(tool.id)}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
                  >
                    {showToolDetails[tool.id] ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                </div>

                {/* 工具详情展开 */}
                {showToolDetails[tool.id] && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">参数规范</h4>
                        <pre className="text-xs bg-gray-50 p-3 rounded-lg overflow-x-auto">
                          {JSON.stringify(tool.parameters || tool.schema, null, 2)}
                        </pre>
                      </div>
                      
                      {/* 在线测试工具的快捷入口 */}
                      {agentConfig.tools_config.enabled_tools.includes(tool.id) && (
                        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                          <span className="text-sm text-blue-700">工具已启用，可在右侧调试</span>
                          <Wrench className="h-4 w-4 text-blue-600" />
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderKnowledgeConfig = () => (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          checked={agentConfig.knowledge_config.enabled}
          onChange={(e) => updateAgentConfig('knowledge_config.enabled', e.target.checked)}
          className="text-blue-600"
        />
        <label className="font-medium">启用知识库</label>
      </div>

      {agentConfig.knowledge_config.enabled && (
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-700">
              知识库功能将在未来版本中提供更完整的文档管理和向量检索功能
            </p>
          </div>
        </div>
      )}
    </div>
  )

  // 渲染调试面板
  const renderDebugPanel = () => (
    <div className="h-full flex flex-col bg-gray-50">
      {/* 调试头部 */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg">
              <Bot className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">
                {agentConfig.name || '未命名Agent'}
              </h2>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <span>实时调试</span>
                {currentAgentId ? (
                  <span className="flex items-center space-x-1 text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    <span>已保存</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 text-yellow-600">
                    <AlertCircle className="h-3 w-3" />
                    <span>未保存</span>
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {debugMessages.length > 0 && (
              <button
                onClick={clearDebugSession}
                className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded-lg hover:bg-gray-100"
              >
                清空会话
              </button>
            )}
            <div className="text-sm text-gray-500">
              {debugMessages.length} 条消息
            </div>
          </div>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {debugMessages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">开始调试您的Agent</p>
              <p className="text-sm mt-2">输入消息测试Agent的响应效果</p>
            </div>
          </div>
        ) : (
          debugMessages.map(message => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="max-w-4xl w-full">
                <div className="flex items-start space-x-3">
                  {message.role !== 'user' && (
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'assistant' ? 'bg-blue-600' :
                      message.role === 'tool' ? 'bg-purple-600' :
                      'bg-gray-600'
                    }`}>
                      {message.role === 'assistant' ? <Bot className="h-4 w-4 text-white" /> :
                       message.role === 'tool' ? <Wrench className="h-4 w-4 text-white" /> :
                       <MessageSquare className="h-4 w-4 text-white" />}
                    </div>
                  )}
                  
                  <div className={`flex-1 ${message.role === 'user' ? 'text-right' : ''}`}>
                    <div
                      className={`inline-block p-4 rounded-lg max-w-full ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-sm'
                          : message.role === 'tool'
                          ? 'bg-purple-50 border border-purple-200 rounded-bl-sm'
                          : 'bg-white border border-gray-200 rounded-bl-sm shadow-sm'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      ) : message.role === 'tool' ? (
                        <div>
                          <div className="font-medium text-purple-800 mb-2">工具执行</div>
                          <pre className="text-sm text-purple-700 whitespace-pre-wrap overflow-x-auto">
                            {message.content}
                          </pre>
                        </div>
                      ) : (
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown
                            components={{
                              code({ inline, className, children, ...props }: any) {
                                const match = /language-(\w+)/.exec(className || '')
                                return !inline && match ? (
                                  <SyntaxHighlighter
                                    style={oneDark}
                                    language={match[1]}
                                    PreTag="div"
                                    {...props}
                                  >
                                    {String(children).replace(/\n$/, '')}
                                  </SyntaxHighlighter>
                                ) : (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                )
                              }
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                          {message.isStreaming && (
                            <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1" />
                          )}
                        </div>
                      )}

                      {/* 工具调用展示 - 使用统一的组件 */}
                      {message.tool_calls && message.tool_calls.length > 0 && (
                        <ToolCallDisplay 
                          toolCalls={message.tool_calls} 
                          variant="compact"
                          showStats={true}
                          allowExpand={true}
                          defaultExpanded={false}
                        />
                      )}
                    </div>
                    
                    {/* 消息元数据 */}
                    <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      <div className="flex items-center space-x-2">
                        {message.execution_time && (
                          <span className="flex items-center space-x-1">
                            <Clock className="h-3 w-3" />
                            <span>{message.execution_time}ms</span>
                          </span>
                        )}
                        {message.confidence && (
                          <span>信心度: {Math.round(message.confidence * 100)}%</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="p-4 bg-white border-t border-gray-200">
        <div className="flex items-end space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendDebugMessage()
                }
              }}
              placeholder="输入消息测试Agent..."
              className="w-full p-3 pr-12 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isDebugging}
            />
          </div>
          <button
            onClick={sendDebugMessage}
            disabled={!inputMessage.trim() || isDebugging}
            className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isDebugging ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
        
        {!currentAgentId && (
          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-700">
              请先填写Agent名称和系统提示词，系统将自动保存后开始调试
            </p>
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="h-screen flex bg-gray-100">
      {/* 左侧：Agent设计面板 */}
      <div className="w-1/2 border-r border-gray-300">
        {renderConfigPanel()}
      </div>
      
      {/* 右侧：实时调试面板 */}
      <div className="w-1/2">
        {renderDebugPanel()}
      </div>
    </div>
  )
}