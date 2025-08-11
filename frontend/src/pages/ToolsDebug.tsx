import { useState, useEffect } from 'react'

interface Tool {
  id: string
  name: string
  description: string
  category?: string
  schema?: any
}

export default function ToolsDebug() {
  const [tools, setTools] = useState<Tool[]>([])
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    try {
      const response = await fetch('/api/v1/tools')
      if (response.ok) {
        const data = await response.json()
        setTools(data)
        console.log('工具数据:', data)
      } else {
        throw new Error('获取工具列表失败')
      }
    } catch (error) {
      console.error('加载工具失败:', error)
      setError(error instanceof Error ? error.message : '未知错误')
    }
  }

  const renderSchemaStructure = (schema: any, level = 0) => {
    if (!schema) return <div className="text-gray-500">无schema</div>
    
    const indent = '  '.repeat(level)
    
    if (typeof schema === 'object') {
      return (
        <div className="font-mono text-sm">
          {Object.entries(schema).map(([key, value]) => (
            <div key={key} className="my-1">
              <span className="text-blue-600">{indent}{key}:</span>
              {typeof value === 'object' ? (
                <div className="ml-4">
                  {renderSchemaStructure(value, level + 1)}
                </div>
              ) : (
                <span className="text-green-600 ml-2">{JSON.stringify(value)}</span>
              )}
            </div>
          ))}
        </div>
      )
    }
    
    return <span className="text-green-600">{JSON.stringify(schema)}</span>
  }

  const getToolProperties = (schema: any) => {
    if (schema?.function?.parameters?.properties) {
      return schema.function.parameters.properties;
    }
    if (schema?.properties) {
      return schema.properties;
    }
    return {};
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">工具调试页面</h1>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 工具列表 */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold mb-4">工具列表 ({tools.length})</h2>
          
          <div className="space-y-3">
            {tools.map(tool => (
              <div 
                key={tool.id}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedTool?.id === tool.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedTool(tool)}
              >
                <div className="font-medium">{tool.name}</div>
                <div className="text-sm text-gray-500 mt-1">{tool.description}</div>
                <div className="text-xs text-gray-400 mt-1">
                  类别: {tool.category || '未分类'} | ID: {tool.id}
                </div>
                <div className="text-xs text-blue-600 mt-1">
                  Schema: {tool.schema ? '有' : '无'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 工具详情 */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold mb-4">工具详情</h2>
          
          {selectedTool ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-gray-900">基本信息</h3>
                <div className="mt-2 text-sm text-gray-600">
                  <p><strong>名称:</strong> {selectedTool.name}</p>
                  <p><strong>描述:</strong> {selectedTool.description}</p>
                  <p><strong>类别:</strong> {selectedTool.category || '未分类'}</p>
                  <p><strong>ID:</strong> {selectedTool.id}</p>
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-900">Schema结构</h3>
                <div className="mt-2 p-3 bg-gray-50 rounded border max-h-64 overflow-auto">
                  {renderSchemaStructure(selectedTool.schema)}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-900">可用参数</h3>
                <div className="mt-2 p-3 bg-gray-50 rounded border max-h-64 overflow-auto">
                  {(() => {
                    const properties = getToolProperties(selectedTool.schema);
                    if (Object.keys(properties).length === 0) {
                      return <div className="text-gray-500">无可配置参数</div>;
                    }
                    return (
                      <div className="space-y-2">
                        {Object.entries(properties).map(([key, field]) => (
                          <div key={key} className="text-sm">
                            <span className="font-medium text-blue-600">{key}:</span>
                            <span className="ml-2 text-gray-600">
                              {typeof field === 'object' && field ? 
                                (field as any).type || 'object' : 
                                typeof field
                              }
                            </span>
                          </div>
                        ))}
                      </div>
                    );
                  })()}
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-900">JSON数据</h3>
                <div className="mt-2 p-3 bg-gray-50 rounded border max-h-64 overflow-auto">
                  <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                    {JSON.stringify(selectedTool, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              请选择一个工具查看详情
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 