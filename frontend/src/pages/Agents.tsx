import { useState, useEffect } from 'react'
import { 
  Globe, 
  Lock, 
  Share2, 
  Eye, 
  Trash2, 
  TestTube, 
  Brain,
  Settings,
  MessageSquare,
  Zap,
  Database,
  Rocket,
  X,
  QrCode,
  Plus,
  Edit,
  Save,
  Code,
  Copy,
  Upload
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
  status: 'active' | 'paused' | 'draft' | 'archived'
  access_level: 'public' | 'private' | 'team'
  
  // 模型配置
  llm_config: {
    primary_model_id: string
    fallback_model_id?: string
    temperature: number
    max_tokens: number
    top_p: number
    frequency_penalty: number
    presence_penalty: number
  }
  
  // 系统配置
  system_config: {
    system_prompt: string
    conversation_starters: string[]
    response_style: 'formal' | 'casual' | 'technical' | 'creative'
    max_context_turns: number
    enable_memory: boolean
  }
  
  // 工具配置
  tools_config: {
    enabled_tools: string[]
    tool_configs: Record<string, any>
    custom_tools: any[]
  }
  
  // 知识库配置
  knowledge_config: {
    enabled: boolean
    documents: string[]
    retrieval_config: {
      top_k: number
      similarity_threshold: number
      rerank: boolean
    }
  }
  
  // 部署配置
  deployment_config: {
    api_key?: string
    rate_limits: {
      requests_per_minute: number
      requests_per_day: number
    }
    webhook_url?: string
  }
  
  // 统计信息
  stats: {
    total_conversations: number
    total_messages: number
    avg_response_time: number
    user_satisfaction: number
  }
  
  created_at: string
  updated_at?: string
  version: number
}

interface Model {
  id: string
  name: string
  provider: string
  context_len: number
}

interface Tool {
  id: string
  name: string
  description: string
  category: string
  parameters: any
  schema?: any // 新增 schema 属性
}

const categories = [
  '客户服务', '数据分析', '内容创作', '编程助手', 
  '教育培训', '销售营销', '项目管理', '法律咨询',
  '医疗健康', '金融理财', '设计创意', '其他'
]

const responseStyles = [
  { value: 'formal', label: '正式专业', desc: '使用正式、专业的语言风格' },
  { value: 'casual', label: '轻松友好', desc: '使用轻松、友好的对话风格' },
  { value: 'technical', label: '技术专业', desc: '注重技术细节和准确性' },
  { value: 'creative', label: '创意灵活', desc: '富有创意和想象力的表达' }
]

