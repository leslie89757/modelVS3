
import { Save, Key, Shield, Bell } from 'lucide-react'

export default function Settings() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
        <p className="mt-2 text-gray-600">配置您的 Agent 平台</p>
      </div>

      <div className="space-y-6">
        {/* API 密钥设置 */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Key className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">API 密钥</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="label">OpenAI API Key</label>
              <input type="password" className="input" placeholder="sk-..." />
            </div>
            <div>
              <label className="label">Anthropic API Key</label>
              <input type="password" className="input" placeholder="sk-ant-..." />
            </div>
            <div>
              <label className="label">Google API Key</label>
              <input type="password" className="input" placeholder="AIza..." />
            </div>
          </div>
        </div>

        {/* 安全设置 */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">安全设置</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">JWT 过期时间</p>
                <p className="text-sm text-gray-500">访问令牌的有效期</p>
              </div>
              <select className="input w-32">
                <option>30 分钟</option>
                <option>1 小时</option>
                <option>24 小时</option>
              </select>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">速率限制</p>
                <p className="text-sm text-gray-500">每分钟最大请求数</p>
              </div>
              <input type="number" className="input w-32" defaultValue={60} />
            </div>
          </div>
        </div>

        {/* 通知设置 */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Bell className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">通知设置</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">执行失败通知</p>
                <p className="text-sm text-gray-500">当 Agent 执行失败时发送通知</p>
              </div>
              <input type="checkbox" className="rounded" defaultChecked />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">成本预警</p>
                <p className="text-sm text-gray-500">当成本超过阈值时发送通知</p>
              </div>
              <input type="checkbox" className="rounded" defaultChecked />
            </div>
            
            <div>
              <label className="label">通知邮箱</label>
              <input type="email" className="input" placeholder="admin@example.com" />
            </div>
          </div>
        </div>

        {/* 保存按钮 */}
        <div className="flex justify-end">
          <button className="btn-primary">
            <Save className="h-4 w-4 mr-2" />
            保存设置
          </button>
        </div>
      </div>
    </div>
  )
} 