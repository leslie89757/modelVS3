/**
 * 统一的消息处理工具
 * 用于处理工具调用消息的合并和显示逻辑
 * 支持多种数据来源和格式
 */

// 导入统一的工具调用接口
import { ToolCall } from '../components/ToolCallDisplay'

export interface ProcessedMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  tool_calls?: ToolCall[]
  execution_time?: number
  confidence?: number
  created_at?: string
  original_id?: string // 保留原始ID以便追踪
}

export interface RawMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  created_at: string
  tool_calls?: any[]
  tool_call_id?: string
  timestamp?: Date | string
}

/**
 * 配置选项
 */
export interface ProcessingOptions {
  filterToolMessages?: boolean      // 是否过滤掉tool消息
  mergeAssistantMessages?: boolean  // 是否合并连续的assistant消息
  enhanceToolCalls?: boolean        // 是否增强工具调用信息
  preserveOrder?: boolean           // 是否保持原始顺序
  includeTimestamps?: boolean       // 是否包含时间戳
}

/**
 * 默认处理选项
 */
const DEFAULT_OPTIONS: ProcessingOptions = {
  filterToolMessages: true,
  mergeAssistantMessages: true,
  enhanceToolCalls: true,
  preserveOrder: true,
  includeTimestamps: true
}

/**
 * 主要的消息处理函数 - 处理原始消息列表，合并工具调用信息
 * @param rawMessages 原始消息列表
 * @param options 处理选项
 * @returns 处理后的消息列表
 */
export function processMessages(
  rawMessages: RawMessage[], 
  options: Partial<ProcessingOptions> = {}
): ProcessedMessage[] {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  
  console.log('🔄 开始处理消息列表，原始消息数:', rawMessages.length)
  console.log('🎛️ 处理选项:', opts)
  
  if (!rawMessages || rawMessages.length === 0) {
    return []
  }

  let processedMessages: ProcessedMessage[] = []

  // 第一步：过滤和标准化消息
  let filteredMessages = opts.filterToolMessages 
    ? rawMessages.filter(msg => msg.role !== 'tool')
    : rawMessages

  console.log('📋 过滤后消息数:', filteredMessages.length)

  // 第二步：标准化消息格式
  const normalizedMessages = filteredMessages.map(msg => normalizeMessage(msg))

  // 第三步：处理工具调用增强
  if (opts.enhanceToolCalls) {
    processedMessages = enhanceToolCallsInMessages(normalizedMessages, rawMessages)
  } else {
    processedMessages = normalizedMessages
  }

  // 第四步：合并连续的assistant消息（如果启用）
  if (opts.mergeAssistantMessages) {
    processedMessages = mergeConsecutiveAssistantMessages(processedMessages)
  }

  // 第五步：排序（如果需要保持顺序）
  if (opts.preserveOrder) {
    processedMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
  }

  console.log('✅ 消息处理完成，最终消息数:', processedMessages.length)
  return processedMessages
}

/**
 * 标准化单个消息
 */
function normalizeMessage(msg: RawMessage): ProcessedMessage {
  // 处理时间戳
  let timestamp: Date
  if (msg.timestamp) {
    timestamp = msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
  } else if (msg.created_at) {
    timestamp = new Date(msg.created_at)
  } else {
    timestamp = new Date()
  }

  return {
    id: msg.id,
    role: msg.role as 'user' | 'assistant' | 'system',
    content: msg.content || '',
    timestamp,
    tool_calls: msg.tool_calls ? normalizeToolCalls(msg.tool_calls) : undefined,
    created_at: msg.created_at,
    original_id: msg.id
  }
}

/**
 * 标准化工具调用数据
 */
function normalizeToolCalls(toolCalls: any[]): ToolCall[] {
  return toolCalls.map((tc, index) => {
    // 处理不同的工具调用格式
    const normalized: ToolCall = {
      id: tc.id || `tool_call_${index}`,
      name: tc.name || tc.function?.name,
      function: tc.function,
      arguments: tc.arguments || tc.function?.arguments,
      result: tc.result,
      status: tc.status || 'success',
      execution_time: tc.execution_time || (tc.endTime && tc.startTime ? tc.endTime - tc.startTime : undefined),
      error_message: tc.error_message || tc.error,
      startTime: tc.startTime,
      endTime: tc.endTime,
      index: tc.index !== undefined ? tc.index : index
    }

    return normalized
  })
}

/**
 * 增强消息中的工具调用信息
 */
function enhanceToolCallsInMessages(
  messages: ProcessedMessage[], 
  allRawMessages: RawMessage[]
): ProcessedMessage[] {
  const toolMessages = allRawMessages.filter(msg => msg.role === 'tool')
  console.log('🔧 找到tool消息数:', toolMessages.length)

  return messages.map(message => {
    if (message.role === 'assistant' && message.tool_calls && message.tool_calls.length > 0) {
      console.log(`🔧 处理assistant消息的工具调用: ${message.tool_calls.length}个`)
      
      // 创建工具结果映射
      const toolResults: Record<string, any> = {}
      toolMessages.forEach(msg => {
        if (msg.tool_call_id) {
          try {
            const parsed = JSON.parse(msg.content || '{}')
            toolResults[msg.tool_call_id] = parsed
          } catch {
            toolResults[msg.tool_call_id] = msg.content
          }
        }
      })

      // 增强工具调用信息
      const enhancedToolCalls = message.tool_calls.map(toolCall => {
        const enhanced = { ...toolCall }
        
        // 如果找到对应的工具结果，增强信息
        if (toolCall.id && toolResults[toolCall.id]) {
          enhanced.result = toolResults[toolCall.id]
          enhanced.status = 'success'
          
          // 如果没有执行时间，尝试计算或使用默认值
          if (!enhanced.execution_time && !enhanced.startTime) {
            enhanced.startTime = Date.now() - 2000
            enhanced.endTime = Date.now()
            enhanced.execution_time = 2000
          }
        }

        return enhanced
      })

      return {
        ...message,
        tool_calls: enhancedToolCalls
      }
    }

    return message
  })
}

