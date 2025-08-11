import { useState, useEffect } from 'react'

/**
 * 安全的 localStorage hook
 * @param key 存储键名
 * @param defaultValue 默认值
 * @returns [值, 设置函数, 删除函数]
 */
export function useLocalStorage<T>(
  key: string,
  defaultValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  // 初始化状态
  const [value, setValue] = useState<T>(() => {
    try {
      if (typeof window === 'undefined') {
        return defaultValue
      }

      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return defaultValue
    }
  })

  // 设置值的函数
  const setStoredValue = (newValue: T | ((prev: T) => T)) => {
    try {
      const valueToStore = newValue instanceof Function ? newValue(value) : newValue
      setValue(valueToStore)

      if (typeof window !== 'undefined') {
        if (valueToStore === undefined) {
          window.localStorage.removeItem(key)
        } else {
          window.localStorage.setItem(key, JSON.stringify(valueToStore))
        }
      }
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }

  // 删除值的函数
  const removeValue = () => {
    try {
      setValue(defaultValue)
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key)
      }
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error)
    }
  }

  // 监听存储变化
  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setValue(JSON.parse(e.newValue))
        } catch (error) {
          console.warn(`Error parsing localStorage value for key "${key}":`, error)
        }
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [key])

  return [value, setStoredValue, removeValue]
}

/**
 * 简化版本的 localStorage hook，只返回值和设置函数
 */
export function useSimpleLocalStorage<T>(key: string, defaultValue: T) {
  const [value, setValue] = useLocalStorage(key, defaultValue)
  return [value, setValue] as const
} 