export default function Agents() {
  const api = useApi()
  const [agents, setAgents] = useState<Agent[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null)
  const [currentStep, setCurrentStep] = useState(1)
  const [showAPIExample, setShowAPIExample] = useState<Agent | null>(null)
  const [qrCodeData, setQrCodeData] = useState<{agent: Agent, qrUrl: string} | null>(null)

  // 新Agent表单数据
  const [formData, setFormData] = useState<Partial<Agent>>({
    name: '',
    description: '',
    category: categories[0],
    tags: [],
    access_level: 'private',
    llm_config: {
      primary_model_id: '',
      temperature: 0.7,
      max_tokens: 2000,
      top_p: 0.9,
      frequency_penalty: 0,
      presence_penalty: 0
    },
    system_config: {
      system_prompt: '',
      conversation_starters: [],
      response_style: 'formal',
      max_context_turns: 10,
      enable_memory: true
    },
    tools_config: {
      enabled_tools: [],
      tool_configs: {},
      custom_tools: []
    },
    knowledge_config: {
      enabled: false,
      documents: [],
      retrieval_config: {
        top_k: 5,
        similarity_threshold: 0.7,
        rerank: true
      }
    },
    deployment_config: {
      rate_limits: {
        requests_per_minute: 60,
        requests_per_day: 1000
      }
    }
  })

  // 加载数据
  useEffect(() => {
    loadAgents()
    loadModels()
    loadTools()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await api.get('/api/v1/agents', { skipToast: true })
      const data = await response.json()
      setAgents(data)
    } catch (error) {
      console.error('加载Agent失败:', error)
      toast.error('加载Agent列表失败')
    }
  }

  const loadModels = async () => {
    try {
      const response = await api.get('/api/v1/models?enabled=true', { skipToast: true })
      const modelsData = await response.json()
      setModels(modelsData)
      if (modelsData.length > 0 && !formData.llm_config?.primary_model_id) {
        setFormData(prev => ({
          ...prev,
          llm_config: {
            ...prev.llm_config!,
            primary_model_id: modelsData[0].id
          }
        }))
      }
    } catch (error) {
      console.error('加载模型失败:', error)
      toast.error('加载模型列表失败')
    }
  }

  const loadTools = async () => {
    try {
      const response = await api.get('/api/v1/tools', { skipToast: true })
      const data = await response.json()
      setTools(data)
    } catch (error) {
      console.error('加载工具失败:', error)
      toast.error('加载工具列表失败')
    }
  }

  const handleCreateAgent = () => {
    setEditingAgent(null)
    setFormData({
      name: '',
      description: '',
      category: '其他',
      tags: [],
      access_level: 'private',
      llm_config: {
        primary_model_id: models[0]?.id || '',
        temperature: 0.7,
        max_tokens: 2000,
        top_p: 0.9,
        frequency_penalty: 0,
        presence_penalty: 0
      },
      system_config: {
        system_prompt: '',
        conversation_starters: [],
        response_style: 'formal',
        max_context_turns: 10,
        enable_memory: true
      },
      tools_config: {
        enabled_tools: [],
        tool_configs: {},
        custom_tools: []
      },
      knowledge_config: {
        enabled: false,
        documents: [],
        retrieval_config: {
          top_k: 5,
          similarity_threshold: 0.7,
          rerank: true
        }
      },
      deployment_config: {
        rate_limits: {
          requests_per_minute: 60,
          requests_per_day: 1000
        }
      }
    })
    setCurrentStep(1)
    setShowCreateModal(true)
  }

  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent)
    
    // 确保JSON字段被正确处理
    const formDataWithDefaults = {
      ...agent,
      // 确保嵌套配置有默认值
      llm_config: agent.llm_config || {
        primary_model_id: '',
        temperature: 0.7,
        max_tokens: 2000,
        top_p: 0.9,
        frequency_penalty: 0,
        presence_penalty: 0
      },
      system_config: agent.system_config || {
        system_prompt: '',
        conversation_starters: [],
        response_style: 'formal',
        max_context_turns: 10,
        enable_memory: true
      },
      tools_config: agent.tools_config || {
        enabled_tools: [],
        tool_configs: {},
        custom_tools: []
      },
      knowledge_config: agent.knowledge_config || {
        enabled: false,
        documents: [],
        retrieval_config: {
          top_k: 5,
          similarity_threshold: 0.7,
          rerank: true
        }
      },
      deployment_config: agent.deployment_config || {
        api_key: '',
        rate_limits: {
          requests_per_minute: 60,
          requests_per_day: 1000
        },
        webhook_url: ''
      },
      stats: agent.stats || {
        total_conversations: 0,
        total_messages: 0,
        avg_response_time: 0,
        user_satisfaction: 0
      }
    }
    
    setFormData(formDataWithDefaults)
    setCurrentStep(1)
    setShowCreateModal(true)
  }

  const handleSaveAgent = async () => {
    console.log('🚀 开始保存Agent...')
    console.log('📋 表单数据:', formData)
    
    try {
      const url = editingAgent 
        ? `/api/v1/agents/${editingAgent.id}`
        : '/api/v1/agents'
      
      const method = editingAgent ? 'PATCH' : 'POST'
      
      console.log(`📡 发送请求: ${method} ${url}`)
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      console.log(`📥 响应状态: ${response.status}`)

      if (response.ok) {
        console.log('✅ 请求成功，开始处理响应...')
        await loadAgents()
        const agentData = await response.json()
        console.log('🎯 返回的Agent数据:', agentData)
        
        setShowCreateModal(false)
        setEditingAgent(null)
        
        if (!editingAgent) {
          // 新建Agent成功后，询问是否立即执行
          const shouldExecute = window.confirm(
            `Agent "${agentData.name}" 创建成功！\n\n是否立即执行该Agent？`
          )
          if (shouldExecute && agentData.status === 'active') {
            handleExecuteAgent(agentData)
          } else if (shouldExecute && agentData.status !== 'active') {
            toast.error('请先激活Agent后再执行')
          }
        }
        
        toast.success(editingAgent ? '更新成功' : '创建成功')
      } else {
        console.error('❌ 请求失败，状态码:', response.status)
        const error = await response.json()
        console.error('❌ 错误详情:', error)
        toast.error(error.detail || '操作失败')
      }
    } catch (error) {
      console.error('❌ 网络错误:', error)
      toast.error('网络错误: ' + (error instanceof Error ? error.message : String(error)))
    }
  }

  const handleCancel = () => {
    setShowCreateModal(false)
    setEditingAgent(null)
  }

  const handleExecuteAgent = (agent: Agent) => {
    // 跳转到Agent设计器页面进行调试
    window.location.href = `/agent-designer?id=${agent.id}`
  }

  const handleStatusChange = async (agentId: string, newStatus: string) => {
    try {
      await api.post(`/api/v1/agents/${agentId}/${newStatus}`, {})
      await loadAgents()
      toast.success(`状态已更新为 ${newStatus}`)
    } catch (error) {
      console.error('状态更新失败:', error)
      // 错误信息已在useApi中处理
    }
  }

  const handleShowAPIExample = (agent: Agent) => {
    setShowAPIExample(agent)
  }

  const handlePublishAgent = async (agentId: string) => {
    try {
      // 先检查Agent状态
      const agent = agents.find(a => a.id === agentId)
      if (!agent) {
        toast.error('Agent不存在')
        return
      }

      // 前端验证
      if (agent.status !== 'active') {
        toast.error('只有激活状态的Agent才能发布，请先激活此Agent')
        return
      }

      if (!agent.description || agent.description.trim().length < 10) {
        toast.error('发布的Agent必须有详细描述（至少10个字符），请先编辑Agent添加描述')
        return
      }

      await api.post(`/api/v1/agents/${agentId}/publish`, {})
      await loadAgents()
      toast.success('Agent已成功发布到市场！')
    } catch (error) {
      console.error('发布错误:', error)
      // 如果后端还有其他错误，会在useApi中显示
    }
  }

  const handleUnpublishAgent = async (agentId: string) => {
    try {
      await api.post(`/api/v1/agents/${agentId}/unpublish`, {})
      await loadAgents()
      toast.success('Agent已取消发布')
    } catch (error) {
      console.error('取消发布错误:', error)
      // 错误信息已在useApi中处理
    }
  }

  const handleShareAgent = async (agent: Agent) => {
    try {
      const response = await api.get(`/api/v1/agents/${agent.id}/share-link`)
      const data = await response.json()
      const shareUrl = `${window.location.origin}${data.data.share_link}`
      
      if (navigator.share) {
        await navigator.share({
          title: `体验 ${agent.name} - ModelVS3`,
          text: agent.description || '',
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

  const handleShowQrCode = async (agent: Agent) => {
    try {
      const response = await api.get(`/api/v1/agents/${agent.id}/share-link`)
      const data = await response.json()
      setQrCodeData({
        agent,
        qrUrl: data.data.qr_code_url
      })
    } catch (error) {
      console.error('获取二维码失败:', error)
      toast.error('获取二维码失败')
    }
  }

  const steps = [
    { id: 1, title: '基本信息', icon: Brain },
    { id: 2, title: '模型配置', icon: Settings },
    { id: 3, title: '系统提示', icon: MessageSquare },
    { id: 4, title: '工具集成', icon: Zap },
    { id: 5, title: '知识库', icon: Database },
    { id: 6, title: '部署设置', icon: Rocket },
    { id: 7, title: '测试预览', icon: TestTube }
  ]

  if (showCreateModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="text-lg font-semibold">
              {editingAgent ? '编辑Agent' : '创建Agent'}
            </h3>
            <button onClick={handleCancel} className="text-gray-500 hover:text-gray-700">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* 步骤导航 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center">
                  <button
                    onClick={() => setCurrentStep(step.id)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                      currentStep === step.id
                        ? 'bg-blue-100 text-blue-700'
                        : currentStep > step.id
                        ? 'bg-green-100 text-green-700'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <step.icon className="h-4 w-4" />
                    <span className="text-sm font-medium">{step.title}</span>
                  </button>
                  {index < steps.length - 1 && (
                    <div className={`w-8 h-0.5 mx-2 ${
                      currentStep > step.id ? 'bg-green-300' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 步骤内容 */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 flex-1 overflow-y-auto">
            {currentStep === 1 && <BasicInfoStep formData={formData} setFormData={setFormData} />}
            {currentStep === 2 && <ModelConfigStep formData={formData} setFormData={setFormData} models={models} />}
            {currentStep === 3 && <SystemPromptStep formData={formData} setFormData={setFormData} />}
            {currentStep === 4 && <ToolsConfigStep formData={formData} setFormData={setFormData} tools={tools} />}
            {currentStep === 5 && <KnowledgeConfigStep formData={formData} setFormData={setFormData} />}
            {currentStep === 6 && <DeploymentConfigStep formData={formData} setFormData={setFormData} />}
            {currentStep === 7 && <TestPreviewStep formData={formData} />}
          </div>

          {/* 底部导航 */}
          <div className="bg-gray-50 rounded-b-lg border border-t border-gray-200 p-4 flex justify-end space-x-3">
            <button
              onClick={handleCancel}
              className="btn-secondary"
            >
              取消
            </button>
            <button
              onClick={handleSaveAgent}
              className="btn-primary"
            >
              <Save className="h-4 w-4 mr-2" />
              保存
            </button>
          </div>
        </div>
      </div>
    )
  }

  // API调用案例弹窗
  if (showAPIExample) {
    const curlExample = `# 执行Agent
curl -X POST "http://localhost:8000/api/v1/runs" \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent_id": "${showAPIExample.id}",
    "messages": [
      {
        "role": "user",
        "content": "你好，请帮我处理一个任务"
      }
    ],
    "stream": false,
    "temperature": 0.7,
    "max_tokens": 2000
  }'

# 获取执行结果
curl -X GET "http://localhost:8000/api/v1/runs/{run_id}"

# 获取执行消息历史
curl -X GET "http://localhost:8000/api/v1/runs/{run_id}/messages"`

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="text-lg font-semibold flex items-center">
              <Code className="h-5 w-5 mr-2" />
              Agent API 调用案例 - {showAPIExample.name}
            </h3>
            <button 
              onClick={() => setShowAPIExample(null)} 
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-6">
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-2">Agent 信息</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">ID:</span> {showAPIExample.id}
                    </div>
                    <div>
                      <span className="font-medium">状态:</span> 
                      <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                        showAPIExample.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {showAPIExample.status}
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="font-medium">描述:</span> {showAPIExample.description}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-md font-medium text-gray-900">cURL 调用示例</h4>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(curlExample)
                      toast.success('已复制到剪贴板')
                    }}
                    className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    复制
                  </button>
                </div>
                <pre className="bg-gray-900 text-green-400 rounded-lg p-4 text-sm overflow-x-auto">
                  <code>{curlExample}</code>
                </pre>
              </div>

              <div>
                <h4 className="text-md font-medium text-gray-900 mb-2">响应示例</h4>
                <pre className="bg-gray-900 text-green-400 rounded-lg p-4 text-sm overflow-x-auto">
                  <code>{`{
  "id": "109ec3c6-ead4-42c3-a824-9cd63bb2449c",
  "agent_id": "${showAPIExample.id}",
  "model_id": null,
  "status": "completed",
  "input_tokens": 451,
  "output_tokens": 19,
  "execution_time_ms": 1024,
  "error_message": null,
  "created_at": "2025-07-24T06:07:58.277916Z",
  "completed_at": "2025-07-24T06:07:59.317559Z",
  "response": {
    "id": "c65fcc12-bf66-42e9-9f8c-922ced219916",
    "role": "assistant",
    "content": "你好！请告诉我你需要我帮你处理什么任务？我会尽我所能来帮助你。",
    "tool_calls": null,
    "tool_call_id": null,
    "created_at": "2025-07-24T06:07:58.300316Z"
  },
  "messages": []
}`}</code>
                </pre>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-md font-medium text-blue-900 mb-2">使用说明</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• 确保Agent状态为 <code>active</code> 才能正常执行</li>
                  <li>• <code>stream</code> 参数设为 <code>true</code> 可获得流式响应</li>
                  <li>• 执行完成后可通过 <code>run_id</code> 获取详细结果</li>
                  <li>• API现在只返回AI回复（<code>response</code>字段），不返回完整对话历史</li>
                  <li>• 前端负责维护对话历史，继续对话时需发送完整的<code>messages</code>数组</li>
                  <li>• <code>messages</code>字段保留为空数组（已废弃，使用<code>response</code>字段）</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">智能Agent管理</h1>
          <p className="text-gray-600 mt-1">创建和管理您的AI助手</p>
        </div>
        <button
          onClick={handleCreateAgent}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>创建Agent</span>
        </button>
      </div>

      {/* Agent卡片列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            onEdit={() => handleEditAgent(agent)}
            onExecute={handleExecuteAgent}
            onStatusChange={handleStatusChange}
            onShowAPIExample={handleShowAPIExample}
            onPublish={handlePublishAgent}
            onUnpublish={handleUnpublishAgent}
            onShare={handleShareAgent}
            onShowQrCode={handleShowQrCode}
            onDelete={async (id) => {
              if (window.confirm('确定要删除这个Agent吗？')) {
                try {
                  await api.delete(`/api/v1/agents/${id}`)
                  setAgents(prev => prev.filter(a => a.id !== id))
                  toast.success('删除成功')
                } catch (error) {
                  console.error('删除失败:', error)
                  // 错误信息已在useApi中处理
                }
              }
            }}
          />
        ))}
      </div>

      {/* 二维码模态框 */}
      {qrCodeData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">
                {qrCodeData.agent.name} - 访问二维码
              </h3>
              <button 
                onClick={() => setQrCodeData(null)} 
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 text-center">
              <div className="mb-4">
                <p className="text-gray-600 text-sm mb-2">
                  扫描二维码即可访问此Agent
                </p>
                <p className="text-xs text-gray-500">
                  {qrCodeData.agent.description}
                </p>
              </div>
              <div className="flex justify-center mb-4">
                <img 
                  src={qrCodeData.qrUrl} 
                  alt={`${qrCodeData.agent.name} 二维码`}
                  className="border border-gray-200 rounded-lg"
                  onError={(e) => {
                    e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjNGNEY2Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiBmaWxsPSIjOUI5QkEzIiBmb250LXNpemU9IjE0Ij7kuozmjaHnoIHliqDovb3lpLHotKU8L3RleHQ+Cjwvc3ZnPgo='
                  }}
                />
              </div>
              <div className="space-y-2">
                <button
                  onClick={async () => {
                    try {
                      const response = await api.get(`/api/v1/agents/${qrCodeData.agent.id}/share-link`)
                      const data = await response.json()
                      const shareUrl = `${window.location.origin}${data.data.share_link}`
                      await navigator.clipboard.writeText(shareUrl)
                      toast.success('访问链接已复制到剪贴板')
                    } catch (error) {
                      console.error('复制链接失败:', error)
                      toast.error('复制链接失败')
                    }
                  }}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  复制访问链接
                </button>
                <button
                  onClick={() => setQrCodeData(null)}
                  className="w-full bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Agent卡片组件
function AgentCard({ 
  agent, 
  onEdit, 
  onDelete, 
  onExecute, 
  onStatusChange, 
  onShowAPIExample,
  onPublish,
  onUnpublish,
  onShare,
  onShowQrCode 
}: {
  agent: Agent
  onEdit: () => void
  onDelete: (id: string) => void
  onExecute: (agent: Agent) => void
  onStatusChange: (agentId: string, newStatus: string) => void
  onShowAPIExample: (agent: Agent) => void
  onPublish: (agentId: string) => void
  onUnpublish: (agentId: string) => void
  onShare: (agent: Agent) => void
  onShowQrCode: (agent: Agent) => void
}) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'paused': return 'bg-yellow-100 text-yellow-800'
      case 'draft': return 'bg-gray-100 text-gray-800'
      case 'archived': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Brain className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 flex items-center">
              {agent.name}
              {agent.access_level === 'public' && (
                <Globe className="h-3 w-3 ml-1 text-green-600" />
              )}
              {agent.access_level === 'private' && (
                <Lock className="h-3 w-3 ml-1 text-gray-400" />
              )}
            </h3>
            <p className="text-sm text-gray-500">{agent.category}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(agent.status)}`}>
            {agent.status}
          </span>
          {agent.access_level === 'public' && (
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
              已发布
            </span>
          )}
        </div>
      </div>

      <p className="text-gray-600 text-sm mb-4 line-clamp-2">{agent.description}</p>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
        <span>{agent.stats?.total_conversations || 0} 次对话</span>
        <span>v{agent.version || 1}</span>
      </div>

      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          {agent.status === 'active' && (
            <button
              onClick={() => onExecute(agent)}
              className="flex-1 btn-primary text-sm py-2"
            >
              <MessageSquare className="h-3 w-3 mr-1" />
              调试
            </button>
          )}
          <button
            onClick={onEdit}
            className="flex-1 btn-secondary text-sm py-2"
          >
            <Edit className="h-3 w-3 mr-1" />
            编辑
          </button>
          <button
            onClick={() => onDelete(agent.id)}
            className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          {agent.status === 'draft' && (
            <button
              onClick={() => onStatusChange(agent.id, 'activate')}
              className="flex-1 text-xs bg-green-100 text-green-700 py-1 px-2 rounded hover:bg-green-200 transition-colors"
            >
              激活
            </button>
          )}
          {agent.access_level === 'private' && (
            <>
              {agent.status === 'active' && (!agent.description || agent.description.trim().length < 10) ? (
                <button 
                  disabled
                  className="flex-1 text-xs bg-gray-100 text-gray-400 py-1 px-2 rounded cursor-not-allowed" 
                  title="需要详细描述（至少10个字符）才能发布"
                >
                  <Globe className="h-3 w-3 inline mr-1" />需要描述
                </button>
              ) : agent.status === 'active' ? (
                <button 
                  onClick={() => onPublish(agent.id)} 
                  className="flex-1 text-xs bg-blue-100 text-blue-700 py-1 px-2 rounded hover:bg-blue-200 transition-colors" 
                  title="发布到市场"
                >
                  <Globe className="h-3 w-3 inline mr-1" />发布
                </button>
              ) : (
                <button 
                  disabled
                  className="flex-1 text-xs bg-gray-100 text-gray-400 py-1 px-2 rounded cursor-not-allowed" 
                  title={`需要先激活Agent才能发布（当前状态：${agent.status}）`}
                >
                  <Globe className="h-3 w-3 inline mr-1" />需要激活
                </button>
              )}
            </>
          )}
          {agent.access_level === 'public' && (
            <>
              <button
                onClick={() => onUnpublish(agent.id)}
                className="flex-1 text-xs bg-orange-100 text-orange-700 py-1 px-2 rounded hover:bg-orange-200 transition-colors"
                title="取消发布"
              >
                <Lock className="h-3 w-3 inline mr-1" />
                取消发布
              </button>
              <button
                onClick={() => onShare(agent)}
                className="flex-1 text-xs bg-green-100 text-green-700 py-1 px-2 rounded hover:bg-green-200 transition-colors"
                title="分享"
              >
                <Share2 className="h-3 w-3 inline mr-1" />
                分享
              </button>
              <button
                onClick={() => onShowQrCode(agent)}
                className="flex-1 text-xs bg-purple-100 text-purple-700 py-1 px-2 rounded hover:bg-purple-200 transition-colors"
                title="显示二维码"
              >
                <QrCode className="h-3 w-3 inline mr-1" />
                二维码
              </button>
            </>
          )}
          {agent.status === 'active' && (
            <button
              onClick={() => onStatusChange(agent.id, 'pause')}
              className="flex-1 text-xs bg-yellow-100 text-yellow-700 py-1 px-2 rounded hover:bg-yellow-200 transition-colors"
            >
              暂停
            </button>
          )}
          {(agent.status === 'paused' || agent.status === 'archived') && (
            <button
              onClick={() => onStatusChange(agent.id, 'activate')}
              className="flex-1 text-xs bg-green-100 text-green-700 py-1 px-2 rounded hover:bg-green-200 transition-colors"
            >
              激活
            </button>
          )}
        </div>
        
        <div className="flex items-center space-x-2 mt-2">
          <button
            onClick={() => onShowAPIExample(agent)}
            className="flex-1 text-xs bg-gray-100 text-gray-700 py-1 px-2 rounded hover:bg-gray-200 transition-colors"
          >
            <Eye className="h-3 w-3 inline mr-1" />
            API调用
          </button>
        </div>
      </div>
    </div>
  )
}

// 步骤组件将在下一部分实现...
function BasicInfoStep({ formData, setFormData }: any) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">基本信息配置</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Agent名称 *
          </label>
          <input
            type="text"
            value={formData.name || ''}
            onChange={(e) => setFormData((prev: any) => ({ ...prev, name: e.target.value }))}
            className="input w-full"
            placeholder="输入Agent名称"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            分类
          </label>
          <select
            value={formData.category || categories[0]}
            onChange={(e) => setFormData((prev: any) => ({ ...prev, category: e.target.value }))}
            className="input w-full"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          描述
        </label>
        <textarea
          value={formData.description || ''}
          onChange={(e) => setFormData((prev: any) => ({ ...prev, description: e.target.value }))}
          className="input w-full"
          rows={3}
          placeholder="描述Agent的功能和用途"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          访问权限
        </label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'private', label: '私有', desc: '仅自己可见' },
            { value: 'team', label: '团队', desc: '团队成员可见' },
            { value: 'public', label: '公开', desc: '所有人可见' }
          ].map(option => (
            <label key={option.value} className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="access_level"
                value={option.value}
                checked={formData.access_level === option.value}
                onChange={(e) => setFormData((prev: any) => ({ ...prev, access_level: e.target.value }))}
                className="text-blue-600"
              />
              <div>
                <div className="font-medium">{option.label}</div>
                <div className="text-xs text-gray-500">{option.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}

function ModelConfigStep({ formData, setFormData, models }: any) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">模型配置</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            主要模型 *
          </label>
          <select
            value={formData.llm_config?.primary_model_id || ''}
            onChange={(e) => setFormData((prev: any) => ({
              ...prev,
              llm_config: { ...prev.llm_config, primary_model_id: e.target.value }
            }))}
            className="input w-full"
          >
            {models.map((model: Model) => (
              <option key={model.id} value={model.id}>
                {model.name} ({model.provider})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            备用模型
          </label>
          <select
            value={formData.llm_config?.fallback_model_id || ''}
            onChange={(e) => setFormData((prev: any) => ({
              ...prev,
              llm_config: { ...prev.llm_config, fallback_model_id: e.target.value }
            }))}
            className="input w-full"
          >
            <option value="">无备用模型</option>
            {models.map((model: Model) => (
              <option key={model.id} value={model.id}>
                {model.name} ({model.provider})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            温度 (Temperature)
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={formData.llm_config?.temperature || 0.7}
            onChange={(e) => setFormData((prev: any) => ({
              ...prev,
              llm_config: { ...prev.llm_config, temperature: parseFloat(e.target.value) }
            }))}
            className="w-full"
          />
          <div className="text-sm text-gray-500 mt-1">
            {formData.llm_config?.temperature || 0.7}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            最大令牌数
          </label>
          <input
            type="number"
            value={formData.llm_config?.max_tokens || 2000}
            onChange={(e) => setFormData((prev: any) => ({
              ...prev,
              llm_config: { ...prev.llm_config, max_tokens: parseInt(e.target.value) }
            }))}
            className="input w-full"
            min="1"
            max="8000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Top P
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={formData.llm_config?.top_p || 0.9}
            onChange={(e) => setFormData((prev: any) => ({
              ...prev,
              llm_config: { ...prev.llm_config, top_p: parseFloat(e.target.value) }
            }))}
            className="w-full"
          />
          <div className="text-sm text-gray-500 mt-1">
            {formData.llm_config?.top_p || 0.9}
          </div>
        </div>
      </div>
    </div>
  )
}

function SystemPromptStep({ formData, setFormData }: any) {
  const promptTemplates = [
    {
      name: '专业助手',
      prompt: '你是一个专业的AI助手，擅长提供准确、详细的信息和建议。请始终保持专业、客观的态度。'
    },
    {
      name: '友好助手',
      prompt: '你是一个友好、热情的AI助手，喜欢与用户进行自然的对话。请用温暖、积极的语气回应。'
    },
    {
      name: '技术专家',
      prompt: '你是一个技术专家，擅长解决技术问题和提供技术建议。请提供准确、详细的技术信息。'
    }
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">系统提示词配置</h2>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          提示词模板
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {promptTemplates.map((template, index) => (
            <button
              key={index}
              onClick={() => setFormData((prev: any) => ({
                ...prev,
                system_config: { ...prev.system_config, system_prompt: template.prompt }
              }))}
              className="p-3 text-left border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="font-medium">{template.name}</div>
              <div className="text-xs text-gray-500 mt-1 line-clamp-2">{template.prompt}</div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          系统提示词 *
        </label>
        <textarea
          value={formData.system_config?.system_prompt || ''}
          onChange={(e) => setFormData((prev: any) => ({
            ...prev,
            system_config: { ...prev.system_config, system_prompt: e.target.value }
          }))}
          className="input w-full"
          rows={6}
          placeholder="定义Agent的角色、行为和能力..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          对话风格
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {responseStyles.map(style => (
            <label key={style.value} className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="response_style"
                value={style.value}
                checked={formData.system_config?.response_style === style.value}
                onChange={(e) => setFormData((prev: any) => ({
                  ...prev,
                  system_config: { ...prev.system_config, response_style: e.target.value }
                }))}
                className="text-blue-600"
              />
              <div>
                <div className="font-medium text-sm">{style.label}</div>
                <div className="text-xs text-gray-500">{style.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}

function ToolsConfigStep({ formData, setFormData, tools }: any) {

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">工具集成配置</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tools.map((tool: Tool) => (
          <label key={tool.id} className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={formData.tools_config?.enabled_tools?.includes(tool.id) || false}
              onChange={(e) => {
                const enabledTools = formData.tools_config?.enabled_tools || []
                if (e.target.checked) {
                  setFormData((prev: any) => ({
                    ...prev,
                    tools_config: {
                      ...prev.tools_config,
                      enabled_tools: [...enabledTools, tool.id]
                    }
                  }))
                } else {
                  setFormData((prev: any) => ({
                    ...prev,
                    tools_config: {
                      ...prev.tools_config,
                      enabled_tools: enabledTools.filter((id: string) => id !== tool.id)
                    }
                  }))
                }
              }}
              className="mt-1 text-blue-600"
            />
            <div className="flex-1">
              <div className="font-medium">{tool.name}</div>
              <div className="text-sm text-gray-500 mt-1">{tool.description}</div>
              <div className="text-xs text-gray-400 mt-1">类别: {tool.category || '未分类'}</div>
            </div>
            {formData.tools_config?.enabled_tools?.includes(tool.id) && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                <div className="text-xs text-blue-600 font-medium mb-2">
                  ✅ 已启用此工具
                </div>
                <div className="text-xs text-gray-500">
                  工具配置将在执行时使用默认参数，如需自定义请在Agent执行时指定。
                </div>
              </div>
            )}
          </label>
        ))}
      </div>
    </div>
  )
}

function KnowledgeConfigStep({ formData, setFormData }: any) {
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([])
  const [isDragging, setIsDragging] = useState(false)

  // 处理文件上传
  const handleFileUpload = async (files: FileList) => {
    const newFiles = Array.from(files).map(file => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0
    }))
    
    setUploadedFiles(prev => [...prev, ...newFiles])
    
    // 真实文件上传
    newFiles.forEach(async (file) => {
      try {
        // 调用真实的上传API
        const formData = new FormData()
        const fileToUpload = Array.from(files).find(f => f.name === file.name)
        if (fileToUpload) {
          formData.append('file', fileToUpload)
        }
        
        // 模拟上传进度
        const interval = setInterval(() => {
          setUploadedFiles(prev => prev.map(f => 
            f.id === file.id 
              ? { ...f, progress: Math.min(f.progress + 20, 100) }
              : f
          ))
          
          if (file.progress >= 100) {
            clearInterval(interval)
            setUploadedFiles(prev => prev.map(f => 
              f.id === file.id ? { ...f, status: 'completed' } : f
            ))
            
            // 更新formData中的documents
            setFormData((prev: any) => ({
              ...prev,
              knowledge_config: {
                ...prev.knowledge_config,
                documents: [...(prev.knowledge_config?.documents || []), file.name]
              }
            }))
          }
        }, 200)
        
        // 真实的上传API调用
        const response = await fetch('/api/v1/agents/upload', {
          method: 'POST',
          body: formData
        })
        
        if (response.ok) {
          const result = await response.json()
          console.log('文件上传成功:', result)
          // 上传成功，进度条会继续到100%
        } else {
          throw new Error('文件上传失败')
        }
        
      } catch (error) {
        console.error('文件上传失败:', error)
        setUploadedFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, status: 'failed' } : f
        ))
        toast.error('文件上传失败')
      }
    })
  }

  // 删除文档
  const handleDeleteDocument = (fileName: string) => {
    setUploadedFiles(prev => prev.filter(f => f.name !== fileName))
    setFormData((prev: any) => ({
      ...prev,
      knowledge_config: {
        ...prev.knowledge_config,
        documents: prev.knowledge_config?.documents?.filter((doc: string) => doc !== fileName) || []
      }
    }))
  }

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFileUpload(e.dataTransfer.files)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">知识库配置</h2>
      
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          checked={formData.knowledge_config?.enabled || false}
          onChange={(e) => setFormData((prev: any) => ({
            ...prev,
            knowledge_config: { ...prev.knowledge_config, enabled: e.target.checked }
          }))}
          className="text-blue-600"
        />
        <label className="font-medium">启用知识库</label>
      </div>

      {formData.knowledge_config?.enabled && (
        <div className="space-y-6">
          {/* 文档上传区域 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              文档上传
            </label>
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                isDragging 
                  ? 'border-blue-400 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500 mb-2">拖拽文件到此处或点击上传</p>
              <p className="text-xs text-gray-400 mb-4">支持 PDF, DOCX, TXT, MD 格式，单个文件最大 10MB</p>
              
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.md"
                onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
              >
                选择文件
              </label>
            </div>
          </div>

          {/* 已上传文档列表 */}
          {uploadedFiles.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">已上传文档</h3>
              <div className="space-y-2">
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                        <span className="text-blue-600 text-xs font-medium">
                          {file.name.split('.').pop()?.toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {file.status === 'uploading' && (
                        <div className="flex items-center space-x-2">
                          <div className="w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                          <span className="text-xs text-gray-500">{file.progress}%</span>
                        </div>
                      )}
                      {file.status === 'completed' && (
                        <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">已完成</span>
                      )}
                      <button
                        onClick={() => handleDeleteDocument(file.name)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 检索配置 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-3">检索配置</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  检索数量 (Top K)
                </label>
                <input
                  type="number"
                  value={formData.knowledge_config?.retrieval_config?.top_k || 5}
                  onChange={(e) => setFormData((prev: any) => ({
                    ...prev,
                    knowledge_config: {
                      ...prev.knowledge_config,
                      retrieval_config: {
                        ...prev.knowledge_config.retrieval_config,
                        top_k: parseInt(e.target.value)
                      }
                    }
                  }))}
                  className="input w-full"
                  min="1"
                  max="20"
                />
                <p className="text-xs text-gray-500 mt-1">每次检索返回的相关文档数量</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  相似度阈值
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.knowledge_config?.retrieval_config?.similarity_threshold || 0.7}
                    onChange={(e) => setFormData((prev: any) => ({
                      ...prev,
                      knowledge_config: {
                        ...prev.knowledge_config,
                        retrieval_config: {
                          ...prev.knowledge_config.retrieval_config,
                          similarity_threshold: parseFloat(e.target.value)
                        }
                      }
                    }))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-500">
                    {formData.knowledge_config?.retrieval_config?.similarity_threshold || 0.7}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">文档相似度最低阈值，低于此值将被过滤</p>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.knowledge_config?.retrieval_config?.rerank || false}
                  onChange={(e) => setFormData((prev: any) => ({
                    ...prev,
                    knowledge_config: {
                      ...prev.knowledge_config,
                      retrieval_config: {
                        ...prev.knowledge_config.retrieval_config,
                        rerank: e.target.checked
                      }
                    }
                  }))}
                  className="text-blue-600"
                />
                <div>
                  <label className="text-sm font-medium text-gray-700">启用重排序</label>
                  <p className="text-xs text-gray-500">对检索结果进行二次排序以提高相关性</p>
                </div>
              </div>
            </div>
          </div>

          {/* 知识库统计 */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-700 mb-2">知识库统计</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-600 font-medium">文档数量:</span>
                <span className="ml-2 text-gray-700">{uploadedFiles.filter(f => f.status === 'completed').length}</span>
              </div>
              <div>
                <span className="text-blue-600 font-medium">总大小:</span>
                <span className="ml-2 text-gray-700">
                  {formatFileSize(uploadedFiles.reduce((acc, f) => acc + f.size, 0))}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DeploymentConfigStep({ formData, setFormData }: any) {
  const [showApiKey, setShowApiKey] = useState(false)
  const [isGeneratingKey, setIsGeneratingKey] = useState(false)

  // 生成API密钥
  const generateApiKey = async () => {
    setIsGeneratingKey(true)
    try {
      const response = await fetch('/api/v1/agents/generate-api-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const result = await response.json()
        setFormData((prev: any) => ({
          ...prev,
          deployment_config: { 
            ...prev.deployment_config, 
            api_key: result.api_key 
          }
        }))
        toast.success('API密钥生成成功')
      } else {
        throw new Error('生成API密钥失败')
      }
    } catch (error) {
      console.error('生成API密钥失败:', error)
      toast.error('生成API密钥失败，请检查网络连接')
    } finally {
      setIsGeneratingKey(false)
    }
  }

  // 复制API密钥
  const copyApiKey = () => {
    if (formData.deployment_config?.api_key) {
      navigator.clipboard.writeText(formData.deployment_config.api_key)
      toast.success('API密钥已复制到剪贴板')
    }
  }

  // 重置API密钥
  const resetApiKey = () => {
    setFormData((prev: any) => ({
      ...prev,
      deployment_config: { 
        ...prev.deployment_config, 
        api_key: undefined 
      }
    }))
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">部署设置</h2>
      
      {/* API密钥管理 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-3">API密钥管理</h3>
        
        {formData.deployment_config?.api_key ? (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <label className="block text-sm font-medium text-gray-700">API密钥</label>
              <button
                onClick={() => setShowApiKey(!showApiKey)}
                className="text-blue-600 hover:text-blue-700 text-sm"
              >
                {showApiKey ? '隐藏' : '显示'}
              </button>
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                type={showApiKey ? "text" : "password"}
                value={formData.deployment_config.api_key}
                readOnly
                className="input flex-1 font-mono text-sm"
              />
              <button
                onClick={copyApiKey}
                className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                复制
              </button>
              <button
                onClick={resetApiKey}
                className="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              >
                重置
              </button>
            </div>
            
            <p className="text-xs text-gray-500">
              请妥善保管您的API密钥，泄露可能导致安全风险
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">尚未生成API密钥</p>
            <button
              onClick={generateApiKey}
              disabled={isGeneratingKey}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isGeneratingKey ? '生成中...' : '生成API密钥'}
            </button>
          </div>
        )}
      </div>

      {/* API端点信息 */}
      {formData.deployment_config?.api_key && (
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-blue-700 mb-3">API端点</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-600">聊天端点:</span>
              <code className="text-xs bg-blue-100 px-2 py-1 rounded">
                POST /api/v1/agents/{formData.id || '[agent_id]'}/chat
              </code>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-600">状态端点:</span>
              <code className="text-xs bg-blue-100 px-2 py-1 rounded">
                GET /api/v1/agents/{formData.id || '[agent_id]'}/status
              </code>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-600">配置端点:</span>
              <code className="text-xs bg-blue-100 px-2 py-1 rounded">
                GET /api/v1/agents/{formData.id || '[agent_id]'}
              </code>
            </div>
          </div>
        </div>
      )}

      {/* 速率限制配置 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-3">速率限制</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              每分钟请求限制
            </label>
            <input
              type="number"
              value={formData.deployment_config?.rate_limits?.requests_per_minute || 60}
              onChange={(e) => setFormData((prev: any) => ({
                ...prev,
                deployment_config: {
                  ...prev.deployment_config,
                  rate_limits: {
                    ...prev.deployment_config.rate_limits,
                    requests_per_minute: parseInt(e.target.value)
                  }
                }
              }))}
              className="input w-full"
              min="1"
              max="1000"
            />
            <p className="text-xs text-gray-500 mt-1">每分钟允许的最大请求数</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              每日请求限制
            </label>
            <input
              type="number"
              value={formData.deployment_config?.rate_limits?.requests_per_day || 1000}
              onChange={(e) => setFormData((prev: any) => ({
                ...prev,
                deployment_config: {
                  ...prev.deployment_config,
                  rate_limits: {
                    ...prev.deployment_config.rate_limits,
                    requests_per_day: parseInt(e.target.value)
                  }
                }
              }))}
              className="input w-full"
              min="1"
              max="100000"
            />
            <p className="text-xs text-gray-500 mt-1">每日允许的最大请求数</p>
          </div>
        </div>
      </div>

      {/* Webhook配置 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Webhook配置</h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Webhook URL (可选)
          </label>
          <input
            type="url"
            value={formData.deployment_config?.webhook_url || ''}
            onChange={(e) => setFormData((prev: any) => ({
              ...prev,
              deployment_config: { ...prev.deployment_config, webhook_url: e.target.value }
            }))}
            className="input w-full"
            placeholder="https://your-webhook-url.com/webhook"
          />
          <p className="text-xs text-gray-500 mt-1">
            配置后，Agent执行结果将发送到此URL
          </p>
        </div>
      </div>

      {/* 部署状态 */}
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="text-sm font-medium text-green-700 mb-3">部署状态</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-green-700">Agent已准备就绪</span>
          </div>
          <div className="text-xs text-green-600">
            保存配置后，Agent将立即可用于API调用和对话
          </div>
        </div>
      </div>
    </div>
  )
}

function TestPreviewStep({ formData }: any) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">测试预览</h2>
      
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="font-medium mb-4">Agent配置预览</h3>
        <div className="space-y-3 text-sm">
          <div><span className="font-medium">名称:</span> {formData.name}</div>
          <div><span className="font-medium">分类:</span> {formData.category}</div>
          <div><span className="font-medium">主要模型:</span> {formData.llm_config?.primary_model_id}</div>
          <div><span className="font-medium">启用工具:</span> {formData.tools_config?.enabled_tools?.length || 0} 个</div>
          <div><span className="font-medium">知识库:</span> {formData.knowledge_config?.enabled ? '已启用' : '未启用'}</div>
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex items-center space-x-2 text-blue-700">
          <TestTube className="h-4 w-4" />
          <span className="font-medium">测试对话</span>
        </div>
        <p className="text-blue-600 text-sm mt-1">
          保存后可以在对话页面测试Agent功能
        </p>
      </div>
    </div>
  )
} 