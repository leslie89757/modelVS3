import React, { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Brain, 
  Bot, 
  Palette, 
  Wrench, 
  Play, 
  MessageSquare, 
  Settings, 
  Zap, 
  Menu, 
  X, 
  User, 
  LogOut,
  ChevronDown,
  Store,
  TestTube
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

interface AuthenticatedLayoutProps {
  children: React.ReactNode
}

const navigation = [
  { name: '仪表板', href: '/', icon: LayoutDashboard },
  { name: '模型管理', href: '/models', icon: Brain },
  { name: 'Agent 管理', href: '/agents', icon: Bot },
  { name: 'Agent 设计器', href: '/agent-designer', icon: Palette },
  { name: 'Agent 市场', href: '/marketplace', icon: Store },
  { name: '工具管理', href: '/tools', icon: Wrench },
  { name: '执行记录', href: '/runs', icon: Play },
  { name: '模型对话', href: '/chat', icon: MessageSquare },
  { name: '🧪 测试页面', href: '/test-page', icon: TestTube },
  { name: '操练场', href: '/multi-model-workspace', icon: Zap },
  { name: '设置', href: '/settings', icon: Settings },
]

export default function AuthenticatedLayout({ children }: AuthenticatedLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 移动端侧边栏 */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-full max-w-xs flex-col bg-white shadow-xl">
          <div className="flex h-16 items-center justify-between px-4">
            <div className="flex items-center space-x-2">
              <Zap className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">ModelVS3</span>
            </div>
            <button
              type="button"
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          <nav className="mt-5 flex-1 px-2 pb-4">
            <ul className="space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <li key={item.name}>
                    <a
                      href={item.href}
                      className={`${
                        isActive
                          ? 'bg-primary-100 text-primary-700'
                          : 'text-gray-700 hover:text-primary-700 hover:bg-gray-100'
                      } group flex items-center px-2 py-2 text-base font-medium rounded-md transition-colors`}
                      onClick={() => setSidebarOpen(false)}
                    >
                      <Icon
                        className={`${
                          isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-primary-500'
                        } mr-3 h-6 w-6 transition-colors`}
                      />
                      {item.name}
                    </a>
                  </li>
                )
              })}
            </ul>
          </nav>
        </div>
      </div>

      {/* 桌面端侧边栏 */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white border-r border-gray-200 px-6 pb-4">
          <div className="flex h-16 shrink-0 items-center">
            <div className="flex items-center space-x-2">
              <Zap className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">ModelVS3</span>
            </div>
          </div>
          <nav className="flex flex-1 flex-col">
            <ul className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul className="space-y-1">
                  {navigation.map((item) => {
                    const Icon = item.icon
                    const isActive = location.pathname === item.href
                    return (
                      <li key={item.name}>
                        <a
                          href={item.href}
                          className={`${
                            isActive
                              ? 'bg-primary-100 text-primary-700'
                              : 'text-gray-700 hover:text-primary-700 hover:bg-gray-100'
                          } group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors`}
                        >
                          <Icon
                            className={`${
                              isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-primary-500'
                            } mr-3 h-5 w-5 transition-colors`}
                          />
                          {item.name}
                        </a>
                      </li>
                    )
                  })}
                </ul>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="lg:pl-64">
        {/* 顶部导航栏 */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          {/* 分隔符 */}
          <div className="h-6 w-px bg-gray-900/10 lg:hidden" />

          <div className="flex flex-1 justify-end gap-x-4 self-stretch lg:gap-x-6">
            {/* 用户菜单 */}
            <div className="relative">
              <button
                type="button"
                className="flex items-center gap-x-2 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
              >
                <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <User className="h-5 w-5 text-primary-600" />
                </div>
                <span className="hidden sm:flex sm:items-center">
                  <span className="text-sm font-medium leading-6 text-gray-900">
                    {user?.full_name || user?.email || '用户'}
                  </span>
                  <ChevronDown className="ml-2 h-5 w-5 text-gray-400" />
                </span>
              </button>

              {/* 用户下拉菜单 */}
              {userMenuOpen && (
                <div className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div className="px-4 py-2 text-sm text-gray-700 border-b">
                    <div className="font-medium">{user?.full_name || '用户'}</div>
                    <div className="text-gray-500 text-xs">{user?.email}</div>
                  </div>
                  <a
                    href="/settings"
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <div className="flex items-center">
                      <Settings className="mr-2 h-4 w-4" />
                      账户设置
                    </div>
                  </a>
                  <button
                    onClick={() => {
                      setUserMenuOpen(false)
                      handleLogout()
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <div className="flex items-center">
                      <LogOut className="mr-2 h-4 w-4" />
                      退出登录
                    </div>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 页面内容 */}
        <main className="py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>

      {/* 点击外部关闭用户菜单 */}
      {userMenuOpen && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setUserMenuOpen(false)}
        />
      )}
    </div>
  )
} 