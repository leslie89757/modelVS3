import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { 
  DndContext, 
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
} from '@dnd-kit/sortable'
import {
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { 
  Plus, 
  Search,
  ChevronDown,
  ChevronUp,
  GripVertical, 
  X, 
  Send, 
  RotateCcw,
  Download,
  Clock,
  Zap,
  Bot,
  User,
  AlertCircle,
  CheckCircle,
  Grid3X3,
  List,
  Maximize2,
  Minimize2,
  Brain,
  MessageSquare,
  Edit3,
  Target,
  Sparkles
} from 'lucide-react'
import toast from 'react-hot-toast'
import { ToolCallDisplay } from '../components/ToolCallDisplay'

// 类型定义
interface Agent {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  status: 'active' | 'paused' | 'draft'
  access_level: 'public' | 'private' | 'team'
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
    context_window_management: string
    response_format_instructions: string
    error_handling_instructions: string
  }
  tools_config: {
    enabled_tools: string[]
    tool_choice: string
    parallel_tool_calls: boolean
  }
}

interface Model {
  id: string
  name: string
  description: string
  provider: string
  endpoint: string
  enabled: boolean
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: Date
  tool_calls?: any[]
  isStreaming?: boolean
  execution_time?: number
}

interface ModelTestCard {
  id: string
  model: Model
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  isCollapsed: boolean
  performance: {
    responseTime: number
    tokenUsage: {
      input: number
      output: number
    }
  } | null
  position: { x: number; y: number }
}

interface WorkspaceConfig {
  layout: 'grid' | 'list'
  gridColumns: number
  showPerformanceMetrics: boolean
  autoCollapse: boolean
  searchFilter: string
  statusFilter: 'all' | 'active' | 'error' | 'loading'
}

