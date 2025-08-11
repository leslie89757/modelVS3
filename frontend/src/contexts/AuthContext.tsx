import React, { createContext, useContext, useEffect, useState } from 'react'
import toast from 'react-hot-toast'

export interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  tenant_id?: string
  created_at: string
  updated_at?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string, tokenType: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user && !!token

  // 刷新token
  const refreshTokens = async (currentToken: string) => {
    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        const newToken = data.access_token
        
        // 更新存储的token
        localStorage.setItem('token', newToken)
        setToken(newToken)
        
        console.log('🔄 Token已自动刷新')
        return newToken
      } else {
        throw new Error('Token refresh failed')
      }
    } catch (error) {
      console.error('Error refreshing token:', error)
      throw error
    }
  }

  // 获取用户信息
  const fetchUser = async (authToken: string) => {
    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        
        // 检查是否需要刷新token
        const refreshSuggested = response.headers.get('X-Token-Refresh-Suggested')
        if (refreshSuggested === 'true') {
          try {
            await refreshTokens(authToken)
          } catch (error) {
            console.error('自动刷新token失败:', error)
          }
        }
        
        return userData
      } else {
        // Token可能过期，清除本地存储
        localStorage.removeItem('token')
        localStorage.removeItem('token_type')
        setToken(null)
        setUser(null)
        throw new Error('Failed to fetch user')
      }
    } catch (error) {
      console.error('Error fetching user:', error)
      localStorage.removeItem('token')
      localStorage.removeItem('token_type')
      setToken(null)
      setUser(null)
      throw error
    }
  }

  // 登录
  const login = async (accessToken: string, tokenType: string = 'bearer') => {
    setIsLoading(true)
    try {
      // 存储token
      localStorage.setItem('token', accessToken)
      localStorage.setItem('token_type', tokenType)
      setToken(accessToken)

      // 获取用户信息
      await fetchUser(accessToken)
      
      toast.success('登录成功！')
    } catch (error) {
      console.error('Login error:', error)
      logout()
      toast.error('登录失败，请重试')
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  // 登出
  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('token_type')
    setToken(null)
    setUser(null)
    toast.success('已安全退出')
  }

  // 刷新用户信息
  const refreshUser = async () => {
    if (!token) return
    
    try {
      await fetchUser(token)
    } catch (error) {
      console.error('Error refreshing user:', error)
      logout()
    }
  }

  // 初始化认证状态
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true)
      try {
        const storedToken = localStorage.getItem('token')
        const storedTokenType = localStorage.getItem('token_type')

        if (storedToken && storedTokenType) {
          setToken(storedToken)
          await fetchUser(storedToken)
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        // 清除无效的token
        localStorage.removeItem('token')
        localStorage.removeItem('token_type')
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  // 定期检查用户状态
  useEffect(() => {
    if (!token) return

    const checkInterval = setInterval(async () => {
      try {
        await refreshUser()
      } catch (error) {
        console.error('User status check failed:', error)
        logout()
      }
    }, 2 * 60 * 60 * 1000) // 每2小时检查一次用户状态

    return () => clearInterval(checkInterval)
  }, [token])

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// 高阶组件：要求用户登录
export const withAuth = <P extends object>(
  WrappedComponent: React.ComponentType<P>
) => {
  const AuthenticatedComponent = (props: P) => {
    const { isAuthenticated, isLoading } = useAuth()

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
        </div>
      )
    }

    if (!isAuthenticated) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full text-center">
            <div className="bg-white rounded-lg shadow-md p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">需要登录</h2>
              <p className="text-gray-600 mb-6">请登录后继续使用该功能</p>
              <a
                href="/login"
                className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
              >
                去登录
              </a>
            </div>
          </div>
        </div>
      )
    }

    return <WrappedComponent {...props} />
  }

  AuthenticatedComponent.displayName = `withAuth(${WrappedComponent.displayName || WrappedComponent.name})`

  return AuthenticatedComponent
} 