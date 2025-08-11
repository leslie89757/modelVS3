import { useState, useRef, useCallback, useEffect } from 'react'
import { processMessages, deepProcessMessages, quickProcessMessages, type ProcessedMessage } from '../utils/messageProcessor'
import { ToolCall } from '../components/ToolCallDisplay'
import toast from 'react-hot-toast'

// 统一的消息接口
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  tool_calls?: ToolCall[]
  isStreaming?: boolean
  error?: string
}

// 对话目标接口
export interface ChatTarget {
  id: string
  name: string
  type: 'model' | 'agent'
  provider?: string
  description?: string
  status?: string
  modelId?: string
}

// 对话配置接口
export interface ChatConfig {
  temperature?: number
  max_tokens?: number
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
  stream?: boolean
  model_id?: string
  temporary_config?: any
}

// Hook配置选项
export interface UseChatOptions {
  target?: ChatTarget
  config?: ChatConfig
  sessionId?: string
  messageProcessing?: 'quick' | 'deep' | 'standard'
  autoSave?: boolean
  enableHistory?: boolean
  onMessageSent?: (message: ChatMessage) => void
  onMessageReceived?: (message: ChatMessage) => void
  onError?: (error: Error) => void
}

// Hook返回值接口
export interface UseChatReturn {
  // 状态
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  target: ChatTarget | null
  
  // 操作方法
  sendMessage: (content: string, options?: Partial<ChatConfig>) => Promise<void>
  setTarget: (target: ChatTarget) => void
  clearMessages: () => void
  retryLastMessage: () => Promise<void>
  
  // 消息管理
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  deleteMessage: (id: string) => void
  
  // 工具调用相关
  getToolCallStats: () => {
    total: number
    success: number
    error: number
    running: number
  }
  
  // 引用
  messagesEndRef: React.RefObject<HTMLDivElement>
}

/**
 * 统一的对话Hook
 * 封装所有对话逻辑，支持模型和Agent对话
 */
