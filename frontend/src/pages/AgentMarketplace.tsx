import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Search, 
  Filter, 
  Star, 
  Users, 
  Play, 
  Share2, 
  Tag,
  Clock,
  TrendingUp,
  Bot,
  Eye,
  MessageSquare
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'

interface Agent {
  id: string
  name: string
  description: string
  avatar?: string
  category: string
  tags: string[]
  access_level: string
  status: string
  created_at: string
  updated_at?: string
  stats: {
    total_conversations: number
    total_messages: number
    avg_response_time: number
    user_satisfaction: number
  }
  system_config: {
    system_prompt: string
    conversation_starters: string[]
    response_style: string
  }
}

interface AgentStats {
  total_runs: number
  successful_runs: number
  success_rate: number
}

export default function AgentMarketplace() {
  const navigate = useNavigate()
  const api = useApi()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [agentStats, setAgentStats] = useState<Record<string, AgentStats>>({})

  const categories = [
    '全部',
    '助手', 
    '客服',
    '教育',
    '创作',
    '分析',
    '娱乐',
    '工具',
    '其他'
  ]

  useEffect(() => {
    loadPublicAgents()
  }, [selectedCategory])

  const loadPublicAgents = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (selectedCategory && selectedCategory !== '全部') {
        params.append('category', selectedCategory)
      }

      const response = await api.get(`/api/v1/agents/public?${params}`, { 
        skipAuth: true, 
        skipToast: true 
      })
      const data = await response.json()
      setAgents(data)
      
      // 加载每个Agent的统计信息
      for (const agent of data) {
        loadAgentStats(agent.id)
      }
    } catch (error) {
      console.error('加载Agent错误:', error)
      toast.error('加载Agent失败')
    } finally {
      setLoading(false)
    }
  }

  const loadAgentStats = async (agentId: string) => {
    try {
      const response = await api.get(`/api/v1/agents/${agentId}/stats`, { 
        skipAuth: true, 
        skipToast: true 
      })
      const data = await response.json()
      setAgentStats(prev => ({
        ...prev,
        [agentId]: data.data
      }))
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  }

  const handleTryAgent = (agent: Agent) => {
    // 跳转到客户端体验页面
    navigate(`/experience/${agent.id}`)
  }



  const handleShareAgent = async (agent: Agent) => {
    try {
      const response = await api.get(`/api/v1/agents/${agent.id}/share-link`, { 
        skipAuth: true 
      })
      const data = await response.json()
      const shareUrl = `${window.location.origin}${data.data.share_link}`
      
      if (navigator.share) {
        await navigator.share({
          title: `试用 ${agent.name} - ModelVS3`,
          text: agent.description,
          url: shareUrl,
        })
      } else {
        await navigator.clipboard.writeText(shareUrl)
        toast.success('分享链接已复制到剪贴板')
      }
    } catch (error) {
      console.error('分享失败:', error)
      // 错误信息已在useApi中处理
    }
  }

  const filteredAgents = agents.filter(agent => 
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN')
  }

  const getStarRating = (satisfaction: number) => {
    const stars = Math.round(satisfaction / 20) // 转换为5星制
    return Array.from({ length: 5 }, (_, i) => (
      <Star 
        key={i} 
        className={`w-4 h-4 ${i < stars ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} 
      />
    ))
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }



  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部区域 */}
      <div className="bg-gradient-to-r from-primary-600 to-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">🤖 Agent 市场</h1>
            <p className="text-xl text-primary-100">
              发现和体验社区创建的智能 Agent
            </p>
            <div className="mt-8 max-w-md mx-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="搜索 Agent..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-white focus:border-transparent text-gray-900"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 分类筛选 */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            分类筛选
          </h2>
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category === '全部' ? '' : category)}
                className={`px-4 py-2 rounded-full border transition-colors ${
                  (selectedCategory === category) || (selectedCategory === '' && category === '全部')
                    ? 'bg-primary-500 text-white border-primary-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-primary-300'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Agent网格 */}
        {filteredAgents.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无Agent</h3>
            <p className="text-gray-500">
              {searchTerm ? '没有找到匹配的Agent' : '这个分类下还没有公开的Agent'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAgents.map((agent) => {
              const stats = agentStats[agent.id]
              return (
                <div
                  key={agent.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow overflow-hidden"
                >
                  {/* Agent头部 */}
                  <div className="p-6 pb-4">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center">
                        {agent.avatar ? (
                          <img
                            src={agent.avatar}
                            alt={agent.name}
                            className="w-12 h-12 rounded-full mr-3"
                          />
                        ) : (
                          <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-blue-500 rounded-full flex items-center justify-center mr-3">
                            <Bot className="w-6 h-6 text-white" />
                          </div>
                        )}
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                          <span className="text-sm text-gray-500">{agent.category}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleShareAgent(agent)}
                        className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                        title="分享"
                      >
                        <Share2 className="w-4 h-4" />
                      </button>
                    </div>

                    <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                      {agent.description}
                    </p>

                    {/* 标签 */}
                    {agent.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-4">
                        {agent.tags.slice(0, 3).map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                          >
                            <Tag className="w-3 h-3 mr-1" />
                            {tag}
                          </span>
                        ))}
                        {agent.tags.length > 3 && (
                          <span className="text-xs text-gray-500">
                            +{agent.tags.length - 3}个标签
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* 统计信息 */}
                  {stats && (
                    <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="flex items-center text-gray-600">
                          <Play className="w-4 h-4 mr-1" />
                          <span>{stats.total_runs} 次使用</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          <span>{stats.success_rate}% 成功率</span>
                        </div>
                      </div>
                      {agent.stats.user_satisfaction > 0 && (
                        <div className="flex items-center mt-2">
                          <div className="flex">
                            {getStarRating(agent.stats.user_satisfaction)}
                          </div>
                          <span className="ml-2 text-xs text-gray-500">
                            ({Math.round(agent.stats.user_satisfaction)}%)
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 操作按钮 */}
                  <div className="px-6 py-4 bg-white">
                    <div className="flex space-x-3">
                      <button
                        onClick={() => handleTryAgent(agent)}
                        className="flex-1 bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                      >
                        <MessageSquare className="w-4 h-4 inline mr-2" />
                        立即体验
                      </button>
                      <button
                        onClick={() => navigate(`/agent-details/${agent.id}`)}
                        className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm"
                      >
                        <Eye className="w-4 h-4 inline mr-1" />
                        详情
                      </button>
                    </div>
                  </div>

                  {/* 创建时间 */}
                  <div className="px-6 py-2 text-xs text-gray-500 border-t border-gray-100">
                    <Clock className="w-3 h-3 inline mr-1" />
                    发布于 {formatTime(agent.created_at)}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* 统计信息 */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-center px-6 py-3 bg-white rounded-full shadow-sm border border-gray-200">
            <Users className="w-5 h-5 text-gray-400 mr-2" />
            <span className="text-gray-600">
              共发现 <span className="font-semibold text-primary-600">{filteredAgents.length}</span> 个公开 Agent
            </span>
          </div>
        </div>
      </div>
    </div>
  )
} 