import { TestTube } from 'lucide-react'

export default function TestPage() {
  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center space-y-4">
          <TestTube className="w-16 h-16 mx-auto text-purple-600" />
          <h1 className="text-3xl font-bold text-gray-900">测试页面</h1>
          <p className="text-lg text-gray-600">
            这是一个测试页面，用于验证导航栏是否能正常添加新的菜单项。
          </p>
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            ✅ 如果你能看到这个页面，说明导航栏功能正常！
          </div>
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded">
            📝 创建时间: {new Date().toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  )
} 