
import { Plus, Eye, Edit, Trash2, Play, ToggleLeft, ToggleRight, Search, Download, RefreshCw, BookOpen, Code, Info } from 'lucide-react'
import { useEffect, useState } from 'react'

interface Tool {
  id: string
  name: string
  description: string
  schema: any
  endpoint?: string
  enabled: boolean
  created_at: string
  updated_at?: string
}

interface ToolCreateForm {
  name: string
  description: string
  schema: string
  endpoint?: string
  enabled: boolean
}

export default function Tools() {
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterEnabled, setFilterEnabled] = useState<boolean | null>(null)
  const [activeTab, setActiveTab] = useState<'management' | 'documentation'>('management')
  
  // 模态框状态
  const [showAddModal, setShowAddModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showTestModal, setShowTestModal] = useState(false)
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  
  // 表单状态
  const [formData, setFormData] = useState<ToolCreateForm>({
    name: '',
    description: '',
    schema: '',
    endpoint: '',
    enabled: true
  })
  
  // 测试工具状态
  const [testParams, setTestParams] = useState<string>('{}')
  const [testResult, setTestResult] = useState<any>(null)
  const [testLoading, setTestLoading] = useState(false)

  // 获取工具列表
  const fetchTools = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/tools/')
      if (response.ok) {
        const data = await response.json()
        setTools(data)
      } else {
        console.error('获取工具列表失败')
      }
    } catch (error) {
      console.error('获取工具列表错误:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTools()
  }, [])

  // 过滤工具
  const filteredTools = tools.filter(tool => {
    const matchesSearch = tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tool.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterEnabled === null || tool.enabled === filterEnabled
    return matchesSearch && matchesFilter
  })

  // 添加工具
  const handleAddTool = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      let schemaObj
      try {
        schemaObj = JSON.parse(formData.schema)
      } catch {
        alert('Schema必须是有效的JSON格式')
        return
      }

      const response = await fetch('/api/v1/tools/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          schema: schemaObj
        }),
      })

      if (response.ok) {
        await fetchTools()
        setShowAddModal(false)
        resetForm()
        alert('工具添加成功！')
      } else {
        const error = await response.json()
        alert(`添加失败: ${error.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('添加工具错误:', error)
      alert('添加工具失败')
    }
  }

  // 更新工具
  const handleUpdateTool = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTool) return

    try {
      let schemaObj
      try {
        schemaObj = JSON.parse(formData.schema)
      } catch {
        alert('Schema必须是有效的JSON格式')
        return
      }

      const response = await fetch(`/api/v1/tools/${selectedTool.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          schema: schemaObj
        }),
      })

      if (response.ok) {
        await fetchTools()
        setShowEditModal(false)
        setSelectedTool(null)
        resetForm()
        alert('工具更新成功！')
      } else {
        const error = await response.json()
        alert(`更新失败: ${error.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('更新工具错误:', error)
      alert('更新工具失败')
    }
  }

  // 删除工具
  const handleDeleteTool = async (tool: Tool) => {
    if (!confirm(`确定要删除工具 "${tool.name}" 吗？此操作不可撤销。`)) {
      return
    }

    try {
      const response = await fetch(`/api/v1/tools/${tool.id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        await fetchTools()
        alert('工具删除成功！')
      } else {
        const error = await response.json()
        alert(`删除失败: ${error.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('删除工具错误:', error)
      alert('删除工具失败')
    }
  }

  // 切换工具启用状态
  const handleToggleEnabled = async (tool: Tool) => {
    try {
      const response = await fetch(`/api/v1/tools/${tool.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          enabled: !tool.enabled
        }),
      })

      if (response.ok) {
        await fetchTools()
        alert(`工具已${!tool.enabled ? '启用' : '禁用'}`)
      } else {
        const error = await response.json()
        alert(`操作失败: ${error.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('切换工具状态错误:', error)
      alert('操作失败')
    }
  }

  // 测试工具
  const handleTestTool = async () => {
    if (!selectedTool) return

    try {
      setTestLoading(true)
      setTestResult(null)

      let params
      try {
        params = JSON.parse(testParams)
      } catch {
        alert('参数必须是有效的JSON格式')
        return
      }

      // 调用真实的工具测试API
      const response = await fetch(`/api/v1/tools/${selectedTool.id}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          parameters: params
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setTestResult(result)
      } else {
        const error = await response.json()
        setTestResult({
          success: false,
          error: error.detail || '测试执行失败',
          timestamp: new Date().toISOString()
        })
      }
    } catch (error) {
      console.error('测试工具错误:', error)
      setTestResult({
        success: false,
        error: `网络错误: ${error instanceof Error ? error.message : '未知错误'}`,
        timestamp: new Date().toISOString()
      })
    } finally {
      setTestLoading(false)
    }
  }

  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      schema: '',
      endpoint: '',
      enabled: true
    })
  }

  // 打开编辑模态框
  const openEditModal = (tool: Tool) => {
    setSelectedTool(tool)
    setFormData({
      name: tool.name,
      description: tool.description,
      schema: JSON.stringify(tool.schema, null, 2),
      endpoint: tool.endpoint || '',
      enabled: tool.enabled
    })
    setShowEditModal(true)
  }

  // 打开查看模态框
  const openViewModal = (tool: Tool) => {
    setSelectedTool(tool)
    setShowViewModal(true)
  }

  // 打开测试模态框
  const openTestModal = (tool: Tool) => {
    setSelectedTool(tool)
    setTestParams('{}')
    setTestResult(null)
    setShowTestModal(true)
  }

  // 导出工具配置
  const handleExportTools = () => {
    const dataStr = JSON.stringify(tools, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `tools-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="card p-6">
                <div className="h-16 bg-gray-200 rounded mb-4"></div>
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* 头部 */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">工具管理</h1>
          <p className="mt-2 text-gray-600">管理 Agent 可使用的工具和功能</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleExportTools}
            className="btn-secondary"
          >
            <Download className="h-4 w-4 mr-2" />
            导出
          </button>
          <button
            onClick={fetchTools}
            className="btn-secondary"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            添加工具
          </button>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('management')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'management'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Plus className="h-4 w-4 mr-2 inline" />
              工具管理
            </button>
            <button
              onClick={() => setActiveTab('documentation')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documentation'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <BookOpen className="h-4 w-4 mr-2 inline" />
              使用说明
            </button>
          </nav>
        </div>
      </div>

      {activeTab === 'management' ? (
        <>
          {/* 搜索和过滤 */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="搜索工具名称或描述..."
            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={filterEnabled === null ? 'all' : filterEnabled.toString()}
            onChange={(e) => {
              const value = e.target.value
              setFilterEnabled(value === 'all' ? null : value === 'true')
            }}
          >
            <option value="all">全部状态</option>
            <option value="true">已启用</option>
            <option value="false">已禁用</option>
          </select>
        </div>
      </div>

      {/* 工具统计 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-gray-900">{tools.length}</div>
          <div className="text-sm text-gray-600">总工具数</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-green-600">
            {tools.filter(t => t.enabled).length}
          </div>
          <div className="text-sm text-gray-600">已启用</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-red-600">
            {tools.filter(t => !t.enabled).length}
          </div>
          <div className="text-sm text-gray-600">已禁用</div>
        </div>
      </div>

      {/* 工具列表 */}
      {filteredTools.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">
            {searchTerm || filterEnabled !== null ? '没有找到匹配的工具' : '暂无工具'}
          </div>
          {!searchTerm && filterEnabled === null && (
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary"
            >
              <Plus className="h-4 w-4 mr-2" />
              添加第一个工具
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTools.map((tool) => (
            <div key={tool.id} className="card p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{tool.name}</h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{tool.description}</p>
                </div>
                <button
                  onClick={() => handleToggleEnabled(tool)}
                  className={`ml-2 ${tool.enabled ? 'text-green-500 hover:text-green-700' : 'text-gray-400 hover:text-gray-600'}`}
                  title={tool.enabled ? '点击禁用' : '点击启用'}
                >
                  {tool.enabled ? <ToggleRight className="h-6 w-6" /> : <ToggleLeft className="h-6 w-6" />}
                </button>
              </div>

              <div className="mb-4">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  tool.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {tool.enabled ? '已启用' : '已禁用'}
                </span>
                {tool.endpoint && (
                  <span className="ml-2 inline-flex px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    API
                  </span>
                )}
              </div>

              <div className="text-xs text-gray-500 mb-4">
                创建时间: {new Date(tool.created_at).toLocaleDateString()}
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => openViewModal(tool)}
                  className="btn-secondary flex-1 text-sm"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  查看
                </button>
                <button
                  onClick={() => openTestModal(tool)}
                  className="btn-secondary text-sm"
                  disabled={!tool.enabled}
                >
                  <Play className="h-4 w-4" />
                </button>
                <button
                  onClick={() => openEditModal(tool)}
                  className="btn-secondary text-sm"
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDeleteTool(tool)}
                  className="btn-secondary text-sm text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 添加工具模态框 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">添加工具</h2>
            
            <form onSubmit={handleAddTool} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  工具名称 *
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="例如: calculator"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  工具描述 *
                </label>
                <textarea
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="描述工具的功能和用途"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schema (JSON) *
                </label>
                <textarea
                  required
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  value={formData.schema}
                  onChange={(e) => setFormData({ ...formData, schema: e.target.value })}
                  placeholder={'{\n  "type": "function",\n  "function": {\n    "name": "tool_name",\n    "description": "工具描述",\n    "parameters": {\n      "type": "object",\n      "properties": {},\n      "required": []\n    }\n  }\n}'}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API端点 (可选)
                </label>
                <input
                  type="url"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.endpoint}
                  onChange={(e) => setFormData({ ...formData, endpoint: e.target.value })}
                  placeholder="https://api.example.com/tool"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="enabled" className="ml-2 block text-sm text-gray-700">
                  启用工具
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false)
                    resetForm()
                  }}
                  className="btn-secondary"
                >
                  取消
                </button>
                <button type="submit" className="btn-primary">
                  添加工具
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 查看工具模态框 */}
      {showViewModal && selectedTool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold">工具详情</h2>
              <button
                onClick={() => setShowViewModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">工具名称</label>
                <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                  {selectedTool.name}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                  {selectedTool.description}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Schema</label>
                <pre className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg overflow-x-auto text-sm">
                  {JSON.stringify(selectedTool.schema, null, 2)}
                </pre>
              </div>

              {selectedTool.endpoint && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API端点</label>
                  <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                    {selectedTool.endpoint}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                  <div className={`px-3 py-2 rounded-lg ${
                    selectedTool.enabled ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                  }`}>
                    {selectedTool.enabled ? '已启用' : '已禁用'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">创建时间</label>
                  <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                    {new Date(selectedTool.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-6">
              <button
                onClick={() => setShowViewModal(false)}
                className="btn-secondary"
              >
                关闭
              </button>
              <button
                onClick={() => {
                  setShowViewModal(false)
                  openEditModal(selectedTool)
                }}
                className="btn-primary"
              >
                编辑工具
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑工具模态框 */}
      {showEditModal && selectedTool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">编辑工具</h2>
            
            <form onSubmit={handleUpdateTool} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  工具名称 *
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  工具描述 *
                </label>
                <textarea
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schema (JSON) *
                </label>
                <textarea
                  required
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  value={formData.schema}
                  onChange={(e) => setFormData({ ...formData, schema: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API端点 (可选)
                </label>
                <input
                  type="url"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.endpoint}
                  onChange={(e) => setFormData({ ...formData, endpoint: e.target.value })}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enabled-edit"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="enabled-edit" className="ml-2 block text-sm text-gray-700">
                  启用工具
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false)
                    setSelectedTool(null)
                    resetForm()
                  }}
                  className="btn-secondary"
                >
                  取消
                </button>
                <button type="submit" className="btn-primary">
                  更新工具
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 测试工具模态框 */}
      {showTestModal && selectedTool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold">测试工具: {selectedTool.name}</h2>
              <button
                onClick={() => setShowTestModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  测试参数 (JSON)
                </label>
                <textarea
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  value={testParams}
                  onChange={(e) => setTestParams(e.target.value)}
                  placeholder='{\n  "param1": "value1",\n  "param2": "value2"\n}'
                />
              </div>

              <button
                onClick={handleTestTool}
                disabled={testLoading}
                className="btn-primary w-full"
              >
                {testLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    测试中...
                  </div>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    测试工具
                  </>
                )}
              </button>

              {testResult && (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    测试结果
                  </label>
                  <pre className={`px-3 py-2 border rounded-lg overflow-x-auto text-sm ${
                    testResult.success 
                      ? 'bg-green-50 border-green-200 text-green-800' 
                      : 'bg-red-50 border-red-200 text-red-800'
                  }`}>
                    {JSON.stringify(testResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={() => setShowTestModal(false)}
                className="btn-secondary"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
        </>
      ) : (
        <ToolDocumentation tools={tools} />
      )}
    </div>
  )
}

// 工具使用说明组件
function ToolDocumentation({ tools }: { tools: Tool[] }) {
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)

  return (
    <div className="space-y-6">
      {/* 工具列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tools.filter(tool => tool.enabled).map(tool => (
          <div
            key={tool.id}
            className={`p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedTool?.id === tool.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
            onClick={() => setSelectedTool(tool)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{tool.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{tool.description}</p>
              </div>
              <Info className="h-4 w-4 text-gray-400 ml-2 flex-shrink-0" />
            </div>
          </div>
        ))}
      </div>

      {/* 工具详细说明 */}
      {selectedTool && (
        <ToolUsageDetails tool={selectedTool} />
      )}
    </div>
  )
}

