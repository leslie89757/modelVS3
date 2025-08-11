import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home, Bug, Copy } from 'lucide-react'
import toast from 'react-hot-toast'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  showDetails?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    }
  }

  static getDerivedStateFromError(error: Error): State {
    // 生成错误ID用于追踪
    const errorId = `ERR_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    return {
      hasError: true,
      error,
      errorInfo: null,
      errorId
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    })

    // 记录错误到控制台
    console.error('🚨 [ErrorBoundary] 捕获到应用错误:', {
      error,
      errorInfo,
      errorId: this.state.errorId,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    })

    // 可以在这里添加错误上报逻辑
    this.reportError(error, errorInfo)
  }

  // 错误上报（可选）
  reportError = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      // 这里可以发送错误报告到后端
      const errorReport = {
        errorId: this.state.errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        userId: localStorage.getItem('userId') || 'anonymous'
      }

      // 发送到错误监控服务
      // await fetch('/api/v1/errors/report', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorReport)
      // })
      
      console.log('📊 [ErrorBoundary] 错误报告已准备:', errorReport)
    } catch (reportError) {
      console.error('📊 [ErrorBoundary] 错误报告发送失败:', reportError)
    }
  }

  // 重试操作
  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    })
    
    // 刷新页面作为最后的重试手段
    window.location.reload()
  }

  // 复制错误信息
  copyErrorInfo = async () => {
    try {
      const errorText = this.formatErrorForCopy()
      await navigator.clipboard.writeText(errorText)
      toast.success('错误信息已复制到剪贴板')
    } catch (error) {
      console.error('复制失败:', error)
      toast.error('复制失败')
    }
  }

  // 格式化错误信息用于复制
  formatErrorForCopy = () => {
    const { error, errorInfo, errorId } = this.state
    return `错误ID: ${errorId}
时间: ${new Date().toLocaleString()}
错误消息: ${error?.message || '未知错误'}
错误堆栈: ${error?.stack || '无堆栈信息'}
组件堆栈: ${errorInfo?.componentStack || '无组件堆栈'}
页面URL: ${window.location.href}
用户代理: ${navigator.userAgent}`
  }

  // 回到首页
  goHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback
      }

      // 默认的错误UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            {/* 错误图标 */}
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="h-8 w-8 text-red-600" />
              </div>
              <h1 className="text-xl font-bold text-gray-900 mb-2">
                哎呀，出现了错误
              </h1>
              <p className="text-gray-600 text-sm">
                应用遇到了意外错误，我们已经记录了此问题
              </p>
            </div>

            {/* 错误ID */}
            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">错误ID:</span>
                <button
                  onClick={this.copyErrorInfo}
                  className="text-xs text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                  title="复制错误信息"
                >
                  <Copy className="h-3 w-3" />
                  <span>复制</span>
                </button>
              </div>
              <code className="text-xs font-mono text-gray-800 block mt-1">
                {this.state.errorId}
              </code>
            </div>

            {/* 错误详情（开发环境或启用详情时显示） */}
            {(this.props.showDetails || import.meta.env.DEV) && (
              <div className="mb-4">
                <details className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <summary className="text-sm font-medium text-red-800 cursor-pointer flex items-center space-x-2">
                    <Bug className="h-4 w-4" />
                    <span>技术详情</span>
                  </summary>
                  <div className="mt-3 space-y-2">
                    {this.state.error && (
                      <div>
                        <p className="text-xs font-medium text-red-700">错误消息:</p>
                        <code className="text-xs text-red-600 bg-red-100 p-2 rounded block overflow-auto">
                          {this.state.error.message}
                        </code>
                      </div>
                    )}
                    {this.state.error?.stack && (
                      <div>
                        <p className="text-xs font-medium text-red-700">堆栈跟踪:</p>
                        <code className="text-xs text-red-600 bg-red-100 p-2 rounded block overflow-auto max-h-32">
                          {this.state.error.stack}
                        </code>
                      </div>
                    )}
                  </div>
                </details>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="space-y-3">
              <button
                onClick={this.handleRetry}
                className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                重新加载页面
              </button>
              
              <button
                onClick={this.goHome}
                className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Home className="h-4 w-4 mr-2" />
                返回首页
              </button>
            </div>

            {/* 帮助信息 */}
            <div className="mt-6 p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-800">
                <strong>需要帮助？</strong><br />
                如果问题持续出现，请将错误ID提供给技术支持团队，我们会尽快解决问题。
              </p>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// 函数式错误边界Hook（用于函数组件中的错误处理）
export const useErrorHandler = () => {
  const handleError = (error: Error, errorInfo?: string) => {
    console.error('🚨 [useErrorHandler] 手动处理错误:', {
      error,
      errorInfo,
      timestamp: new Date().toISOString()
    })
    
    // 显示用户友好的错误提示
    toast.error(`操作失败: ${error.message}`, {
      duration: 5000,
      position: 'top-center'
    })
  }

  return { handleError }
}

// 简单的错误页面组件
export const ErrorPage = ({ 
  message = '页面加载失败', 
  action,
  actionText = '重试'
}: {
  message?: string
  action?: () => void
  actionText?: string
}) => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="h-8 w-8 text-red-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">出现错误</h2>
        <p className="text-gray-600 mb-6">{message}</p>
        {action && (
          <button
            onClick={action}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {actionText}
          </button>
        )}
      </div>
    </div>
  )
}

export default ErrorBoundary 