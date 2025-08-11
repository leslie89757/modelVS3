
import { User, Bot, Wrench, CheckCircle, XCircle, Clock, FileText, Copy } from 'lucide-react'
import toast from 'react-hot-toast'

interface ToolCall {
  index: number
  id: string
  type: string
  function: {
    name: string
    arguments: string
  }
  status?: 'success' | 'error' | 'running'
  result?: any
  startTime?: number
  endTime?: number
}

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  created_at: string
  tool_calls?: ToolCall[]
  tool_call_id?: string
}

interface MessageBubbleProps {
  message: Message
  className?: string
  variant?: 'default' | 'mobile' | 'compact'
}

export default function MessageBubble({ message, className = '', variant = 'default' }: MessageBubbleProps) {
  const isMobile = variant === 'mobile'
  
  const renderAvatar = () => {
    const avatarSize = isMobile ? 'w-8 h-8' : 'w-8 h-8'
    const iconSize = isMobile ? 'w-5 h-5' : 'w-4 h-4'
    
    if (message.role === 'user') {
      return (
        <div className={`${avatarSize} bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0`}>
          <User className={`${iconSize} text-white`} />
        </div>
      )
    } else if (message.role === 'assistant') {
      return (
        <div className={`${avatarSize} bg-gradient-to-r from-purple-500 to-blue-600 rounded-full flex items-center justify-center flex-shrink-0`}>
          <Bot className={`${iconSize} text-white`} />
        </div>
      )
    } else if (message.role === 'tool') {
      return (
        <div className={`${avatarSize} bg-green-500 rounded-full flex items-center justify-center flex-shrink-0`}>
          <Wrench className={`${iconSize} text-white`} />
        </div>
      )
    }
    return null
  }

  // 复制功能
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('已复制到剪贴板')
    } catch (err) {
      console.error('复制失败:', err)
      toast.error('复制失败')
    }
  }

  // 格式化结果显示，与AgentDesigner保持一致
  const formatResult = (result: any) => {
    if (!result) return null
    
    // 如果是奇门遁甲工具的结果结构
    if (typeof result === 'object' && result.success && result.result) {
      return (
        <div className="space-y-2">
          <div className="bg-green-50 border border-green-200 rounded p-2">
            <div className="flex items-center space-x-2 mb-1">
              <CheckCircle className="h-3 w-3 text-green-600" />
              <span className="text-green-800 font-medium text-xs">执行成功</span>
            </div>
            <div className="text-green-700 text-xs">
              状态: {result.success ? '成功' : '失败'}
            </div>
          </div>
          
          <div className="bg-white border border-gray-200 rounded p-2">
            <div className="flex items-center space-x-2 mb-2">
              <FileText className="h-3 w-3 text-blue-600" />
              <span className="font-medium text-gray-800 text-xs">详细结果</span>
            </div>
            <div className="relative">
              <div className="bg-gray-50 rounded p-2 max-h-96 overflow-y-auto">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                  {result.result}
                </pre>
              </div>
              <button
                onClick={() => copyToClipboard(result.result)}
                className="absolute bottom-2 left-2 p-1 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
                title="复制结果"
              >
                <Copy className="h-3 w-3 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      )
    }

    // 通用结果显示
    if (typeof result === 'string') {
      return (
        <div className="relative">
          <div className="bg-gray-50 rounded p-2 max-h-96 overflow-y-auto">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
              {result}
            </pre>
          </div>
          <button
            onClick={() => copyToClipboard(result)}
            className="absolute bottom-2 left-2 p-1 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
            title="复制结果"
          >
            <Copy className="h-3 w-3 text-gray-600" />
          </button>
        </div>
      )
    }

    // JSON结果显示
    const jsonString = JSON.stringify(result, null, 2)
    return (
      <div className="relative">
        <div className="bg-gray-50 rounded p-2 max-h-96 overflow-y-auto">
          <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
            {jsonString}
          </pre>
        </div>
        <button
          onClick={() => copyToClipboard(jsonString)}
          className="absolute bottom-2 left-2 p-1 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
          title="复制结果"
        >
          <Copy className="h-3 w-3 text-gray-600" />
        </button>
      </div>
    )
  }

  const renderToolCalls = () => {
    if (!message.tool_calls || message.tool_calls.length === 0) {
      return null
    }

    const isCompact = variant === 'compact'

    return (
      <div className="mt-3 space-y-2">
        <div className="flex items-center space-x-2 text-xs text-gray-600">
          <Wrench className="w-3 h-3" />
          <span>工具调用执行</span>
        </div>
        
        {message.tool_calls.map((toolCall, index) => (
          <div key={toolCall.id || index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Wrench className="w-4 h-4 text-blue-600" />
                <span className="font-medium text-sm text-gray-900">
                  {toolCall.function?.name || 'unknown'}
                </span>
              </div>
              
              <div className="flex items-center space-x-1">
                {toolCall.status === 'success' && (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                )}
                {toolCall.status === 'error' && (
                  <XCircle className="w-4 h-4 text-red-600" />
                )}
                {toolCall.status === 'running' && (
                  <Clock className="w-4 h-4 text-yellow-600 animate-spin" />
                )}
              </div>
            </div>
            
            {toolCall.startTime && toolCall.endTime && (
              <div className="text-xs text-gray-500 mb-2">
                执行时间: {toolCall.endTime - toolCall.startTime}ms
              </div>
            )}
            
            {toolCall.function?.arguments && !isCompact && (
              <details className="mt-2">
                <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800">
                  查看参数
                </summary>
                <div className="mt-1 bg-gray-100 rounded p-2">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                    {JSON.stringify(JSON.parse(toolCall.function.arguments), null, 2)}
                  </pre>
                </div>
              </details>
            )}
            
            {toolCall.result && !isCompact && (
              <details className="mt-2" open>
                <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800">
                  查看结果
                </summary>
                <div className="mt-2">
                  {formatResult(toolCall.result)}
                </div>
              </details>
            )}
          </div>
        ))}
      </div>
    )
  }

  const messageTime = new Date(message.created_at).toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })

  const isUserMessage = message.role === 'user'
  
  return (
    <div className={`flex ${isUserMessage ? 'justify-end' : 'justify-start'} ${className}`}>
      <div className={`flex items-start space-x-3 max-w-[80%] ${
        isUserMessage ? 'flex-row-reverse space-x-reverse' : ''
      }`}>
        {!isUserMessage && renderAvatar()}
        
        <div className={`px-4 py-3 rounded-2xl ${
          isUserMessage
            ? 'bg-blue-600 text-white'
            : 'bg-white/80 backdrop-blur-sm border border-gray-200 text-gray-800'
        }`}>
          {message.content && (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          )}
          
          {!isUserMessage && renderToolCalls()}
          
          <p className={`text-xs mt-2 ${
            isUserMessage ? 'text-blue-100' : 'text-gray-500'
          }`}>
            {messageTime}
          </p>
        </div>
        
        {isUserMessage && renderAvatar()}
      </div>
    </div>
  )
}

// 简化的工具调用显示组件
export function ToolCallsSummary({ toolCalls }: { toolCalls: ToolCall[] }) {
  if (!toolCalls || toolCalls.length === 0) return null

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
      <div className="flex items-center space-x-2 mb-2">
        <Wrench className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-900">工具调用</span>
      </div>
      
      <div className="space-y-1">
        {toolCalls.map((toolCall, index) => (
          <div key={toolCall.id || index} className="flex items-center justify-between text-sm">
            <span className="text-blue-800">
              {index + 1}. {toolCall.function?.name || 'unknown'}
            </span>
            <div className="flex items-center space-x-1">
              {toolCall.status === 'success' && (
                <>
                  <CheckCircle className="w-3 h-3 text-green-600" />
                  <span className="text-xs text-green-700">成功</span>
                </>
              )}
              {toolCall.status === 'error' && (
                <>
                  <XCircle className="w-3 h-3 text-red-600" />
                  <span className="text-xs text-red-700">失败</span>
                </>
              )}
              {toolCall.startTime && toolCall.endTime && (
                <span className="text-xs text-blue-600">
                  {toolCall.endTime - toolCall.startTime}ms
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
} 