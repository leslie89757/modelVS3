import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Eye, EyeOff, X, Save, TestTube, Server, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiRequest } from '../config'

interface Model {
  id: string
  name: string
  provider: string
  endpoint: string
  context_len: number
  enabled: boolean
  api_key?: string
  custom_headers?: Record<string, string>
  created_at: string
}

interface ModelFormData {
  name: string
  provider: string
  endpoint: string
  context_len: number
  api_key?: string
  requires_auth: boolean
  custom_headers?: string
}

const providers = [
  { 
    id: 'openai', 
    name: 'OpenAI', 
    defaultEndpoint: 'https://api.openai.com/v1/chat/completions',
    requiresAuth: true,
    description: 'OpenAI 官方 API'
  },
  { 
    id: 'anthropic', 
    name: 'Anthropic', 
    defaultEndpoint: 'https://api.anthropic.com/v1/messages',
    requiresAuth: true,
    description: 'Anthropic Claude API'
  },
  { 
    id: 'google', 
    name: 'Google', 
    defaultEndpoint: 'https://generativelanguage.googleapis.com/v1/models',
    requiresAuth: true,
    description: 'Google Gemini API'
  },
  { 
    id: 'azure', 
    name: 'Azure OpenAI', 
    defaultEndpoint: 'https://your-resource.openai.azure.com/openai/deployments',
    requiresAuth: true,
    description: 'Azure OpenAI 服务'
  },
  { 
    id: 'ollama', 
    name: 'Ollama (本地)', 
    defaultEndpoint: 'http://localhost:11434/v1/chat/completions',
    requiresAuth: false,
    description: '本地 Ollama 服务，兼容 OpenAI 格式'
  },
  { 
    id: 'localai', 
    name: 'LocalAI', 
    defaultEndpoint: 'http://localhost:8080/v1/chat/completions',
    requiresAuth: false,
    description: '本地 LocalAI 服务'
  },
  { 
    id: 'vllm', 
    name: 'vLLM', 
    defaultEndpoint: 'http://localhost:8000/v1/chat/completions',
    requiresAuth: false,
    description: 'vLLM 推理服务器'
  },
  { 
    id: 'custom', 
    name: '自定义 API', 
    defaultEndpoint: 'http://localhost:8000/v1/chat/completions',
    requiresAuth: false,
    description: '自定义的 OpenAI 兼容 API'
  }
]

