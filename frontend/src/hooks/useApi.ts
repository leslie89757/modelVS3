import { useAuth } from '../contexts/AuthContext'
import { useCallback } from 'react'
import toast from 'react-hot-toast'

interface ApiOptions extends RequestInit {
  skipAuth?: boolean
  skipToast?: boolean
}

export const useApi = () => {
  const { token, logout } = useAuth()

  const apiRequest = useCallback(async (
    endpoint: string, 
    options: ApiOptions = {}
  ) => {
    const { skipAuth = false, skipToast = false, ...fetchOptions } = options

    // 构建请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // 添加原有的headers
    if (fetchOptions.headers) {
      Object.assign(headers, fetchOptions.headers)
    }

    // 自动添加认证头
    if (!skipAuth && token) {
      headers.Authorization = `Bearer ${token}`
    }

    try {
      const response = await fetch(endpoint, {
        ...fetchOptions,
        headers,
      })

      // 处理401未授权错误
      if (response.status === 401) {
        if (!skipToast) {
          toast.error('登录已过期，请重新登录')
        }
        logout()
        throw new Error('未授权访问')
      }

      // 处理其他HTTP错误
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || errorData.message || `请求失败: ${response.status}`
        
        if (!skipToast) {
          toast.error(errorMessage)
        }
        throw new Error(errorMessage)
      }

      return response
    } catch (error) {
      // 网络错误处理
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = '网络连接失败，请检查网络后重试'
        if (!skipToast) {
          toast.error(networkError)
        }
        throw new Error(networkError)
      }
      
      // 重新抛出其他错误
      throw error
    }
  }, [token, logout])

  // 便捷方法
  const get = useCallback((endpoint: string, options: ApiOptions = {}) => {
    return apiRequest(endpoint, { ...options, method: 'GET' })
  }, [apiRequest])

  const post = useCallback((endpoint: string, data: any, options: ApiOptions = {}) => {
    return apiRequest(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    })
  }, [apiRequest])

  const put = useCallback((endpoint: string, data: any, options: ApiOptions = {}) => {
    return apiRequest(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }, [apiRequest])

  const del = useCallback((endpoint: string, options: ApiOptions = {}) => {
    return apiRequest(endpoint, { ...options, method: 'DELETE' })
  }, [apiRequest])

  const patch = useCallback((endpoint: string, data: any, options: ApiOptions = {}) => {
    return apiRequest(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }, [apiRequest])

  return {
    apiRequest,
    get,
    post,
    put,
    delete: del,
    patch,
  }
} 