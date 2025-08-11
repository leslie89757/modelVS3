import { useState, useRef, useEffect } from 'react'
import { Send, Bot, ChevronDown, Share2, MoreVertical } from 'lucide-react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'
import MessageBubble from './MessageBubble'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  tool_calls?: any[]
}

interface Agent {
  id: string
  name: string
  description: string
  avatar?: string
  status: string
  system_config?: {
    conversation_starters?: string[]
  }
}

interface MobileAgentChatProps {
  agent: Agent
  onBack?: () => void
  isPublic?: boolean
}

export default function MobileAgentChat({ agent, onBack, isPublic = false }: MobileAgentChatProps) {
  const api = useApi()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      created_at: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await api.post('/api/v1/runs/', {
        agent_id: agent.id,
        messages: [...messages, userMessage].map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        stream: false
      }, {
        skipAuth: isPublic
      })

      const runData = await response.json()
      if (runData.response && runData.response.content) {
        const newMessage: Message = {
          id: Date.now().toString() + '_assistant',
          role: 'assistant',
          content: runData.response.content,
          created_at: new Date().toISOString(),
          tool_calls: runData.response.tool_calls || []
        }
        setMessages(prev => [...prev, newMessage])
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      // 错误信息已在useApi中处理
    } finally {
      setIsLoading(false)
    }
  }

  // 使用对话开启语
  const handleStarterClick = (starter: string) => {
    setInputMessage(starter)
    inputRef.current?.focus()
  }

  // 分享功能
  const handleShare = async () => {
    try {
      const shareUrl = `${window.location.origin}/marketplace`
      const shareText = `来试试 ${agent.name}，一个很棒的AI助手！`
      
      if (navigator.share) {
        await navigator.share({
          title: agent.name,
          text: shareText,
          url: shareUrl,
        })
      } else {
        await navigator.clipboard.writeText(`${shareText} ${shareUrl}`)
        toast.success('分享链接已复制')
      }
      setShowMenu(false)
    } catch (error) {
      console.error('分享失败:', error)
      toast.error('分享失败')
    }
  }

  // 处理输入框高度自适应
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  // 处理回车发送
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10 shadow-sm">
        <div className="flex items-center space-x-3 flex-1 min-w-0">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 -ml-2 text-gray-600 hover:text-gray-800 lg:hidden"
            >
              <ChevronDown className="w-5 h-5 transform rotate-90" />
            </button>
          )}
          <div className="flex items-center space-x-3 min-w-0">
            {agent.avatar ? (
              <img
                src={agent.avatar}
                alt={agent.name}
                className="w-10 h-10 rounded-full flex-shrink-0"
              />
            ) : (
              <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-6 h-6 text-primary-600" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <h1 className="text-lg font-semibold text-gray-900 truncate">{agent.name}</h1>
              <p className="text-sm text-green-600">在线</p>
            </div>
          </div>
        </div>
        
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 text-gray-600 hover:text-gray-800"
          >
            <MoreVertical className="w-5 h-5" />
          </button>
          
          {showMenu && (
            <div className="absolute right-0 top-12 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
              <button
                onClick={handleShare}
                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                <Share2 className="w-4 h-4 mr-3" />
                分享这个Agent
              </button>
              {!isPublic && (
                <button
                  onClick={() => {
                    window.open(`/marketplace`, '_blank')
                    setShowMenu(false)
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <Bot className="w-4 h-4 mr-3" />
                  浏览更多Agent
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* 欢迎消息 */}
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bot className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              你好！我是 {agent.name}
            </h3>
            <p className="text-gray-600 text-sm mb-6 max-w-sm mx-auto">
              {agent.description}
            </p>
            
            {/* 对话开启语 */}
            {agent.system_config?.conversation_starters && agent.system_config.conversation_starters.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-gray-500 mb-3">你可以尝试这些话题：</p>
                {agent.system_config.conversation_starters.slice(0, 3).map((starter, index) => (
                  <button
                    key={index}
                    onClick={() => handleStarterClick(starter)}
                    className="block w-full max-w-sm mx-auto px-4 py-3 bg-white border border-gray-200 rounded-lg text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    {starter}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 消息列表 */}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} variant="mobile" />
        ))}

        {/* 加载指示器 */}
        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-5 h-5 text-primary-600" />
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="bg-white border-t border-gray-200 px-4 py-3">
        <div className="flex items-end space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="输入你的消息..."
              className="w-full resize-none border border-gray-300 rounded-2xl px-4 py-3 pr-12 focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm max-h-[120px] min-h-[44px]"
              style={{ height: '44px' }}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className={`p-3 rounded-full transition-colors ${
              inputMessage.trim() && !isLoading
                ? 'bg-primary-500 text-white hover:bg-primary-600'
                : 'bg-gray-200 text-gray-400'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* 点击外部关闭菜单 */}
      {showMenu && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setShowMenu(false)}
        />
      )}
    </div>
  )
} 