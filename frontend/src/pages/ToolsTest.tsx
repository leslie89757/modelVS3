import { useState } from 'react'
import { Plus, Eye, Edit, Trash2 } from 'lucide-react'

export default function ToolsTest() {
  const [message, setMessage] = useState('页面加载完成')
  const [showModal, setShowModal] = useState(false)
  const [clickCount, setClickCount] = useState(0)

  const handleButtonClick = (buttonName: string) => {
    setMessage(`点击了 ${buttonName} 按钮`)
    setClickCount(prev => prev + 1)
    console.log(`按钮点击: ${buttonName}`)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">工具页面按钮测试</h1>
      
      <div className="bg-white p-4 rounded-lg border mb-6">
        <p className="text-green-600 font-semibold">状态: {message}</p>
        <p className="text-blue-600">点击次数: {clickCount}</p>
      </div>

      {/* 基础按钮测试 */}
      <div className="bg-white p-6 rounded-lg border mb-6">
        <h2 className="text-lg font-semibold mb-4">基础按钮测试</h2>
        <div className="flex space-x-3">
          <button
            onClick={() => handleButtonClick('添加工具')}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            添加工具
          </button>
          
          <button
            onClick={() => handleButtonClick('刷新')}
            className="btn-secondary"
          >
            刷新
          </button>
          
          <button
            onClick={() => {
              handleButtonClick('显示模态框')
              setShowModal(true)
            }}
            className="btn-secondary"
          >
            显示模态框
          </button>
        </div>
      </div>

      {/* 工具卡片测试 */}
      <div className="bg-white p-6 rounded-lg border mb-6">
        <h2 className="text-lg font-semibold mb-4">工具卡片按钮测试</h2>
        <div className="border rounded-lg p-4">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-semibold">测试工具</h3>
              <p className="text-sm text-gray-600">这是一个测试工具</p>
            </div>
            <span className="bg-green-100 text-green-800 px-2 py-1 text-xs rounded-full">
              已启用
            </span>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => handleButtonClick('查看')}
              className="btn-secondary flex-1 text-sm"
            >
              <Eye className="h-4 w-4 mr-1" />
              查看
            </button>
            <button
              onClick={() => handleButtonClick('编辑')}
              className="btn-secondary text-sm"
            >
              <Edit className="h-4 w-4" />
            </button>
            <button
              onClick={() => handleButtonClick('删除')}
              className="btn-secondary text-sm text-red-600"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* API测试 */}
      <div className="bg-white p-6 rounded-lg border mb-6">
        <h2 className="text-lg font-semibold mb-4">API测试</h2>
        <button
          onClick={async () => {
            try {
              setMessage('正在获取工具列表...')
              const response = await fetch('/api/v1/tools/')
              if (response.ok) {
                const tools = await response.json()
                setMessage(`成功获取 ${tools.length} 个工具`)
              } else {
                setMessage(`API错误: ${response.status}`)
              }
            } catch (error) {
              setMessage(`网络错误: ${error instanceof Error ? error.message : '未知错误'}`)
            }
          }}
          className="btn-primary"
        >
          测试API
        </button>
      </div>

      {/* 模态框测试 */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">测试模态框</h3>
            <p className="mb-4">这是一个测试模态框，用于验证模态框功能是否正常。</p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  handleButtonClick('关闭模态框')
                  setShowModal(false)
                }}
                className="btn-secondary"
              >
                关闭
              </button>
              <button
                onClick={() => {
                  handleButtonClick('确认')
                  setShowModal(false)
                }}
                className="btn-primary"
              >
                确认
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 