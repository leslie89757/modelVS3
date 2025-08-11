import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2, MessageSquare, Clock, ExternalLink, Bot, User } from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useApi } from '../hooks/useApi'
import { ToolCallDisplay } from '../components/ToolCallDisplay'
import { deepProcessMessages, type RawMessage, type ProcessedMessage } from '../utils/messageProcessor'

interface Agent {
  id: string
  name: string
  description: string
  status: string
}

interface Run {
  id: string
  status: string
  execution_time_ms: number
  input_tokens?: number
  output_tokens?: number
  created_at: string
  completed_at?: string
  messages?: RawMessage[]
}

export default function AgentExecute() {
  const { agentId } = useParams<{ agentId: string }>()
  const navigate = useNavigate()
  const api = useApi()
  
  const [agent, setAgent] = useState<Agent | null>(null)
  const [runs, setRuns] = useState<Run[]>([])
  const [selectedRun, setSelectedRun] = useState<Run | null>(null)
  const [processedMessages, setProcessedMessages] = useState<ProcessedMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingAgent, setIsLoadingAgent] = useState(true)

  // 加载Agent信息
  const loadAgent = async () => {
    try {
      setIsLoadingAgent(true)
      const response = await api.get(`/api/v1/agents/${agentId}`, { 
        skipAuth: true, // 支持公开访问
        skipToast: true 
      })
      const agentData = await response.json()
      setAgent(agentData)
    } catch (error) {
      console.error('加载Agent失败:', error)
      toast.error('无法加载Agent信息，请检查Agent是否存在或已公开')
    } finally {
      setIsLoadingAgent(false)
    }
  }

  // 加载执行记录
  const loadRuns = async () => {
    try {
      setIsLoading(true)
      const response = await api.get(`/api/v1/runs?agent_id=${agentId}`, { 
        skipAuth: true, // 支持公开访问
        skipToast: true 
      })
      const data = await response.json()
      // 确保每个run都有messages数组
      const runsWithMessages = data.map((run: any) => ({
        ...run,
        messages: run.messages || []
      }))
      setRuns(runsWithMessages)
    } catch (error) {
      console.error('加载执行记录失败:', error)
      toast.error('加载执行记录失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 加载特定执行记录的详情
  const loadRunDetails = async (runId: string) => {
    try {
      const response = await api.get(`/api/v1/runs/${runId}`, { 
        skipAuth: true, // 支持公开访问
        skipToast: true 
      })
      const runData = await response.json()
      
      // 确保messages存在并处理
      const runWithMessages = {
        ...runData,
        messages: runData.messages || []
      }
      
      setSelectedRun(runWithMessages)
      
      // 使用统一的消息处理器处理消息
      if (runWithMessages.messages && runWithMessages.messages.length > 0) {
        console.log('🔄 [AgentExecute] 开始处理消息:', runWithMessages.messages.length)
        const processed = deepProcessMessages(runWithMessages.messages)
        console.log('✅ [AgentExecute] 消息处理完成:', processed.length)
        setProcessedMessages(processed)
      } else {
        setProcessedMessages([])
      }
    } catch (error) {
      console.error('加载执行详情失败:', error)
      toast.error('加载执行详情失败')
    }
  }

  // 跳转到模型对话页面
  const goToChat = () => {
    navigate('/chat')
    toast.success('请在模型对话中选择该Agent进行对话')
  }

  useEffect(() => {
    if (agentId) {
      loadAgent()
      loadRuns()
    }
  }, [agentId])

  if (isLoadingAgent) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">加载Agent信息中...</p>
        </div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Agent不存在</h3>
          <p className="text-gray-600 mb-4">请检查Agent ID是否正确，或该Agent是否已公开</p>
          <button
            onClick={() => navigate('/marketplace')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            返回Agent市场
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 顶部导航 */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/agents')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-xl font-semibold">{agent.name} - 执行记录</h1>
              <p className="text-sm text-gray-500">{agent.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={goToChat}
              className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              去对话
            </button>
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
              agent.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
            }`}>
              {agent.status}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：执行记录列表 */}
        <div className="w-96 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">执行记录 ({runs.length})</h3>
              <button
                onClick={loadRuns}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                刷新
              </button>
            </div>
            
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="ml-2 text-gray-500">加载中...</span>
              </div>
            ) : (
            <div className="space-y-2">
              {runs.map((run) => (
                <div
                  key={run.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedRun?.id === run.id
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  }`}
                    onClick={() => loadRunDetails(run.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      {new Date(run.created_at).toLocaleString()}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      run.status === 'completed' ? 'bg-green-100 text-green-800' :
                      run.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {run.status}
                    </span>
                  </div>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div className="flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                        {run.execution_time_ms || 0}ms
                      </div>
                      {(run.input_tokens || run.output_tokens) && (
                        <div className="flex items-center space-x-2">
                          <span>输入: {run.input_tokens || 0}</span>
                          <span>输出: {run.output_tokens || 0}</span>
                        </div>
                      )}
                      <div>{(run.messages || []).length} 条消息</div>
                    </div>
                  </div>
                ))}
                
                {runs.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">暂无执行记录</p>
                    <p className="text-xs mt-1">在模型对话中使用该Agent来创建记录</p>
                </div>
                )}
            </div>
            )}
          </div>
        </div>

        {/* 右侧：执行详情 */}
        <div className="flex-1 flex flex-col">
          {selectedRun ? (
            <>
              {/* 执行信息 */}
              <div className="bg-white border-b border-gray-200 p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">状态</span>
                    <div className={`font-medium ${
                      selectedRun.status === 'completed' ? 'text-green-600' :
                      selectedRun.status === 'failed' ? 'text-red-600' :
                      'text-yellow-600'
                    }`}>
                      {selectedRun.status}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">执行时间</span>
                    <div className="font-medium">{selectedRun.execution_time_ms || 0}ms</div>
                  </div>
                  <div>
                    <span className="text-gray-500">输入/输出</span>
                    <div className="font-medium">{selectedRun.input_tokens || 0} / {selectedRun.output_tokens || 0}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">创建时间</span>
                    <div className="font-medium">{new Date(selectedRun.created_at).toLocaleString()}</div>
                  </div>
                </div>
              </div>

              {/* 消息记录 */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {processedMessages.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">该执行记录暂无消息</p>
                  </div>
                ) : (
                  processedMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex space-x-3 max-w-4xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                          message.role === 'user' ? 'bg-blue-600' : 'bg-gray-600'
                        }`}>
                          {message.role === 'user' ? (
                            <User className="h-4 w-4 text-white" />
                          ) : (
                            <Bot className="h-4 w-4 text-white" />
                          )}
                        </div>
                        
                        <div className={`flex-1 px-4 py-3 rounded-lg ${
                          message.role === 'user' 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-gray-100 text-gray-900'
                        }`}>
                          {/* 消息内容 */}
                          {message.content && (
                            <div className={`${message.role === 'user' ? '' : 'prose prose-sm max-w-none'}`}>
                              {message.role === 'user' ? (
                                <p className="whitespace-pre-wrap">{message.content}</p>
                              ) : (
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
                              )}
                            </div>
                          )}
                          
                          {/* 工具调用展示 - 使用统一的组件 */}
                          {message.role === 'assistant' && message.tool_calls && message.tool_calls.length > 0 && (
                            <ToolCallDisplay 
                              toolCalls={message.tool_calls} 
                              variant="default"
                              showStats={true}
                              allowExpand={true}
                              defaultExpanded={false}
                            />
                          )}
                          
                          <div className="flex items-center justify-between mt-2 text-xs opacity-70">
                            <span>{message.timestamp.toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">选择一个执行记录查看详情</p>
                <p className="text-sm mt-2">点击左侧的执行记录来查看消息内容</p>
          </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 