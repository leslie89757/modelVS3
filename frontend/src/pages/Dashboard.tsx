import { Activity, Users, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'

interface DashboardStats {
  total_runs: number
  active_agents: number
  total_cost_usd: number
  avg_response_time_ms: number
  daily_usage: Array<{
    date: string
    request_count: number
    input_tokens: number
    output_tokens: number
    cost_usd: number
  }>
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/v1/dashboard/stats')
        if (response.ok) {
          const data = await response.json()
          setStats(data)
        } else {
          console.error('获取仪表板数据失败')
        }
      } catch (error) {
        console.error('获取仪表板数据错误:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="h-16 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center text-gray-500">
          无法加载仪表板数据
        </div>
      </div>
    )
  }

  const maxValue = Math.max(...stats.daily_usage.map(d => d.request_count))

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">控制台</h1>
        <p className="mt-2 text-gray-600">欢迎使用 Agent 平台管理后台</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">总运行次数</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_runs.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Users className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">活跃 Agent</p>
              <p className="text-2xl font-bold text-gray-900">{stats.active_agents}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Zap className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">平均响应时间</p>
              <p className="text-2xl font-bold text-gray-900">{Math.round(stats.avg_response_time_ms)}ms</p>
            </div>
          </div>
        </div>
      </div>

      {/* 使用趋势图 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">最近7天使用趋势</h2>
        <div className="flex items-end space-x-2 h-32">
          {stats.daily_usage.map((day, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-blue-500 rounded-t"
                style={{
                  height: `${(day.request_count / maxValue) * 100}%`,
                  minHeight: '4px'
                }}
              />
              <span className="text-xs text-gray-500 mt-2">
                {new Date(day.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
} 