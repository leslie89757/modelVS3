import { useState, useEffect } from 'react'
import { 
  Send, 
  Bot, 
  User, 
  Plus, 
  Search, 
  MessageSquare,
  Pin,
  Brain,
  ChevronRight,
  Trash2,
  Loader2
} from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useChat, useChatSession, type ChatTarget } from '../hooks/useChat'
import { ToolCallDisplay } from '../components/ToolCallDisplay'

// 会话接口
interface ChatSession {
  id: string
  title: string
  targetId: string
  targetType: 'model' | 'agent'
  targetName: string
  messageCount: number
  lastMessage?: string
  lastActivity: Date
  isPinned: boolean
  tags: string[]
}

export default function Chat() {
  // 状态管理
  const [targets, setTargets] = useState<ChatTarget[]>([])
  const [sessions, setSessions] = useState<ChatSession[]>([])

  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  const [inputMessage, setInputMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showNewChatModal, setShowNewChatModal] = useState(false)

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
    messageProcessing: 'deep', // 使用深度处理
    autoSave: true,
    sessionId: currentSessionId || undefined,
    onError: (error) => {
      console.error('对话错误:', error)
    }
  })

  // 会话管理Hook
  const { createSession } = useChatSession()

  // 初始化加载
  useEffect(() => {
    loadTargets()
    loadSessions()
  }, [])

  // 加载对话目标（模型和Agent）
  const loadTargets = async () => {
    try {
      const [modelsRes, agentsRes] = await Promise.all([
        fetch('/api/v1/models?enabled=true'),
        fetch('/api/v1/agents')
      ])

      const [models, agents] = await Promise.all([
        modelsRes.json(),
        agentsRes.json()
      ])

      const allTargets: ChatTarget[] = [
        ...models.map((model: any) => ({
          id: model.name, // 使用name作为id，因为API需要model name
          name: model.name,
          type: 'model' as const,
          provider: model.provider,
          description: `${model.provider} 模型`,
          modelId: model.id // 保留原始id以备用
        })),
        ...agents.filter((agent: any) => agent.status === 'active').map((agent: any) => ({
          id: agent.id,
          name: agent.name,
          type: 'agent' as const,
          description: agent.description || 'AI智能助手',
          status: agent.status
        }))
      ]

      setTargets(allTargets)
    } catch (error) {
      console.error('加载对话目标失败:', error)
      toast.error('加载失败')
    }
  }

  // 加载会话历史
  const loadSessions = async () => {
    try {
      const response = await fetch('/api/v1/chat-sessions/')
      if (response.ok) {
        const data = await response.json()
        const sessions = data.map((session: any) => ({
          id: session.id,
          title: session.title,
          targetId: session.model_type === 'model' ? session.model_id : session.agent_id,
          targetType: session.model_type as 'model' | 'agent',
          targetName: session.title, // 暂时使用title作为target name
          messageCount: 0, // TODO: 从API获取消息数量
          lastMessage: '', // TODO: 从API获取最后消息
          lastActivity: new Date(session.updated_at || session.created_at),
          isPinned: session.is_pinned,
          tags: session.tags || []
        }))
        setSessions(sessions)
      }
    } catch (error) {
      console.error('加载会话失败:', error)
    }
  }

  // 创建新对话
  const createNewChat = async (selectedTarget: ChatTarget) => {
    try {
      const sessionId = await createSession(
        selectedTarget.type === 'model' ? selectedTarget.modelId || selectedTarget.id : selectedTarget.id,
        selectedTarget.type,
        `与${selectedTarget.name}的对话`
      )

      const newSession: ChatSession = {
        id: sessionId,
        title: `与${selectedTarget.name}的对话`,
        targetId: selectedTarget.id,
        targetType: selectedTarget.type,
        targetName: selectedTarget.name,
        messageCount: 0,
        lastActivity: new Date(),
        isPinned: false,
        tags: []
      }

      setSessions(prev => [newSession, ...prev])
      setCurrentSessionId(sessionId)
      setTarget(selectedTarget)
      clearMessages()
      setShowNewChatModal(false)
      toast.success(`已创建与${selectedTarget.name}的新对话`)
    } catch (error) {
      console.error('创建会话失败:', error)
      toast.error('创建会话失败')
    }
  }

  // 选择会话
  const selectSession = async (session: ChatSession) => {
    setCurrentSessionId(session.id)
    
    // 设置对话目标
    const selectedTarget = targets.find(t => t.id === session.targetId)
    if (selectedTarget) {
      setTarget(selectedTarget)
    }
    
    // 加载会话消息
    try {
      const response = await fetch(`/api/v1/chat-sessions/${session.id}/messages`)
      if (response.ok) {
        const data = await response.json()
        // 清空当前消息，然后加载历史消息
        clearMessages()
        
        // 这里我们需要手动添加历史消息，因为useChat Hook不自动加载
        // TODO: 可以考虑在useChat中添加loadMessages方法
        console.log('加载的历史消息:', data)
      } else {
        clearMessages()
      }
    } catch (error) {
      console.error('加载消息失败:', error)
      clearMessages()
    }
  }

  // 清除当前对话目标
  const clearTarget = () => {
    setTarget({
      id: '',
      name: '',
      type: 'model'
    })
    setCurrentSessionId('')
    clearMessages()
  }

  // 删除会话
  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation() // 阻止触发选择会话
    
    if (!confirm('确定要删除这个会话吗？此操作不可恢复。')) {
      return
    }

    try {
      const response = await fetch(`/api/v1/chat-sessions/${sessionId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        // 从列表中移除会话
        setSessions(prev => prev.filter(session => session.id !== sessionId))
        
        // 如果删除的是当前会话，清空当前状态
        if (currentSessionId === sessionId) {
          clearTarget()
        }
        
        toast.success('会话已删除')
      } else {
        throw new Error('删除失败')
      }
    } catch (error) {
      console.error('删除会话失败:', error)
      toast.error('删除会话失败')
    }
  }

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !target || isLoading) return

    await sendMessage(inputMessage.trim())
    setInputMessage('')

    // 更新会话信息
    setSessions(prev => prev.map(session => 
      session.id === currentSessionId 
        ? {
            ...session,
            messageCount: session.messageCount + 2,
            lastMessage: inputMessage.trim().substring(0, 50),
            lastActivity: new Date()
          }
        : session
    ))
  }

  // 过滤目标
  const filteredTargets = targets.filter(target =>
    target.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    target.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // 过滤会话
  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.targetName.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="h-full flex bg-white">
      {/* 左侧边栏 */}
      <div className="w-80 border-r border-gray-200 flex flex-col">
        {/* 搜索和新建 */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2 mb-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索对话或目标..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={() => setShowNewChatModal(true)}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* 会话列表 */}
        <div className="flex-1 overflow-y-auto">
          {filteredSessions.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>暂无对话</p>
              <button
                onClick={() => setShowNewChatModal(true)}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800"
              >
                创建新对话
              </button>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {filteredSessions.map((session) => (
                <div
                  key={session.id}
                  className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                    currentSessionId === session.id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div onClick={() => selectSession(session)} className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        {session.targetType === 'agent' ? (
                          <Bot className="h-4 w-4 text-blue-600 flex-shrink-0" />
                        ) : (
                          <Brain className="h-4 w-4 text-green-600 flex-shrink-0" />
                        )}
                        <span className="font-medium text-sm truncate">
                          {session.targetName}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {session.lastMessage || '开始新对话...'}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-400">
                          {session.messageCount} 条消息
                        </span>
                        <span className="text-xs text-gray-400">
                          {session.lastActivity.toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1">
                      {session.isPinned && (
                        <Pin className="h-3 w-3 text-yellow-500 flex-shrink-0" />
                      )}
                    </div>
                  </div>
                  
                  {/* 删除按钮 - 鼠标悬停时显示 */}
                  <button
                    onClick={(e) => deleteSession(session.id, e)}
                    className="absolute top-2 right-2 p-1 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                    title="删除会话"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 主对话区域 */}
      <div className="flex-1 flex flex-col relative">
        {target && target.id ? (
          <>
            {/* 对话头部 */}
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center space-x-3">
                {target.type === 'agent' ? (
                  <Bot className="h-6 w-6 text-blue-600" />
                ) : (
                  <Brain className="h-6 w-6 text-green-600" />
                )}
                <div>
                  <h2 className="font-semibold text-gray-900">{target.name}</h2>
                  <p className="text-sm text-gray-500">{target.description}</p>
                </div>
              </div>
              {error && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                  {error}
                  <button 
                    onClick={retryLastMessage}
                    className="ml-2 text-red-600 hover:text-red-800 underline"
                  >
                    重试
                  </button>
                </div>
              )}
            </div>

            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-32">
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">开始对话</p>
                    <p className="text-sm mt-2">向{target.name}发送消息</p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`flex space-x-3 max-w-3xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
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
                        {message.role === 'user' ? (
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        ) : message.isStreaming ? (
                          // 显示loading效果
                          <div className="flex items-center space-x-2 text-gray-500">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>AI正在思考中...</span>
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
                              />
                            )}
                          </div>
                        )}
                        
                        <div className="flex items-center justify-between mt-2 text-xs opacity-70">
                          <span>{message.timestamp.toLocaleTimeString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 固定在底部的输入区域 */}
            <div className="absolute bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200 shadow-lg">
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
                    placeholder={`与${target.name}对话...`}
                    className="w-full p-3 pr-12 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                    rows={2}
                    disabled={isLoading}
                  />
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </div>
          </>
        ) : (
          // 没有选择目标时的欢迎页面
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageSquare className="h-24 w-24 mx-auto mb-6 opacity-50" />
              <h2 className="text-2xl font-semibold mb-2">欢迎使用模型对话</h2>
              <p className="text-lg mb-6">选择一个模型或Agent开始对话</p>
              <button
                onClick={() => setShowNewChatModal(true)}
                className="btn-primary"
              >
                <Plus className="h-4 w-4 mr-2" />
                开始新对话
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 新对话模态框 */}
      {showNewChatModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-96 overflow-hidden">
            <h3 className="text-lg font-semibold mb-4">选择对话目标</h3>
            
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜索模型或Agent..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="overflow-y-auto max-h-64 space-y-2">
              {filteredTargets.map((target) => (
                <div
                  key={target.id}
                  onClick={() => createNewChat(target)}
                  className="p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    {target.type === 'agent' ? (
                      <Bot className="h-5 w-5 text-blue-600" />
                    ) : (
                      <Brain className="h-5 w-5 text-green-600" />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{target.name}</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          target.type === 'agent' 
                            ? 'bg-blue-100 text-blue-700' 
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {target.type === 'agent' ? 'Agent' : '模型'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">{target.description}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowNewChatModal(false)
                  setSearchQuery('')
                }}
                className="btn-secondary"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}