// 可拖拽的模型测试卡片组件
function SortableModelCard({ 
  card, 
  onRemove, 
  onToggleCollapse,
  layout 
}: { 
  card: ModelTestCard
  onRemove: (id: string) => void
  onToggleCollapse: (id: string) => void
  layout: 'grid' | 'list'
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }



  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow ${
        isDragging ? 'shadow-2xl z-50' : ''
      } ${layout === 'list' ? 'mb-4' : ''}`}
    >
      {/* 卡片头部 - 可拖拽区域 */}
      <div 
        className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50 rounded-t-lg cursor-move"
        {...attributes}
        {...listeners}
      >
        <div className="flex items-center space-x-2">
          <GripVertical className="h-4 w-4 text-gray-400" />
          <Brain className="h-4 w-4 text-blue-600" />
          <div>
            <div className="font-medium text-sm">{card.model.name}</div>
            <div className="text-xs text-gray-500">{card.model.provider}</div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* 性能指标 */}
          {card.performance && (
            <div className="flex items-center space-x-3 text-xs text-gray-500">
              <span className="flex items-center">
                <Clock className="h-3 w-3 mr-1" />
                {card.performance.responseTime}ms
              </span>
              <span className="flex items-center">
                <Zap className="h-3 w-3 mr-1" />
                {card.performance.tokenUsage.input + card.performance.tokenUsage.output} tokens
              </span>
            </div>
          )}
          
          {/* 状态指示器 */}
          {card.isLoading && <Clock className="h-4 w-4 text-blue-600 animate-spin" />}
          {card.error && <AlertCircle className="h-4 w-4 text-red-600" />}
          {!card.isLoading && !card.error && card.messages.length > 0 && (
            <CheckCircle className="h-4 w-4 text-green-600" />
          )}
          
          {/* 控制按钮 */}
          <button
            onClick={() => onToggleCollapse(card.id)}
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            title={card.isCollapsed ? "展开" : "折叠"}
          >
            {card.isCollapsed ? (
              <Maximize2 className="h-3 w-3 text-gray-500" />
            ) : (
              <Minimize2 className="h-3 w-3 text-gray-500" />
            )}
          </button>
          
          <button
            onClick={() => onRemove(card.id)}
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            title="移除"
          >
            <X className="h-3 w-3 text-gray-500" />
          </button>
        </div>
      </div>

      {/* 卡片内容 */}
      {!card.isCollapsed && (
        <>
          {/* 消息列表 */}
          <div className="max-h-96 overflow-y-auto px-3 pt-3 pb-0">
            {card.messages.length === 0 ? (
              <div className="h-32 flex items-center justify-center text-gray-400 text-sm">
                等待消息...
              </div>
            ) : (
              card.messages.map((message, index) => (
                <div key={message.id} className={`flex space-x-2 ${index > 0 ? 'mt-3' : ''}`}>
                  {/* 头像 */}
                  <div className="flex-shrink-0">
                    {message.role === 'user' ? (
                      <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                        <User className="w-3 h-3 text-white" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-blue-600 rounded-full flex items-center justify-center">
                        <Bot className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </div>
                  
                  {/* 消息内容 */}
                  <div className="flex-1 min-w-0">
                    {message.content && (
                      <div className="bg-gray-50 rounded-lg p-3 text-sm prose prose-sm max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    )}
                    
                    {/* 工具调用 */}
                    {message.tool_calls && message.tool_calls.length > 0 && (
                      <div className="mt-1">
                        <ToolCallDisplay 
                          toolCalls={message.tool_calls} 
                          variant="compact"
                          showStats={false}
                          allowExpand={true}
                          defaultExpanded={false}
                          compactDefaultExpanded={false}
                        />
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-500 mt-1 flex items-center justify-between">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      {message.execution_time && (
                        <span className="flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          {message.execution_time}ms
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 错误显示 */}
          {card.error && (
            <div className="p-3 bg-red-50 border-t border-red-200">
              <div className="flex items-center space-x-2 text-red-600 text-sm">
                <AlertCircle className="h-4 w-4" />
                <span>{card.error}</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default function MultiModelTestWorkspace() {
  // 核心状态
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([])
  const [availableModels, setAvailableModels] = useState<Model[]>([])
  const [modelCards, setModelCards] = useState<ModelTestCard[]>([])
  const [inputMessage, setInputMessage] = useState('')
  
  // UI状态
  const [workspaceConfig, setWorkspaceConfig] = useState<WorkspaceConfig>({
    layout: 'grid',
    gridColumns: 2,
    showPerformanceMetrics: true,
    autoCollapse: false,
    searchFilter: '',
    statusFilter: 'all'
  })
  const [showAgentInfo, setShowAgentInfo] = useState(true)
  const [showModelSelector, setShowModelSelector] = useState(false)
  const [selectedModelIds, setSelectedModelIds] = useState<Set<string>>(new Set())
  const [showAgentEditor, setShowAgentEditor] = useState(false)
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null)

  // 拖拽传感器
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // 加载数据
  useEffect(() => {
    loadAgents()
    loadModels()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await fetch('/api/v1/agents?status=active')
      if (response.ok) {
        const agents = await response.json()
        setAvailableAgents(agents)
      }
    } catch (error) {
      console.error('加载Agent失败:', error)
      toast.error('加载Agent失败')
    }
  }

  const loadModels = async () => {
    try {
      const response = await fetch('/api/v1/models?enabled=true')
      if (response.ok) {
        const models = await response.json()
        setAvailableModels(models)
      }
    } catch (error) {
      console.error('加载模型失败:', error)
      toast.error('加载模型失败')
    }
  }



  // 批量添加模型
  const addSelectedModels = (models: Model[]) => {
    const newCards: ModelTestCard[] = []
    const existingModelIds = new Set(modelCards.map(card => card.model.id))
    
    models.forEach(model => {
      if (!existingModelIds.has(model.id)) {
        newCards.push({
          id: `card-${model.id}-${Date.now()}`,
          model,
          messages: [],
          isLoading: false,
          error: null,
          isCollapsed: false,
          performance: null,
          position: { x: 0, y: 0 }
        })
      }
    })

    if (newCards.length > 0) {
      setModelCards(prev => [...prev, ...newCards])
      setShowModelSelector(false)
      toast.success(`已添加 ${newCards.length} 个模型`)
    } else {
      toast.error('所选模型已在测试列表中')
    }
  }

  // 移除模型
  const removeModel = (cardId: string) => {
    setModelCards(prev => prev.filter(card => card.id !== cardId))
    const card = modelCards.find(c => c.id === cardId)
    if (card) {
      toast.success(`已移除 ${card.model.name}`)
    }
  }

  // 切换折叠状态
  const toggleCollapse = (cardId: string) => {
    setModelCards(prev => prev.map(card => 
      card.id === cardId 
        ? { ...card, isCollapsed: !card.isCollapsed }
        : card
    ))
  }



  // 拖拽结束处理
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      setModelCards((items) => {
        const oldIndex = items.findIndex(item => item.id === active.id)
        const newIndex = items.findIndex(item => item.id === over.id)

        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }

  // 发送消息给所有模型
  const sendToAllModels = async () => {
    if (!selectedAgent || !inputMessage.trim() || modelCards.length === 0) {
      return
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    // 添加用户消息到所有卡片
    setModelCards(prev => prev.map(card => ({
      ...card,
      messages: [...card.messages, userMessage],
      isLoading: true,
      error: null
    })))

    setInputMessage('')

    // 并发发送到所有模型
    const promises = modelCards.map(async (card) => {
      try {
        const startTime = Date.now()
        
        const requestData = {
          agent_id: selectedAgent.id,
          messages: [{ role: 'user', content: userMessage.content }],
          model_id: card.model.id,
          temperature: selectedAgent.llm_config.temperature,
          max_tokens: selectedAgent.llm_config.max_tokens,
          stream: false
        }

        const response = await fetch('/api/v1/runs/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData)
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const result = await response.json()
        const endTime = Date.now()
        
        const assistantMessage: ChatMessage = {
          id: `assistant-${card.model.id}-${Date.now()}`,
          role: 'assistant',
          content: result.response?.content || '执行完成',
          timestamp: new Date(),
          tool_calls: result.response?.tool_calls || [],
          execution_time: endTime - startTime
        }

        const performance = {
          responseTime: endTime - startTime,
          tokenUsage: {
            input: result.input_tokens || 0,
            output: result.output_tokens || 0
          }
        }

        setModelCards(prev => prev.map(c => 
          c.id === card.id 
            ? {
                ...c,
                messages: [...c.messages, assistantMessage],
                isLoading: false,
                performance: c.performance ? { ...c.performance, ...performance } : performance
              }
            : c
        ))

      } catch (error) {
        console.error(`模型 ${card.model.name} 调用失败:`, error)
        
        setModelCards(prev => prev.map(c => 
          c.id === card.id 
            ? {
                ...c,
                isLoading: false,
                error: error instanceof Error ? error.message : '调用失败'
              }
            : c
        ))
      }
    })

    await Promise.all(promises)
  }



  // 清空所有对话
  const clearAllChats = () => {
    setModelCards(prev => prev.map(card => ({
      ...card,
      messages: [],
      error: null,
      performance: card.performance ? { ...card.performance, responseTime: 0, tokenUsage: { input: 0, output: 0 } } : null
    })))
    toast.success('已清空所有对话')
  }

  // 导出测试结果
  const exportResults = () => {
    const exportData = {
      agent: selectedAgent,
      timestamp: new Date().toISOString(),
      results: modelCards.map(card => ({
        model: card.model.name,
        provider: card.model.provider,
        messages: card.messages,
        performance: card.performance,
        error: card.error
      }))
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `multi-model-test-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success('测试结果已导出')
  }

  // 过滤模型卡片
  const filteredCards = modelCards.filter(card => {
    if (workspaceConfig.searchFilter && !card.model.name.toLowerCase().includes(workspaceConfig.searchFilter.toLowerCase())) {
      return false
    }
    
    switch (workspaceConfig.statusFilter) {
      case 'active':
        return !card.isLoading && !card.error && card.messages.length > 0
      case 'error':
        return !!card.error
      case 'loading':
        return card.isLoading
      default:
        return true
    }
  })

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 顶部工具栏 */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 via-blue-500 to-green-500 rounded-xl flex items-center justify-center">
                <Target className="h-6 w-6 text-white" />
              </div>
              <Sparkles className="absolute -top-1 -right-1 h-4 w-4 text-yellow-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-green-600 bg-clip-text text-transparent">
                操练场
              </h1>
              <p className="text-sm text-gray-600">多模型对比测试工作区 · 支持拖拽排序</p>
            </div>
          </div>
          
          {/* 工具栏按钮 */}
          <div className="flex items-center space-x-3">
            {/* 搜索框 */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索模型..."
                value={workspaceConfig.searchFilter}
                onChange={(e) => setWorkspaceConfig(prev => ({ ...prev, searchFilter: e.target.value }))}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            {/* 状态筛选 */}
            <select
              value={workspaceConfig.statusFilter}
              onChange={(e) => setWorkspaceConfig(prev => ({ ...prev, statusFilter: e.target.value as any }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">全部状态</option>
              <option value="active">运行中</option>
              <option value="error">错误</option>
              <option value="loading">加载中</option>
            </select>
            
            {/* 布局切换 */}
            <div className="flex border border-gray-300 rounded-lg">
              <button
                onClick={() => setWorkspaceConfig(prev => ({ ...prev, layout: 'grid' }))}
                className={`p-2 ${workspaceConfig.layout === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setWorkspaceConfig(prev => ({ ...prev, layout: 'list' }))}
                className={`p-2 ${workspaceConfig.layout === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
            
            {/* 网格列数控制 */}
            {workspaceConfig.layout === 'grid' && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">列数:</span>
                <select
                  value={workspaceConfig.gridColumns}
                  onChange={(e) => setWorkspaceConfig(prev => ({ ...prev, gridColumns: parseInt(e.target.value) }))}
                  className="px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={1}>1列</option>
                  <option value={2}>2列</option>
                  <option value={3}>3列</option>
                  <option value={4}>4列</option>
                </select>
              </div>
            )}
            
            {/* 操作按钮 */}
            <button
              onClick={clearAllChats}
              className="flex items-center px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              清空
            </button>
            
            <button
              onClick={exportResults}
              disabled={modelCards.length === 0}
              className="flex items-center px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <Download className="h-4 w-4 mr-2" />
              导出
            </button>
          </div>
        </div>

        {/* Agent选择器 */}
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <select
              value={selectedAgent?.id || ''}
              onChange={(e) => {
                const agent = availableAgents.find(a => a.id === e.target.value)
                setSelectedAgent(agent || null)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">选择测试Agent...</option>
              {availableAgents.map(agent => (
                <option key={agent.id} value={agent.id}>{agent.name}</option>
              ))}
            </select>
          </div>
          
          <button
            onClick={() => {
              setEditingAgent(selectedAgent ? {...selectedAgent} : null)
              setShowAgentEditor(true)
            }}
            disabled={!selectedAgent}
            className="flex items-center px-3 py-2 text-purple-600 border border-purple-300 rounded-lg hover:bg-purple-50 disabled:bg-gray-100 disabled:cursor-not-allowed disabled:text-gray-400"
          >
            <Edit3 className="h-4 w-4 mr-2" />
            编辑Agent
          </button>
          
          <button
            onClick={() => setShowModelSelector(true)}
            disabled={!selectedAgent}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Plus className="h-4 w-4 mr-2" />
            添加模型
          </button>
        </div>
      </div>

      {/* Agent信息区 - 可折叠 */}
      {selectedAgent && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Bot className="h-5 w-5 text-blue-600" />
                <span className="font-medium text-blue-900">当前Agent: {selectedAgent.name}</span>
                <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                  {selectedAgent.category}
                </span>
              </div>
              <button
                onClick={() => setShowAgentInfo(!showAgentInfo)}
                className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
              >
                <span className="text-sm">{showAgentInfo ? '隐藏' : '显示'}详情</span>
                {showAgentInfo ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
            </div>
            
            <p className="text-sm text-blue-700 mb-2">{selectedAgent.description}</p>
            
            {showAgentInfo && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="bg-white rounded p-3">
                  <h4 className="font-medium text-gray-700 mb-2">LLM配置</h4>
                  <div className="space-y-1">
                    <div>温度: {selectedAgent.llm_config.temperature}</div>
                    <div>最大Token: {selectedAgent.llm_config.max_tokens}</div>
                    <div>Top-p: {selectedAgent.llm_config.top_p}</div>
                  </div>
                </div>
                <div className="bg-white rounded p-3">
                  <h4 className="font-medium text-gray-700 mb-2">系统配置</h4>
                  <div className="max-h-20 overflow-y-auto">
                    <div className="text-gray-600">{selectedAgent.system_config.system_prompt.slice(0, 100)}...</div>
                  </div>
                </div>
                <div className="bg-white rounded p-3">
                  <h4 className="font-medium text-gray-700 mb-2">工具配置</h4>
                  <div className="space-y-1">
                    <div>启用工具: {selectedAgent.tools_config.enabled_tools.length}</div>
                    <div>并行调用: {selectedAgent.tools_config.parallel_tool_calls ? '是' : '否'}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 主工作区 */}
      <div className="flex-1 overflow-hidden">
        {modelCards.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-500">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">开始多模型对比测试</h3>
              <p className="text-sm mb-4">
                {selectedAgent ? '添加模型开始测试' : '请先选择一个Agent'}
              </p>
              {selectedAgent && (
                <button
                  onClick={() => setShowModelSelector(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4 mr-2 inline" />
                  添加模型
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full p-4">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={filteredCards.map(card => card.id)}
                strategy={rectSortingStrategy}
              >
                <div 
                  className={`h-full overflow-y-auto ${
                    workspaceConfig.layout === 'grid' 
                      ? `grid gap-6` 
                      : 'space-y-4'
                  }`}
                  style={workspaceConfig.layout === 'grid' ? {
                    gridTemplateColumns: `repeat(${Math.min(filteredCards.length, workspaceConfig.gridColumns)}, 1fr)`,
                    minHeight: 'min-content',
                    alignContent: 'start'
                  } : {}}
                >
                  {filteredCards.map((card) => (
                    <SortableModelCard
                      key={card.id}
                      card={card}
                      onRemove={removeModel}
                      onToggleCollapse={toggleCollapse}
                      layout={workspaceConfig.layout}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </div>
        )}
      </div>

      {/* 底部输入区 */}
      {selectedAgent && modelCards.length > 0 && (
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendToAllModels()
                  }
                }}
                placeholder="输入测试消息，将发送给所有模型进行对比..."
                className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
              />
            </div>
            <button
              onClick={sendToAllModels}
              disabled={!inputMessage.trim() || modelCards.some(card => card.isLoading)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
          
          {/* 统计信息 */}
          <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
            <span>
              {modelCards.length} 个模型 · {modelCards.reduce((sum, card) => sum + card.messages.length, 0)} 条消息
            </span>
            <div className="flex space-x-4">
              {modelCards.filter(card => card.isLoading).length > 0 && (
                <span className="text-blue-600">
                  {modelCards.filter(card => card.isLoading).length} 个正在处理
                </span>
              )}
              {modelCards.filter(card => card.error).length > 0 && (
                <span className="text-red-600">
                  {modelCards.filter(card => card.error).length} 个出错
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 模型选择模态框 */}
      {showModelSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">批量添加测试模型</h3>
                <p className="text-sm text-gray-600">已选择 {selectedModelIds.size} 个模型</p>
              </div>
              <button
                onClick={() => {
                  setShowModelSelector(false)
                  setSelectedModelIds(new Set())
                }}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    const availableIds = availableModels
                      .filter(model => !modelCards.find(card => card.model.id === model.id))
                      .map(model => model.id)
                    setSelectedModelIds(new Set(availableIds))
                  }}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                >
                  全选可用
                </button>
                <button
                  onClick={() => setSelectedModelIds(new Set())}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                >
                  清空选择
                </button>
              </div>
              <button
                onClick={() => {
                  const selectedModels = availableModels.filter(model => selectedModelIds.has(model.id))
                  addSelectedModels(selectedModels)
                  setSelectedModelIds(new Set())
                }}
                disabled={selectedModelIds.size === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                添加选中的模型 ({selectedModelIds.size})
              </button>
            </div>
            
            <div className="overflow-y-auto max-h-[50vh]">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {availableModels.map((model) => {
                  const isSelected = selectedModelIds.has(model.id)
                  const isAdded = modelCards.find(card => card.model.id === model.id)
                  
                  return (
                    <div
                      key={model.id}
                      onClick={() => {
                        if (isAdded) return
                        
                        const newSelected = new Set(selectedModelIds)
                        if (isSelected) {
                          newSelected.delete(model.id)
                        } else {
                          newSelected.add(model.id)
                        }
                        setSelectedModelIds(newSelected)
                      }}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        isAdded 
                          ? 'border-gray-200 bg-gray-50 cursor-not-allowed' 
                          : isSelected
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        {/* 选择框 */}
                        <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                          isAdded
                            ? 'border-gray-300 bg-gray-100'
                            : isSelected
                              ? 'border-blue-500 bg-blue-500'
                              : 'border-gray-300'
                        }`}>
                          {isSelected && <CheckCircle className="w-3 h-3 text-white" />}
                          {isAdded && <CheckCircle className="w-3 h-3 text-gray-400" />}
                        </div>
                        
                        <Brain className={`h-5 w-5 ${isAdded ? 'text-gray-400' : 'text-blue-600'}`} />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className={`font-medium ${isAdded ? 'text-gray-400' : 'text-gray-900'}`}>
                              {model.name}
                            </span>
                            {isAdded && (
                              <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">
                                已添加
                              </span>
                            )}
                          </div>
                          <p className={`text-sm ${isAdded ? 'text-gray-400' : 'text-gray-500'}`}>
                            {model.provider}
                          </p>
                          <p className={`text-xs ${isAdded ? 'text-gray-300' : 'text-gray-400'}`}>
                            {model.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agent编辑悬浮窗口 */}
      {showAgentEditor && editingAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
            {/* 窗口头部 */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                  <Edit3 className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">编辑Agent配置</h3>
                  <p className="text-sm text-gray-600">{editingAgent.name}</p>
                </div>
              </div>
              <button
                onClick={() => setShowAgentEditor(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>
            
            {/* 窗口内容 */}
            <div className="overflow-y-auto max-h-[70vh] p-6">
              <div className="space-y-6">
                {/* 基本信息 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Agent名称</label>
                  <input
                    type="text"
                    value={editingAgent.name}
                    onChange={(e) => setEditingAgent(prev => prev ? {...prev, name: e.target.value} : null)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">描述</label>
                  <textarea
                    value={editingAgent.description}
                    onChange={(e) => setEditingAgent(prev => prev ? {...prev, description: e.target.value} : null)}
                    rows={2}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                {/* 系统提示词 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">系统提示词</label>
                  <textarea
                    value={editingAgent.system_config.system_prompt}
                    onChange={(e) => setEditingAgent(prev => prev ? {
                      ...prev,
                      system_config: {
                        ...prev.system_config,
                        system_prompt: e.target.value
                      }
                    } : null)}
                    rows={8}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
                    placeholder="输入系统提示词..."
                  />
                </div>

                {/* LLM参数 */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">LLM参数</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Temperature</label>
                      <input
                        type="number"
                        min="0"
                        max="2"
                        step="0.1"
                        value={editingAgent.llm_config.temperature}
                        onChange={(e) => setEditingAgent(prev => prev ? {
                          ...prev,
                          llm_config: {
                            ...prev.llm_config,
                            temperature: parseFloat(e.target.value)
                          }
                        } : null)}
                        className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Max Tokens</label>
                      <input
                        type="number"
                        min="1"
                        max="8000"
                        value={editingAgent.llm_config.max_tokens}
                        onChange={(e) => setEditingAgent(prev => prev ? {
                          ...prev,
                          llm_config: {
                            ...prev.llm_config,
                            max_tokens: parseInt(e.target.value)
                          }
                        } : null)}
                        className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Top-p</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={editingAgent.llm_config.top_p}
                        onChange={(e) => setEditingAgent(prev => prev ? {
                          ...prev,
                          llm_config: {
                            ...prev.llm_config,
                            top_p: parseFloat(e.target.value)
                          }
                        } : null)}
                        className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Frequency Penalty</label>
                      <input
                        type="number"
                        min="-2"
                        max="2"
                        step="0.1"
                        value={editingAgent.llm_config.frequency_penalty}
                        onChange={(e) => setEditingAgent(prev => prev ? {
                          ...prev,
                          llm_config: {
                            ...prev.llm_config,
                            frequency_penalty: parseFloat(e.target.value)
                          }
                        } : null)}
                        className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 窗口底部 */}
            <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setShowAgentEditor(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
              >
                取消
              </button>
              <button
                onClick={async () => {
                  try {
                    const response = await fetch(`/api/v1/agents/${editingAgent.id}`, {
                      method: 'PATCH',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify(editingAgent)
                    })
                    
                    if (response.ok) {
                      setSelectedAgent(editingAgent)
                      setShowAgentEditor(false)
                      toast.success('Agent配置已保存')
                    } else {
                      toast.error('保存失败')
                    }
                  } catch (error) {
                    console.error('保存Agent失败:', error)
                    toast.error('保存失败')
                  }
                }}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-colors"
              >
                保存配置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 