export default function Models() {
  const [models, setModels] = useState<Model[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingModel, setEditingModel] = useState<Model | null>(null)
  const [isTestingModel, setIsTestingModel] = useState(false)
  const [formData, setFormData] = useState<ModelFormData>({
    name: '',
    provider: '',
    endpoint: '',
    context_len: 4096,
    api_key: '',
    requires_auth: false,
    custom_headers: ''
  })

  // 加载模型列表
  const loadModels = async () => {
    try {
      const response = await apiRequest('/api/v1/models/')
      const modelsData = await response.json()
      setModels(modelsData)
    } catch (error) {
      console.error('加载模型失败:', error)
      toast.error('加载模型列表失败')
    }
  }

  // 初始化时加载模型
  useEffect(() => {
    loadModels()
  }, [])

  const resetForm = () => {
    setFormData({
      name: '',
      provider: '',
      endpoint: '',
      context_len: 4096,
      api_key: '',
      requires_auth: false,
      custom_headers: ''
    })
  }

  const openCreateModal = () => {
    resetForm()
    setShowCreateModal(true)
  }

  const openEditModal = (model: Model) => {
    setEditingModel(model)
    
    // 确定是否需要认证：如果模型有API密钥，或者提供商默认需要认证
    const hasApiKey = model.api_key && model.api_key.trim() !== ''
    const providerRequiresAuth = providers.find(p => p.id === model.provider)?.requiresAuth || false
    const requiresAuth = hasApiKey || providerRequiresAuth
    
    setFormData({
      name: model.name,
      provider: model.provider,
      endpoint: model.endpoint,
      context_len: model.context_len,
      api_key: model.api_key || '',
      requires_auth: requiresAuth,
      custom_headers: model.custom_headers ? JSON.stringify(model.custom_headers, null, 2) : ''
    })
    setShowEditModal(true)
  }

  const closeModals = () => {
    setShowCreateModal(false)
    setShowEditModal(false)
    setEditingModel(null)
    resetForm()
  }







  const toggleModelStatus = async (id: string) => {
    try {
      const model = models.find(m => m.id === id)
      if (!model) return

      const response = await fetch(`/api/v1/models/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled: !model.enabled })
      })

      if (response.ok) {
        toast.success('模型状态已更新')
        loadModels() // 重新加载模型列表
      } else {
        throw new Error('更新模型状态失败')
      }
    } catch (error) {
      console.error('更新状态失败:', error)
      toast.error('更新状态失败，请重试')
    }
  }

  const deleteModel = async (id: string) => {
    if (window.confirm('确定要删除这个模型吗？')) {
      try {
        const response = await fetch(`/api/v1/models/${id}`, {
          method: 'DELETE'
        })

        if (response.ok) {
          toast.success('模型已删除')
          loadModels() // 重新加载模型列表
        } else {
          throw new Error('删除模型失败')
        }
      } catch (error) {
        console.error('删除失败:', error)
        toast.error('删除失败，请重试')
      }
    }
  }

  const getProviderDisplayName = (providerId: string) => {
    return providers.find(p => p.id === providerId)?.name || providerId
  }

  const getProviderIcon = (providerId: string) => {
    if (['ollama', 'localai', 'vllm', 'custom'].includes(providerId)) {
      return <Server className="h-4 w-4" />
    }
    return null
  }

  const Modal = ({ isOpen, onClose, title, children }: {
    isOpen: boolean
    onClose: () => void
    title: string
    children: React.ReactNode
  }) => {
    if (!isOpen) return null

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          {children}
        </div>
      </div>
    )
  }

  // 简化的表单组件
  const SimpleForm = () => {
    const [name, setName] = useState(formData.name)
    const [provider, setProvider] = useState(formData.provider)
    const [endpoint, setEndpoint] = useState(formData.endpoint)
    const [contextLen, setContextLen] = useState(formData.context_len)
    const [apiKey, setApiKey] = useState(formData.api_key || '')
    const [requiresAuth, setRequiresAuth] = useState(formData.requires_auth)
    const [customHeaders, setCustomHeaders] = useState(formData.custom_headers || '')

    // 同步外部formData变化
    useEffect(() => {
      setName(formData.name)
      setProvider(formData.provider)
      setEndpoint(formData.endpoint)
      setContextLen(formData.context_len)
      setApiKey(formData.api_key || '')
      setRequiresAuth(formData.requires_auth)
      setCustomHeaders(formData.custom_headers || '')
    }, [formData])

    const handleSubmitForm = async (e: React.FormEvent) => {
      e.preventDefault()
      
      // 直接在这里进行验证
      if (!name.trim()) {
        toast.error('请输入模型名称')
        return
      }
      if (!provider) {
        toast.error('请选择提供商')
        return
      }
      if (!endpoint.trim()) {
        toast.error('请输入 API 端点')
        return
      }
      if (contextLen < 1 || contextLen > 1000000) {
        toast.error('上下文长度必须在 1 到 1,000,000 之间')
        return
      }
      
      // 验证API密钥：如果requires_auth为true，则必须提供API密钥
      if (requiresAuth && (!apiKey || !apiKey.trim())) {
        toast.error('启用API密钥认证时，必须提供API密钥')
        return
      }
      
      // 验证自定义 headers 格式
      if (customHeaders && customHeaders.trim()) {
        try {
          JSON.parse(customHeaders)
        } catch (error) {
          toast.error('自定义 Headers 必须是有效的 JSON 格式')
          return
        }
      }

      try {
        // 构建模型数据
        const modelData: any = {
          name: name.trim(),
          provider: provider,
          endpoint: endpoint.trim(),
          context_len: contextLen,
          enabled: true
        }
        
        // 处理API密钥
        if (requiresAuth && apiKey && apiKey.trim()) {
          modelData.api_key = apiKey.trim()
        } else {
          modelData.api_key = null
        }
        
        // 处理自定义headers
        if (customHeaders && customHeaders.trim()) {
          try {
            modelData.custom_headers = JSON.parse(customHeaders)
          } catch (error) {
            toast.error('自定义 Headers 格式错误')
            return
          }
        } else {
          modelData.custom_headers = null
        }

        if (editingModel) {
          // 更新模型
          const response = await fetch(`/api/v1/models/${editingModel.id}`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(modelData)
          })

          if (response.ok) {
            toast.success('模型更新成功')
            closeModals()
            loadModels()
          } else {
            const error = await response.json()
            toast.error(`更新失败: ${error.detail}`)
          }
        } else {
          // 创建模型
          const response = await fetch('/api/v1/models/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(modelData)
          })

          if (response.ok) {
            toast.success('模型创建成功')
            closeModals()
            loadModels()
          } else {
            const error = await response.json()
            toast.error(`创建失败: ${error.detail}`)
          }
        }
      } catch (error) {
        console.error('提交失败:', error)
        toast.error('提交失败，请检查网络连接')
      }
    }

    const handleProviderSelect = (providerId: string) => {
      setProvider(providerId)
      const selectedProvider = providers.find(p => p.id === providerId)
      if (selectedProvider) {
        setEndpoint(selectedProvider.defaultEndpoint)
        setRequiresAuth(selectedProvider.requiresAuth)
      }
    }

    return (
      <form onSubmit={handleSubmitForm} className="p-6 space-y-6">
        {/* 基础信息 */}
        <div>
          <label className="label">模型名称 *</label>
          <input
            type="text"
            className="input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如：gpt-4、llama2-7b、custom-model 等"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            建议使用官方模型名称，便于识别和管理
          </p>
        </div>

        {/* 提供商选择 */}
        <div>
          <label className="label">提供商 *</label>
          <select
            className="input"
            value={provider}
            onChange={(e) => handleProviderSelect(e.target.value)}
            required
          >
            <option value="">请选择提供商</option>
            {providers.map(p => (
              <option key={p.id} value={p.id}>
                {p.name} - {p.description}
              </option>
            ))}
          </select>
          {provider && (
            <div className="mt-2 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700">
                {providers.find(p => p.id === provider)?.description}
              </p>
            </div>
          )}
        </div>

        {/* API 端点 */}
        <div>
          <label className="label">API 端点 *</label>
          <input
            type="url"
            className="input"
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            placeholder="https://api.example.com/v1/chat/completions"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            模型的 API 调用地址，会根据选择的提供商自动填充默认值
          </p>
          {endpoint && endpoint.includes('localhost') && (
            <div className="mt-2 flex items-start space-x-2 p-3 bg-yellow-50 rounded-lg">
              <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-yellow-700">
                检测到本地端点，请确保对应的服务正在运行
              </p>
            </div>
          )}
        </div>

        {/* 上下文长度 */}
        <div>
          <label className="label">上下文长度 *</label>
          <input
            type="number"
            className="input"
            value={contextLen}
            onChange={(e) => setContextLen(parseInt(e.target.value))}
            min="1"
            max="1000000"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            模型支持的最大 token 数量，用于对话长度限制
          </p>
        </div>

        {/* 认证配置 */}
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <input
              type="checkbox"
              id="requires_auth"
              checked={requiresAuth}
              onChange={(e) => {
                setRequiresAuth(e.target.checked)
                if (!e.target.checked) {
                  setApiKey('')
                }
              }}
              className="rounded text-blue-600"
            />
            <label htmlFor="requires_auth" className="text-sm font-medium text-gray-700">
              需要 API 密钥认证
            </label>
          </div>
          
          {requiresAuth && (
            <div>
              <label className="label">API 密钥 *</label>
              <input
                type="password"
                className="input"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                API密钥将安全保存到系统配置中，用于模型调用认证
              </p>
            </div>
          )}
        </div>

        {/* 自定义 Headers */}
        <div>
          <label className="label">自定义 Headers（可选）</label>
          <textarea
            className="input h-20 resize-none font-mono text-sm"
            value={customHeaders}
            onChange={(e) => setCustomHeaders(e.target.value)}
            placeholder='{"X-Custom-Header": "value", "User-Agent": "MyApp/1.0"}'
          />
          <p className="text-xs text-gray-500 mt-1">
            JSON 格式的自定义请求头，用于特殊的 API 要求
          </p>
        </div>

        {/* 按钮组 */}
        <div className="flex justify-between pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={async () => {
              // 直接使用表单内部状态进行测试
              if (!name.trim()) {
                toast.error('请输入模型名称')
                return
              }
              if (!provider) {
                toast.error('请选择提供商')
                return
              }
              if (!endpoint.trim()) {
                toast.error('请输入 API 端点')
                return
              }
              if (contextLen < 1 || contextLen > 1000000) {
                toast.error('上下文长度必须在 1 到 1,000,000 之间')
                return
              }
              
              if (requiresAuth && (!apiKey || !apiKey.trim())) {
                toast.error('启用API密钥认证时，必须提供API密钥')
                return
              }
              
              if (customHeaders && customHeaders.trim()) {
                try {
                  JSON.parse(customHeaders)
                } catch (error) {
                  toast.error('自定义 Headers 必须是有效的 JSON 格式')
                  return
                }
              }

              setIsTestingModel(true)
              try {
                const headers: Record<string, string> = {
                  'Content-Type': 'application/json'
                }
                
                if (requiresAuth && apiKey) {
                  if (provider === 'anthropic') {
                    headers['x-api-key'] = apiKey
                    headers['anthropic-version'] = '2023-06-01'
                  } else if (provider === 'google') {
                    headers['Authorization'] = `Bearer ${apiKey}`
                  } else {
                    headers['Authorization'] = `Bearer ${apiKey}`
                  }
                }
                
                if (customHeaders && customHeaders.trim()) {
                  const customHeadersObj = JSON.parse(customHeaders)
                  Object.assign(headers, customHeadersObj)
                }
                
                const testPayload = {
                  model: name,
                  messages: [
                    {
                      role: 'user',
                      content: 'Hello, this is a connection test.'
                    }
                  ],
                  max_tokens: 10,
                  temperature: 0.1
                }
                
                console.log('Testing endpoint:', endpoint)
                console.log('Headers:', headers)
                console.log('Payload:', testPayload)
                
                const response = await fetch(endpoint, {
                  method: 'POST',
                  headers: headers,
                  body: JSON.stringify(testPayload)
                })
                
                if (response.ok) {
                  const result = await response.json()
                  console.log('API Response:', result)
                  toast.success('模型连接测试成功！API 响应正常')
                } else {
                  const errorText = await response.text()
                  console.error('API Error:', response.status, errorText)
                  toast.error(`API 连接测试失败: ${response.status} - ${errorText}`)
                }
              } catch (error) {
                console.error('测试失败:', error)
                toast.error(`测试失败: ${error instanceof Error ? error.message : '网络连接错误'}`)
              } finally {
                setIsTestingModel(false)
              }
            }}
            disabled={isTestingModel}
            className="btn-secondary flex items-center"
          >
            <TestTube className="h-4 w-4 mr-2" />
            {isTestingModel ? '测试中...' : '测试连接'}
          </button>
          
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={closeModals}
              className="btn-secondary"
            >
              取消
            </button>
            <button
              type="submit"
              className="btn-primary"
            >
              <Save className="h-4 w-4 mr-2" />
              {editingModel ? '更新' : '添加'}
            </button>
          </div>
        </div>
      </form>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">模型管理</h1>
          <p className="mt-2 text-gray-600">管理您的 LLM 模型配置，支持云端和本地部署</p>
        </div>
        <button
          onClick={openCreateModal}
          className="btn-primary"
        >
          <Plus className="h-4 w-4 mr-2" />
          添加模型
        </button>
      </div>
      
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">模型列表</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  模型名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  提供商
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  上下文长度
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {models.map((model) => (
                <tr key={model.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 flex items-center">
                      {getProviderIcon(model.provider) && (
                        <span className="mr-2 text-blue-500">
                          {getProviderIcon(model.provider)}
                        </span>
                      )}
                      {model.name}
                    </div>
                    <div className="text-sm text-gray-500 truncate max-w-xs" title={model.endpoint}>
                      {model.endpoint}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      ['ollama', 'localai', 'vllm', 'custom'].includes(model.provider)
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {getProviderDisplayName(model.provider)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.context_len.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      model.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {model.enabled ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button
                      onClick={() => toggleModelStatus(model.id)}
                      className="text-indigo-600 hover:text-indigo-900"
                      title={model.enabled ? '禁用模型' : '启用模型'}
                    >
                      {model.enabled ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                    <button 
                      onClick={() => openEditModal(model)}
                      className="text-indigo-600 hover:text-indigo-900"
                      title="编辑模型"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteModel(model.id)}
                      className="text-red-600 hover:text-red-900"
                      title="删除模型"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 添加/编辑模型模态框 */}
      <Modal 
        isOpen={showCreateModal || showEditModal} 
        onClose={closeModals}
        title={editingModel ? '编辑模型' : '添加模型'}
      >
        <SimpleForm />
      </Modal>
    </div>
  )
} 