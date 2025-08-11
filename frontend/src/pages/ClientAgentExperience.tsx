import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Send, 
  Bot, 
  User, 
  ArrowLeft, 
  ExternalLink,
  Loader2,

  Settings,
  RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useChat, useChatSession, type ChatTarget } from '../hooks/useChat'
import { ToolCallDisplay } from '../components/ToolCallDisplay'

interface Agent {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  status: 'active' | 'paused' | 'draft'
  visibility: 'public' | 'private' | 'organization'
  is_featured: boolean
  
  llm_config: {
    primary_model_id: string
    temperature: number
    max_tokens: number
    top_p: number
    frequency_penalty: number
    presence_penalty: number
  }
  
  system_config: {
    system_prompt: string
    conversation_starters: string[]
    response_style: string
    max_context_turns: number
    enable_memory: boolean
  }
  
  tools_config: {
    enabled_tools: string[]
    tool_configs: Record<string, any>
  }
  
  created_at: string
  updated_at: string
}

export default function ClientAgentExperience() {
  const { agentId } = useParams<{ agentId: string }>()
  const navigate = useNavigate()
  
  const [agent, setAgent] = useState<Agent | null>(null)
  const [isLoadingAgent, setIsLoadingAgent] = useState(true)
  const [inputMessage, setInputMessage] = useState('')
  const [showSettings, setShowSettings] = useState(false)

  // 会话管理
  const { sessionId, createSession, isCreatingSession } = useChatSession()

  // 使用统一的Chat Hook
  const {
    messages,
    isLoading,
    error,
    target,
    sendMessage,
    setTarget,
    clearMessages,
    retryLastMessage,
    messagesEndRef
  } = useChat({
    messageProcessing: 'deep', // 使用深度处理以获得最佳体验
    autoSave: !!sessionId,
    sessionId: sessionId || undefined,
    onError: (error) => {
      console.error('对话错误:', error)
    },
    onMessageReceived: (message) => {
      // 可以在这里添加特殊的处理逻辑，比如分析等
      console.log('收到AI回复:', message)
    }
  })

  // 加载Agent信息
  const loadAgent = async () => {
    try {
      setIsLoadingAgent(true)
      const response = await fetch(`/api/v1/agents/${agentId}`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const agentData = await response.json()
      
      // 检查Agent是否公开
      if (agentData.visibility !== 'public' && agentData.status !== 'active') {
        throw new Error('该Agent不是公开访问的')
      }
      
      setAgent(agentData)
      
      // 设置对话目标
      const chatTarget: ChatTarget = {
        id: agentData.id,
        name: agentData.name,
        type: 'agent',
        description: agentData.description,
        status: agentData.status
      }
      setTarget(chatTarget)
      
    } catch (error) {
      console.error('加载Agent失败:', error)
      toast.error('无法加载Agent信息，请检查Agent是否存在或已公开')
    } finally {
      setIsLoadingAgent(false)
    }
  }

  // 初始化会话
  const initializeSession = async () => {
    if (!agent || sessionId) return
    
    try {
      const newSessionId = await createSession(
        agent.id,
        'agent',
        `与${agent.name}的对话`
      )
      console.log('创建会话成功:', newSessionId)
    } catch (error) {
      console.error('创建会话失败:', error)
      // 不阻塞用户使用，只是不会保存对话历史
    }
  }

  useEffect(() => {
    if (agentId) {
      loadAgent()
    }
  }, [agentId])

  useEffect(() => {
    if (agent && !isCreatingSession) {
      initializeSession()
    }
  }, [agent, isCreatingSession])

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !target || isLoading) return

    await sendMessage(inputMessage.trim())
    setInputMessage('')
  }

  // 开始新对话
  const startNewConversation = () => {
    clearMessages()
    toast.success('已开始新对话')
  }

  // 获取对话启动建议
  const getConversationStarters = () => {
    if (!agent?.system_config?.conversation_starters) return []
    return agent.system_config.conversation_starters.slice(0, 4) // 最多显示4个
  }

  const conversationStarters = getConversationStarters()

  if (isLoadingAgent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">加载Agent信息中...</p>
        </div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <Bot className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">Agent不存在</h3>
          <p className="text-gray-600 mb-6">
            请检查Agent ID是否正确，或该Agent是否已公开访问
          </p>
          <div className="space-y-2">
            <button
              onClick={() => navigate('/marketplace')}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              返回Agent市场
            </button>
            <button
              onClick={() => navigate('/')}
              className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              返回首页
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶部导航 */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            
            <div>
              <div className="flex items-center space-x-3">
                <Bot className="h-6 w-6 text-blue-600" />
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">{agent.name}</h1>
                  <p className="text-sm text-gray-500">{agent.description}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2 mt-2">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  agent.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {agent.status}
                </span>
                
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                  {agent.category}
                </span>
                
                {agent.is_featured && (
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                    精选
                  </span>
                )}
                
                {agent.tags.slice(0, 3).map((tag) => (
                  <span key={tag} className="px-2 py-1 text-xs text-gray-600 bg-gray-100 rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="设置"
            >
              <Settings className="h-5 w-5" />
            </button>
            
            <button
              onClick={startNewConversation}
              className="flex items-center px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              新对话
            </button>
            
            <button
              onClick={() => navigate('/marketplace')}
              className="flex items-center px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              更多Agent
            </button>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 mx-4 mt-4 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <p className="text-red-700 text-sm">{error}</p>
            <button 
              onClick={retryLastMessage}
              className="text-red-600 hover:text-red-800 underline text-sm"
            >
              重试
            </button>
          </div>
        </div>
      )}

      {/* 设置面板 */}
      {showSettings && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-3">
          <div className="max-w-4xl mx-auto">
            <h3 className="text-sm font-medium text-blue-900 mb-2">Agent配置信息</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-blue-700">主模型:</span>
                <div className="font-medium text-blue-900">{agent.llm_config.primary_model_id}</div>
              </div>
              <div>
                <span className="text-blue-700">温度:</span>
                <div className="font-medium text-blue-900">{agent.llm_config.temperature}</div>
              </div>
              <div>
                <span className="text-blue-700">最大Token:</span>
                <div className="font-medium text-blue-900">{agent.llm_config.max_tokens}</div>
              </div>
              <div>
                <span className="text-blue-700">启用工具:</span>
                <div className="font-medium text-blue-900">{agent.tools_config.enabled_tools.length} 个</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 主对话区域 */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 ? (
            // 欢迎界面
            <div className="text-center space-y-6">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                <Bot className="h-10 w-10 text-blue-600" />
              </div>
              
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  你好！我是 {agent.name}
                </h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  {agent.description}
                </p>
              </div>

              {/* 对话启动建议 */}
              {conversationStarters.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-medium text-gray-900">你可以这样开始对话：</h3>
                  <div className="grid gap-3 max-w-2xl mx-auto">
                    {conversationStarters.map((starter, index) => (
                      <button
                        key={index}
                        onClick={() => setInputMessage(starter)}
                        className="p-4 text-left bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                      >
                        <p className="text-gray-900">{starter}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            // 对话消息
            <div className="space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex space-x-3 max-w-3xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                      message.role === 'user' ? 'bg-blue-600' : 'bg-gray-600'
                    }`}>
                      {message.role === 'user' ? (
                        <User className="h-5 w-5 text-white" />
                      ) : (
                        <Bot className="h-5 w-5 text-white" />
                      )}
                    </div>
                    
                    <div className={`flex-1 px-6 py-4 rounded-2xl ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-white border border-gray-200 text-gray-900'
                    }`}>
                      {message.role === 'user' ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      ) : message.isStreaming ? (
                        // 显示loading效果
                        <div className="flex items-center space-x-2 text-gray-500">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>正在思考中...</span>
                        </div>
                      ) : (
                        <div>
                          {/* 消息内容 */}
                          {message.content && (
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
                            </div>
                          )}
                          
                          {/* 工具调用展示 - 使用统一的组件 */}
                          {message.tool_calls && message.tool_calls.length > 0 && (
                            <ToolCallDisplay 
                              toolCalls={message.tool_calls} 
                              variant="default"
                              showStats={true}
                              allowExpand={true}
                              defaultExpanded={false}
                            />
                          )}
                        </div>
                      )}
                      
                      <div className="flex items-center justify-between mt-3 text-xs opacity-70">
                        <span>{message.timestamp.toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className="px-4 py-4 bg-white border-t border-gray-200">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage()
                  }
                }}
                placeholder={`与${agent.name}对话...`}
                className="w-full p-4 pr-12 border border-gray-300 rounded-2xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                rows={2}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="p-4 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
          
          {/* 提示信息 */}
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span>按 Enter 发送，Shift + Enter 换行</span>
            {sessionId ? (
              <span className="text-green-600">✓ 对话已保存</span>
            ) : (
              <span className="text-orange-600">! 对话不会保存</span>
            )}
          </div>
        </div>
      </div>

      {/* 底部信息 */}
      <div className="bg-gray-100 px-4 py-3 text-center">
        <p className="text-xs text-gray-500">
          由 {agent.name} 提供服务 • 最后更新: {new Date(agent.updated_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  )
} 