/**
 * 合并连续的assistant消息
 */
function mergeConsecutiveAssistantMessages(messages: ProcessedMessage[]): ProcessedMessage[] {
  const merged: ProcessedMessage[] = []
  
  for (let i = 0; i < messages.length; i++) {
    const currentMsg = messages[i]
    
    // 如果是assistant消息，检查是否需要合并
    if (currentMsg.role === 'assistant' && currentMsg.tool_calls && currentMsg.tool_calls.length > 0) {
      const nextMsg = messages[i + 1]
      
      // 如果下一条也是assistant消息且有内容，则合并
      if (nextMsg && nextMsg.role === 'assistant' && nextMsg.content && !nextMsg.tool_calls) {
        console.log('🔗 发现连续的assistant消息，进行合并')
        
        const mergedMessage: ProcessedMessage = {
          ...currentMsg,
          content: (currentMsg.content + '\n\n' + nextMsg.content).trim(),
          id: `${currentMsg.id}_merged_${nextMsg.id}`,
          original_id: currentMsg.original_id
        }
        
        merged.push(mergedMessage)
        i++ // 跳过下一条消息，因为已经合并
        console.log('✅ 合并完成，内容长度:', mergedMessage.content.length)
      } else {
        merged.push(currentMsg)
      }
    } else {
      merged.push(currentMsg)
    }
  }
  
  return merged
}

/**
 * 快速消息处理函数 - 用于简单场景
 * 只过滤tool消息，保持其他消息不变
 */
export function quickProcessMessages(rawMessages: RawMessage[]): ProcessedMessage[] {
  return processMessages(rawMessages, {
    filterToolMessages: true,
    mergeAssistantMessages: false,
    enhanceToolCalls: false,
    preserveOrder: true
  })
}

/**
 * 深度处理函数 - 用于复杂场景（如AgentExecute页面）
 * 启用所有增强功能
 */
export function deepProcessMessages(rawMessages: RawMessage[]): ProcessedMessage[] {
  return processMessages(rawMessages, {
    filterToolMessages: true,
    mergeAssistantMessages: true,
    enhanceToolCalls: true,
    preserveOrder: true
  })
}

/**
 * 内联处理函数 - 用于紧凑显示场景
 * 简化处理，主要用于预览
 */
export function inlineProcessMessages(rawMessages: RawMessage[]): ProcessedMessage[] {
  return processMessages(rawMessages, {
    filterToolMessages: true,
    mergeAssistantMessages: false,
    enhanceToolCalls: false,
    preserveOrder: true
  })
}

/**
 * 检查消息是否包含工具调用
 */
export function hasToolCalls(message: ProcessedMessage): boolean {
  return !!(message.tool_calls && message.tool_calls.length > 0)
}

/**
 * 获取消息中的工具调用统计
 */
export function getToolCallStats(message: ProcessedMessage) {
  if (!message.tool_calls) return null
  
  const stats = {
    total: message.tool_calls.length,
    success: message.tool_calls.filter(tc => tc.status === 'success').length,
    error: message.tool_calls.filter(tc => tc.status === 'error').length,
    running: message.tool_calls.filter(tc => tc.status === 'running').length,
    pending: message.tool_calls.filter(tc => tc.status === 'pending').length,
    totalExecutionTime: message.tool_calls.reduce((total, tc) => total + (tc.execution_time || 0), 0)
  }
  
  return stats
}

/**
 * 获取消息列表的整体统计信息
 */
export function getMessagesStats(messages: ProcessedMessage[]) {
  const stats = {
    total: messages.length,
    user: messages.filter(m => m.role === 'user').length,
    assistant: messages.filter(m => m.role === 'assistant').length,
    system: messages.filter(m => m.role === 'system').length,
    withToolCalls: messages.filter(m => hasToolCalls(m)).length,
    totalToolCalls: messages.reduce((total, m) => total + (m.tool_calls?.length || 0), 0)
  }
  
  return stats
}

/**
 * 格式化消息用于显示
 */
export function formatMessageForDisplay(message: ProcessedMessage): ProcessedMessage {
  return {
    ...message,
    content: message.content?.trim() || '',
    timestamp: message.timestamp || new Date()
  }
}

/**
 * 验证消息数据完整性
 */
export function validateMessage(message: any): message is RawMessage {
  return (
    typeof message === 'object' &&
    message !== null &&
    typeof message.id === 'string' &&
    typeof message.role === 'string' &&
    ['user', 'assistant', 'system', 'tool'].includes(message.role) &&
    (typeof message.content === 'string' || message.content === null || message.content === undefined)
  )
}

/**
 * 批量验证消息列表
 */
export function validateMessages(messages: any[]): RawMessage[] {
  return messages.filter(validateMessage)
}

// 为了向后兼容，保留原有的导出
export { processMessages as filterToolMessages } 