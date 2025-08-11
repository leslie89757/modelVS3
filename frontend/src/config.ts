// API 配置
const getApiBaseUrl = () => {
  // 开发环境下使用环境变量
  if ((import.meta as any).env?.DEV) {
    return (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001'
  }
  
  // 生产环境下使用相对路径（通过nginx代理）
  // 这样可以避免CORS问题，所有API请求都通过nginx转发
  const hostname = window.location.hostname
  
  // 本地开发环境特殊处理
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // 根据前端端口判断对应的API端口
    const port = window.location.port === '3004' ? ':8001' : ':8000'
    return `${window.location.protocol}//${hostname}${port}`
  }
  
  // 远程生产环境：使用空字符串，通过nginx代理转发
  // API请求 /api/v1/auth/login 会被nginx代理到后端api:8000
  return ''
}

export const API_BASE_URL = getApiBaseUrl()

// API 请求工具函数
export const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const response = await fetch(url, {
    ...options,
    headers: defaultHeaders,
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`)
  }

  return response
}

// 全局 fetch 拦截器 - 自动处理API路径和认证
const originalFetch = window.fetch
window.fetch = async function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  // 处理URL重写
  let finalInput = input
  let finalInit = { ...init }
  
  // 如果是相对路径的API请求，转换为绝对路径
  if (typeof input === 'string' && input.startsWith('/api/')) {
    finalInput = `${API_BASE_URL}${input}`
  } else if (input instanceof Request && input.url.startsWith('/api/')) {
    finalInput = new Request(`${API_BASE_URL}${input.url}`, input)
  }
  
  // 自动添加认证头（除了登录和注册接口）
  const token = localStorage.getItem('token')
  const isApiRequest = (typeof finalInput === 'string' && finalInput.includes('/api/')) || 
                      (finalInput instanceof Request && finalInput.url.includes('/api/'))
  const isAuthEndpoint = (typeof finalInput === 'string' && 
                         (finalInput.includes('/auth/login') || finalInput.includes('/auth/register'))) ||
                        (finalInput instanceof Request && 
                         (finalInput.url.includes('/auth/login') || finalInput.url.includes('/auth/register')))
  
  if (isApiRequest && !isAuthEndpoint && token) {
    const headers = new Headers(finalInit.headers)
    if (!headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    finalInit.headers = headers
  }
  
  // 发送请求
  const response = await originalFetch.call(this, finalInput, finalInit)
  
  // 检查是否需要刷新token
  if (response.ok && response.headers.get('X-Token-Refresh-Suggested') === 'true') {
    try {
      const refreshResponse = await originalFetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      
      if (refreshResponse.ok) {
        const data = await refreshResponse.json()
        localStorage.setItem('token', data.access_token)
        console.log('🔄 Token已自动刷新')
      }
    } catch (error) {
      console.error('自动刷新token失败:', error)
    }
  }
  
  return response
}

// 日志输出，便于调试
console.log('🔧 API配置:', {
  baseUrl: API_BASE_URL,
  env: (import.meta as any).env?.DEV ? 'development' : 'production',
  viteApiUrl: (import.meta as any).env?.VITE_API_URL
})

console.log('🌐 Fetch拦截器已启用，所有/api/请求将重定向到:', API_BASE_URL) 