export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const {
    target: initialTarget,
    config: defaultConfig = {},
    sessionId,
    messageProcessing = 'standard',
    autoSave = true,

    onMessageSent,
    onMessageReceived,
    onError
  } = options

  // 状态管理
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [target, setTargetState] = useState<ChatTarget | null>(initialTarget || null)
  
  // 引用
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 清除错误状态
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // 生成消息ID
  const generateMessageId = useCallback(() => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }, [])

  // 添加消息
  const addMessage = useCallback((messageData: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const message: ChatMessage = {
      ...messageData,
      id: generateMessageId(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, message])
    return message
  }, [generateMessageId])

  // 更新消息
  const updateMessage = useCallback((id: string, updates: Partial<ChatMessage>) => {
    setMessages(prev => prev.map(msg => 
      msg.id === id ? { ...msg, ...updates } : msg
    ))
  }, [])

  // 删除消息
  const deleteMessage = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id))
  }, [])

  // 清空消息
  const clearMessages = useCallback(() => {
    setMessages([])
    clearError()
  }, [clearError])

  // 设置对话目标
  const setTarget = useCallback((newTarget: ChatTarget) => {
    setTargetState(newTarget)
    if (options.target !== newTarget) {
      // 如果目标改变，清空当前消息（可选）
      // clearMessages()
    }
  }, [options.target])

  // 处理API响应消息
  const processApiResponse = useCallback((rawMessages: any[]): ChatMessage[] => {
    let processedMessages: ProcessedMessage[]
    
    // 根据配置选择处理方式
    switch (messageProcessing) {
      case 'quick':
        processedMessages = quickProcessMessages(rawMessages)
        break
      case 'deep':
        processedMessages = deepProcessMessages(rawMessages)
        break
      default:
        processedMessages = processMessages(rawMessages)
        break
    }

    // 转换为ChatMessage格式
    return processedMessages.map(msg => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp,
      tool_calls: msg.tool_calls
    }))
  }, [messageProcessing])

  // 保存消息到会话（如果启用）
  const saveMessageToSession = useCallback(async (message: ChatMessage) => {
    if (!autoSave || !sessionId) return

    try {
      await fetch(`/api/v1/chat-sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          role: message.role,
          content: message.content,
          tool_calls: message.tool_calls,
          model_used: target?.type === 'model' ? target.id : null
        })
      })
    } catch (error) {
      console.error('保存消息失败:', error)
      // 不阻断用户交互，只记录错误
    }
  }, [autoSave, sessionId, target])

  // 发送消息主函数
  const sendMessage = useCallback(async (content: string, messageConfig: Partial<ChatConfig> = {}) => {
    if (!content.trim() || !target || isLoading) return

    clearError()

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    // 合并配置
    const finalConfig = { ...defaultConfig, ...messageConfig }

    // 添加用户消息
    const userMessage = addMessage({
      role: 'user',
      content: content.trim()
    })

    onMessageSent?.(userMessage)

    // 保存用户消息
    if (autoSave) {
      await saveMessageToSession(userMessage)
    }

    // 添加loading消息
    const loadingMessage = addMessage({
      role: 'assistant',
      content: '',
      isStreaming: true
    })

    setIsLoading(true)

    try {
      let response: Response
      let apiUrl: string
      let requestBody: any

      if (target.type === 'model') {
        // 直接调用模型API
        apiUrl = '/v1/chat/completions'
        requestBody = {
          model: target.id,
          messages: messages.concat(userMessage).map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          stream: finalConfig.stream || false,
          temperature: finalConfig.temperature,
          max_tokens: finalConfig.max_tokens,
          top_p: finalConfig.top_p,
          frequency_penalty: finalConfig.frequency_penalty,
          presence_penalty: finalConfig.presence_penalty
        }
      } else {
        // 调用Agent API
        apiUrl = '/api/v1/runs/'
        requestBody = {
          agent_id: target.id,
          messages: messages.concat(userMessage).map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          stream: finalConfig.stream || false,
          model_id: finalConfig.model_id,
          temperature: finalConfig.temperature,
          max_tokens: finalConfig.max_tokens,
          temporary_config: finalConfig.temporary_config
        }
      }

      response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `API调用失败: ${response.status}`)
      }

      const result = await response.json()

      // 移除loading消息
      deleteMessage(loadingMessage.id)

      // 处理响应
      let assistantContent = ''
      let toolCalls: ToolCall[] | undefined = undefined

      if (target.type === 'model') {
        // 模型API响应格式
        assistantContent = result.choices?.[0]?.message?.content || '无回复'
        toolCalls = result.choices?.[0]?.message?.tool_calls
      } else {
        // Agent API响应格式
        if (result.messages && result.messages.length > 0) {
          // 使用消息处理器处理完整消息历史
          const processedMessages = processApiResponse(result.messages)
          const assistantMessages = processedMessages.filter(msg => msg.role === 'assistant')
          
          if (assistantMessages.length > 0) {
            const lastAssistant = assistantMessages[assistantMessages.length - 1]
            assistantContent = lastAssistant.content
            toolCalls = lastAssistant.tool_calls
          }
        } else if (result.response) {
          // 兼容旧格式
          assistantContent = result.response.content || '无回复'
          toolCalls = result.response.tool_calls
        }

        // 使用增强的工具调用数据
        if (result.response?.tool_calls && result.response.tool_calls.length > 0) {
          toolCalls = result.response.tool_calls
        }
      }

      // 添加AI回复
      const assistantMessage = addMessage({
        role: 'assistant',
        content: assistantContent,
        tool_calls: toolCalls
      })

      onMessageReceived?.(assistantMessage)

      // 保存AI消息
      if (autoSave) {
        await saveMessageToSession(assistantMessage)
      }

    } catch (error: any) {
      // 移除loading消息
      deleteMessage(loadingMessage.id)

      if (error.name === 'AbortError') {
        return // 请求被取消，不显示错误
      }

      const errorMessage = error.message || '发送失败'
      setError(errorMessage)
      onError?.(error)
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }, [
    target, isLoading, defaultConfig, messages, addMessage, deleteMessage, 
    processApiResponse, saveMessageToSession, onMessageSent, onMessageReceived, onError, clearError
  ])

  // 重试最后一条用户消息
  const retryLastMessage = useCallback(async () => {
    const lastUserMessage = [...messages].reverse().find(msg => msg.role === 'user')
    if (lastUserMessage) {
      // 移除最后的assistant消息（如果有错误）
      const lastMessage = messages[messages.length - 1]
      if (lastMessage && lastMessage.role === 'assistant' && lastMessage.error) {
        deleteMessage(lastMessage.id)
      }
      
      await sendMessage(lastUserMessage.content)
    }
  }, [messages, deleteMessage, sendMessage])

  // 获取工具调用统计
  const getToolCallStats = useCallback(() => {
    const stats = {
      total: 0,
      success: 0,
      error: 0,
      running: 0
    }

    messages.forEach(message => {
      if (message.tool_calls) {
        stats.total += message.tool_calls.length
        message.tool_calls.forEach(tc => {
          switch (tc.status) {
            case 'success':
              stats.success++
              break
            case 'error':
              stats.error++
              break
            case 'running':
              stats.running++
              break
          }
        })
      }
    })

    return stats
  }, [messages])

  // 清理资源
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    // 状态
    messages,
    isLoading,
    error,
    target,
    
    // 操作方法
    sendMessage,
    setTarget,
    clearMessages,
    retryLastMessage,
    
    // 消息管理
    addMessage,
    updateMessage,
    deleteMessage,
    
    // 工具调用相关
    getToolCallStats,
    
    // 引用
    messagesEndRef
  }
}

// 辅助Hook - 用于会话管理
export function useChatSession() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isCreatingSession, setIsCreatingSession] = useState(false)

  const createSession = useCallback(async (targetId: string, targetType: 'model' | 'agent', title?: string) => {
    setIsCreatingSession(true)
    try {
      const response = await fetch('/api/v1/chat-sessions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title || `与${targetType === 'model' ? '模型' : 'Agent'}的对话`,
          model_id: targetType === 'model' ? targetId : null,
          agent_id: targetType === 'agent' ? targetId : null,
          model_type: targetType,
          is_pinned: false,
          tags: []
        })
      })

      if (response.ok) {
        const session = await response.json()
        setSessionId(session.id)
        return session.id
      } else {
        throw new Error('创建会话失败')
      }
    } catch (error) {
      console.error('创建会话失败:', error)
      toast.error('创建会话失败')
      throw error
    } finally {
      setIsCreatingSession(false)
    }
  }, [])

  return {
    sessionId,
    createSession,
    isCreatingSession
  }
}

export default useChat 