// 工具使用详情组件
function ToolUsageDetails({ tool }: { tool: Tool }) {
  const getToolParameters = (schema: any) => {
    if (schema?.function?.parameters?.properties) {
      return schema.function.parameters.properties
    }
    if (schema?.properties) {
      return schema.properties
    }
    return {}
  }

  const getToolExamples = (toolName: string) => {
    const examples: Record<string, any[]> = {
      calendar: [
        {
          title: "查询特定日期信息",
          params: {
            action: "get_date_info",
            year: 2024,
            month: 12,
            day: 25,
            include_festivals: true,
            include_zodiac: true
          },
          description: "获取2024年12月25日的详细信息，包括节日和生肖星座"
        },
        {
          title: "获取月历",
          params: {
            action: "get_month_calendar", 
            year: 2024,
            month: 12
          },
          description: "获取2024年12月的完整月历"
        },
        {
          title: "计算年龄",
          params: {
            action: "calculate_age",
            birth_year: 1990,
            birth_month: 5,
            birth_day: 15
          },
          description: "计算出生于1990年5月15日的人的当前年龄"
        },
        {
          title: "获取年份信息",
          params: {
            action: "get_year_info",
            year: 2024
          },
          description: "获取2024年的基本信息（是否闰年、生肖等）"
        }
      ],
      precision_time: [
        {
          title: "获取当前时间",
          params: {
            action: "get_time",
            timezone: "Asia/Shanghai",
            format: "human",
            locale: "zh_CN"
          },
          description: "获取上海时区的当前时间，使用人类可读格式"
        },
        {
          title: "获取UTC时间戳",
          params: {
            action: "get_time",
            timezone: "UTC",
            format: "timestamp",
            include_microseconds: true
          },
          description: "获取UTC时间戳，包含微秒精度"
        },
        {
          title: "获取时区信息",
          params: {
            action: "get_timezone_info",
            timezone: "America/New_York"
          },
          description: "获取纽约时区的详细信息"
        }
      ]
    }
    return examples[toolName] || []
  }

  const parameters = getToolParameters(tool.schema)
  const examples = getToolExamples(tool.name)

  return (
    <div className="bg-white border rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{tool.name}</h2>
        <p className="text-gray-600">{tool.description}</p>
      </div>

      {/* 参数说明 */}
      <div className="mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Code className="h-5 w-5 mr-2" />
          参数说明
        </h3>
        
        {Object.keys(parameters).length === 0 ? (
          <div className="text-gray-500 italic">此工具无需参数</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    参数名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    类型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    必填
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    描述
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    默认值
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(parameters).map(([key, param]: [string, any]) => (
                  <tr key={key}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <code className="bg-gray-100 px-2 py-1 rounded">{key}</code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {param.type || 'string'}
                        {param.enum && ' (enum)'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {tool.schema?.function?.parameters?.required?.includes(key) ? (
                        <span className="text-red-600 font-medium">是</span>
                      ) : (
                        <span className="text-gray-400">否</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {param.description || '无描述'}
                      {param.enum && (
                        <div className="mt-1 text-xs">
                          可选值: {param.enum.join(', ')}
                        </div>
                      )}
                      {param.minimum !== undefined && param.maximum !== undefined && (
                        <div className="mt-1 text-xs">
                          范围: {param.minimum} - {param.maximum}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {param.default !== undefined ? (
                        <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                          {JSON.stringify(param.default)}
                        </code>
                      ) : (
                        <span className="text-gray-400">无</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 使用示例 */}
      {examples.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Play className="h-5 w-5 mr-2" />
            使用示例
          </h3>
          
          <div className="space-y-4">
            {examples.map((example, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">{example.title}</h4>
                <p className="text-sm text-gray-600 mb-3">{example.description}</p>
                
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-2">参数示例:</div>
                  <pre className="text-sm text-gray-800 font-mono overflow-x-auto">
                    {JSON.stringify(example.params, null, 2)}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 最佳实践 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-medium text-blue-900 mb-2 flex items-center">
          <Info className="h-5 w-5 mr-2" />
          最佳实践
        </h3>
        <div className="text-sm text-blue-800 space-y-2">
          {tool.name === 'calendar' && (
            <>
              <p>• 使用 get_date_info 查询特定日期的详细信息</p>
              <p>• 使用 get_month_calendar 获取完整月历视图</p>
              <p>• 计算年龄时确保提供正确的出生日期格式</p>
              <p>• 可以组合多个操作来获取更全面的日期信息</p>
            </>
          )}
          {tool.name === 'precision_time' && (
            <>
              <p>• 指定正确的时区名称，如 'Asia/Shanghai'、'UTC'</p>
              <p>• 根据需要选择合适的时间格式</p>
              <p>• 对于高精度需求，启用微秒选项</p>
              <p>• 使用 get_timezone_info 了解时区详情</p>
            </>
          )}
          <p>• 在Agent对话中，工具会根据用户需求自动调用合适的参数</p>
          <p>• 多数参数都有合理的默认值，通常无需手动指定</p>
        </div>
      </div>
    </div>
  )
} 