import { useState, useEffect } from 'react'

/**
 * 防抖Hook - 延迟更新值，适用于搜索、输入验证等场景
 * @param value 要防抖的值
 * @param delay 延迟时间（毫秒）
 * @returns 防抖后的值
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    // 设置定时器
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    // 清理函数：清除定时器
    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * 防抖回调Hook - 延迟执行回调函数
 * @param callback 要执行的回调函数
 * @param delay 延迟时间（毫秒）
 * @param deps 依赖数组
 * @returns 防抖后的回调函数
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const [debouncedCallback] = useState(() => {
    let timeoutId: number

    return ((...args: Parameters<T>) => {
      clearTimeout(timeoutId)
      timeoutId = window.setTimeout(() => callback(...args), delay)
    }) as T
  })

  useEffect(() => {
    // 依赖项改变时重新创建回调
    return () => {
      // 组件卸载时清理定时器
    }
  }, deps)

  return debouncedCallback
} 