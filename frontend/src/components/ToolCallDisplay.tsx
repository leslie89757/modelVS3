import { useState } from 'react'
import { 
  Wrench,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Copy,
  FileText,
  Loader2,
  Play
} from 'lucide-react'
import toast from 'react-hot-toast'

// 统一的工具调用接口
export interface ToolCall {
  id: string
  name?: string
  function?: {
    name: string
    arguments: string | any
  }
  arguments?: string | any
  result?: any
  status?: 'pending' | 'running' | 'success' | 'error'
  execution_time?: number
  error_message?: string
  startTime?: number
  endTime?: number
  index?: number
}

interface ToolCallDisplayProps {
  toolCalls: ToolCall[]
  variant?: 'default' | 'compact' | 'inline' | 'minimal'
  className?: string
  showStats?: boolean
  allowExpand?: boolean
  defaultExpanded?: boolean
  compactDefaultExpanded?: boolean
}

// 优化的工具调用显示组件 - 支持多种显示模式
export function ToolCallDisplay({ 
  toolCalls, 
  variant = 'default',
  className = '',
  showStats = true,
  allowExpand = true,
  defaultExpanded = false,
  compactDefaultExpanded = false
}: ToolCallDisplayProps) {
  const isCompact = variant === 'compact' || variant === 'minimal'
  const shouldExpand = isCompact ? compactDefaultExpanded : defaultExpanded
  
  const [expandedItems, setExpandedItems] = useState<Set<string>>(
    shouldExpand ? new Set(toolCalls.map(tc => tc.id)) : new Set()
  )
  
  if (!toolCalls || toolCalls.length === 0) {
    return null
  }
  
  const toggleExpanded = (toolCallId: string) => {
    if (!allowExpand) return
    
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(toolCallId)) {
      newExpanded.delete(toolCallId)
    } else {
      newExpanded.add(toolCallId)
    }
    setExpandedItems(newExpanded)
  }

  // 统计信息
  const stats = {
    total: toolCalls.length,
    pending: toolCalls.filter(tc => tc.status === 'pending').length,
    running: toolCalls.filter(tc => tc.status === 'running').length,
    success: toolCalls.filter(tc => tc.status === 'success').length,
    error: toolCalls.filter(tc => tc.status === 'error').length
  }

  // 总执行时间
  const totalExecutionTime = toolCalls.reduce((total, tc) => {
    if (tc.execution_time) {
      return total + tc.execution_time
    }
    if (tc.startTime && tc.endTime) {
      return total + (tc.endTime - tc.startTime)
    }
    return total
  }, 0)

  // 根据variant选择样式
  const getContainerStyle = () => {
    switch (variant) {
      case 'compact':
        return 'border border-blue-200 rounded-md bg-blue-50 p-2 mt-2'
      case 'inline':
        return 'border-l-2 border-blue-300 bg-blue-50 pl-3 py-1 mt-2'
      case 'minimal':
        return 'bg-gray-50 rounded p-2 mt-2'
      default:
        return 'border border-blue-200 rounded-lg bg-blue-50 p-4 mt-3'
    }
  }

  const getHeaderStyle = () => {
    switch (variant) {
      case 'compact':
      case 'minimal':
        return 'mb-2'
      case 'inline':
        return 'mb-1'
      default:
        return 'mb-4'
    }
  }

  const isInline = variant === 'inline'

  return (
    <div className={`${getContainerStyle()} ${className}`}>
      {/* 头部统计信息 */}
      {showStats && (
        <div className={`flex items-center justify-between ${getHeaderStyle()}`}>
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Wrench className={`${isCompact ? 'h-3 w-3' : 'h-4 w-4'} text-blue-600`} />
              <span className={`font-medium text-blue-800 ${isCompact ? 'text-xs' : 'text-sm'}`}>
                工具调用
              </span>
              <span className={`bg-blue-200 text-blue-800 px-2 py-1 rounded-full ${isCompact ? 'text-xs' : 'text-xs'} font-medium`}>
                {stats.total} 个
              </span>
            </div>
            {totalExecutionTime > 0 && !isInline && (
              <div className={`${isCompact ? 'text-xs' : 'text-xs'} text-blue-600 bg-blue-100 px-2 py-1 rounded`}>
                总耗时: {totalExecutionTime}ms
              </div>
            )}
          </div>
          
          {/* 状态统计 */}
          {!isInline && (
            <div className={`flex items-center space-x-2 ${isCompact ? 'text-xs' : 'text-xs'}`}>
              {stats.success > 0 && (
                <span className="bg-green-100 text-green-700 px-2 py-1 rounded flex items-center space-x-1">
                  <CheckCircle className="h-3 w-3" />
                  <span>{stats.success}</span>
                </span>
              )}
              {stats.running > 0 && (
                <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>{stats.running}</span>
                </span>
              )}
              {stats.error > 0 && (
                <span className="bg-red-100 text-red-700 px-2 py-1 rounded flex items-center space-x-1">
                  <XCircle className="h-3 w-3" />
                  <span>{stats.error}</span>
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* 工具调用列表 */}
      <div className={`${isInline ? 'space-y-1' : isCompact ? 'space-y-2' : 'space-y-3'}`}>
        {toolCalls.map((toolCall, index) => (
          <ToolCallItem 
            key={toolCall.id || index} 
            toolCall={toolCall} 
            index={index}
            variant={variant}
            isExpanded={expandedItems.has(toolCall.id || index.toString())}
            onToggleExpanded={() => toggleExpanded(toolCall.id || index.toString())}
            allowExpand={allowExpand}
          />
        ))}
      </div>
    </div>
  )
}

// 单个工具调用项组件 - 支持多种显示模式
function ToolCallItem({ 
  toolCall, 
  index, 
  variant = 'default',
  isExpanded, 
  onToggleExpanded,
  allowExpand = true
}: { 
  toolCall: ToolCall
  index: number
  variant?: 'default' | 'compact' | 'inline' | 'minimal'
  isExpanded: boolean
  onToggleExpanded: () => void
  allowExpand?: boolean
}) {
  const status = toolCall.status || 'success' // 默认认为成功
  const toolName = toolCall.function?.name || toolCall.name || '未知工具'
  const hasResult = toolCall.result !== undefined
  const hasError = toolCall.error_message !== undefined
  const isCompact = variant === 'compact' || variant === 'minimal'
  const isInline = variant === 'inline'

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

  const getStatusStyle = () => {
    const baseStyle = isInline ? 'border-l-4 pl-2' : 'border rounded-lg'
    switch (status) {
      case 'running':
        return `${baseStyle} ${isInline ? 'border-yellow-400' : 'border-yellow-300 bg-yellow-50'}`
      case 'success':
        return `${baseStyle} ${isInline ? 'border-green-400' : 'border-green-300 bg-green-50'}`
      case 'error':
        return `${baseStyle} ${isInline ? 'border-red-400' : 'border-red-300 bg-red-50'}`
      default:
        return `${baseStyle} ${isInline ? 'border-gray-400' : 'border-gray-300 bg-gray-50'}`
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'running': return 'text-yellow-700'
      case 'success': return 'text-green-700' 
      case 'error': return 'text-red-700'
      default: return 'text-gray-700'
    }
  }

  const getStatusIcon = () => {
    const iconSize = isCompact ? 'h-3 w-3' : 'h-4 w-4'
    switch (status) {
      case 'running':
        return <Loader2 className={`${iconSize} animate-spin text-yellow-600`} />
      case 'success':
        return <CheckCircle className={`${iconSize} text-green-600`} />
      case 'error':
        return <XCircle className={`${iconSize} text-red-600`} />
      default:
        return <Play className={`${iconSize} text-gray-600`} />
    }
  }

  // 格式化结果显示
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
              <div className="bg-gray-50 rounded p-2 max-h-64 overflow-auto w-full">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed break-words overflow-wrap-anywhere w-full">
                  {result.result}
                </pre>
              </div>
              <button
                onClick={() => copyToClipboard(result.result)}
                className="absolute bottom-1 left-1 p-1 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors z-10"
                title="复制结果"
              >
                <Copy className="h-3 w-3 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      )
    }

    // 字符串结果显示
    if (typeof result === 'string') {
      return (
        <div className="bg-white border border-gray-200 rounded p-2">
          <div className="relative">
            <div className="bg-gray-50 rounded p-2 max-h-32 overflow-auto w-full">
              <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed break-words overflow-wrap-anywhere w-full">
                {result}
              </pre>
            </div>
            <button
              onClick={() => copyToClipboard(result)}
              className="absolute bottom-1 left-1 p-1 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors z-10"
              title="复制结果"
            >
              <Copy className="h-3 w-3 text-gray-600" />
            </button>
          </div>
        </div>
      )
    }

    // JSON 对象结果显示
    const jsonString = JSON.stringify(result, null, 2)
    return (
      <div className="bg-white border border-gray-200 rounded p-2">
        <div className="relative">
          <div className="bg-gray-50 rounded p-2 max-h-32 overflow-auto w-full">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed break-words overflow-wrap-anywhere w-full">
              {jsonString}
            </pre>
          </div>
          <button
            onClick={() => copyToClipboard(jsonString)}
            className="absolute bottom-1 left-1 p-1 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors z-10"
            title="复制结果"
          >
            <Copy className="h-3 w-3 text-gray-600" />
          </button>
        </div>
      </div>
    )
  }

  // 格式化参数显示
  const formatArguments = (args: any) => {
    if (!args) return null
    
    let argsToShow = args
    if (typeof args === 'string') {
      try {
        argsToShow = JSON.parse(args)
      } catch {
        argsToShow = args
      }
    }
    
    return (
      <div className="bg-white border border-gray-200 rounded p-2">
        <div className="flex items-center space-x-2 mb-2">
          <FileText className="h-3 w-3 text-blue-600" />
          <span className="font-medium text-gray-800 text-xs">调用参数</span>
        </div>
        <div className="relative">
          <div className="bg-gray-50 rounded p-2 max-h-32 overflow-auto w-full">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed break-words overflow-wrap-anywhere w-full">
              {typeof argsToShow === 'string' ? argsToShow : JSON.stringify(argsToShow, null, 2)}
            </pre>
          </div>
          <button
            onClick={() => copyToClipboard(typeof argsToShow === 'string' ? argsToShow : JSON.stringify(argsToShow, null, 2))}
            className="absolute bottom-1 left-1 p-1 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors z-10"
            title="复制参数"
          >
            <Copy className="h-3 w-3 text-gray-600" />
          </button>
        </div>
      </div>
    )
  }

  // 内联模式的简化显示
  if (isInline) {
    return (
      <div className={`${getStatusStyle()} py-1`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span className={`text-xs font-medium ${getStatusColor()}`}>
              {toolName}
            </span>
            {toolCall.execution_time && (
              <span className="text-xs text-gray-500">
                {toolCall.execution_time}ms
              </span>
            )}
          </div>
          <span className={`text-xs ${getStatusColor()}`}>
            {status === 'pending' && '等待'}
            {status === 'running' && '运行中'}
            {status === 'success' && '成功'}
            {status === 'error' && '失败'}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className={`${getStatusStyle()} p-${isCompact ? '2' : '3'} transition-all duration-200`}>
      {/* 工具调用头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <div>
            <div className="flex items-center space-x-2">
              <span className={`font-medium ${getStatusColor()} ${isCompact ? 'text-xs' : 'text-sm'}`}>
                {toolName}
              </span>
              <span className={`${isCompact ? 'text-xs' : 'text-xs'} text-gray-500`}>#{index + 1}</span>
            </div>
            <div className={`flex items-center space-x-2 ${isCompact ? 'text-xs' : 'text-xs'} text-gray-500 mt-1`}>
              <span>状态: {status}</span>
              {(toolCall.execution_time || (toolCall.startTime && toolCall.endTime)) && (
                <>
                  <span>•</span>
                  <span>耗时: {toolCall.execution_time || (toolCall.endTime! - toolCall.startTime!)}ms</span>
                </>
              )}
            </div>
          </div>
        </div>
        
        {allowExpand && (
          <button
            onClick={onToggleExpanded}
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            title={isExpanded ? "收起详情" : "展开详情"}
          >
            {isExpanded ? (
              <ChevronUp className={`${isCompact ? 'h-3 w-3' : 'h-4 w-4'} text-gray-600`} />
            ) : (
              <ChevronDown className={`${isCompact ? 'h-3 w-3' : 'h-4 w-4'} text-gray-600`} />
            )}
          </button>
        )}
      </div>

      {/* 展开的详细信息 */}
      {isExpanded && (
        <div className={`mt-${isCompact ? '2' : '3'}`}>
          {/* 参数显示 */}
          {(toolCall.function?.arguments || toolCall.arguments) && (
            <div className={`mb-${isCompact ? '2' : '3'}`}>
              {formatArguments(toolCall.function?.arguments || toolCall.arguments)}
            </div>
          )}
          
          {/* 结果显示 */}
          {hasResult && (
            <div className={hasError ? `mb-${isCompact ? '2' : '3'}` : ''}>
              {formatResult(toolCall.result)}
            </div>
          )}
          
          {/* 错误显示 */}
          {hasError && (
            <div className="bg-red-50 border border-red-200 rounded p-2">
              <div className="flex items-center space-x-2 mb-1">
                <AlertCircle className="h-3 w-3 text-red-600" />
                <span className="text-red-800 font-medium text-xs">执行错误</span>
              </div>
              <div className="text-red-700 text-xs whitespace-pre-wrap">
                {toolCall.error_message}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ToolCallDisplay 