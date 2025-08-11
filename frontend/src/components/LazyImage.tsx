import React, { useState, useRef, useEffect } from 'react'
import { ImageIcon } from 'lucide-react'

interface LazyImageProps {
  src: string
  alt: string
  className?: string
  placeholder?: React.ReactNode
  fallback?: React.ReactNode
  onLoad?: () => void
  onError?: () => void
}

export default function LazyImage({
  src,
  alt,
  className = '',
  placeholder,
  fallback,
  onLoad,
  onError,
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isError, setIsError] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)

  // 使用 Intersection Observer 实现懒加载
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
      }
    )

    if (imgRef.current) {
      observer.observe(imgRef.current)
    }

    return () => observer.disconnect()
  }, [])

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setIsError(true)
    onError?.()
  }

  const defaultPlaceholder = (
    <div className={`bg-gray-200 animate-pulse flex items-center justify-center ${className}`}>
      <ImageIcon className="w-8 h-8 text-gray-400" />
    </div>
  )

  const defaultFallback = (
    <div className={`bg-gray-100 flex items-center justify-center ${className}`}>
      <ImageIcon className="w-8 h-8 text-gray-400" />
    </div>
  )

  // 错误状态
  if (isError) {
    return fallback || defaultFallback
  }

  // 未进入视口或未加载
  if (!isInView || !isLoaded) {
    return (
      <div ref={imgRef} className={className}>
        {!isInView ? (
          placeholder || defaultPlaceholder
        ) : (
          <>
            {placeholder || defaultPlaceholder}
            <img
              src={src}
              alt={alt}
              onLoad={handleLoad}
              onError={handleError}
              className="absolute inset-0 w-full h-full object-cover opacity-0"
            />
          </>
        )}
      </div>
    )
  }

  // 加载完成
  return (
    <img
      ref={imgRef}
      src={src}
      alt={alt}
      className={className}
      onError={handleError}
    />
  )
}

// 头像专用的懒加载组件
export function LazyAvatar({
  src,
  alt,
  size = 'md',
  className = '',
  fallbackText,
}: {
  src?: string
  alt: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  fallbackText?: string
}) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-lg',
  }

  const fallback = (
    <div
      className={`
        ${sizeClasses[size]} 
        bg-primary-100 rounded-full flex items-center justify-center 
        ${className}
      `}
    >
      {fallbackText ? (
        <span className="font-medium text-primary-600">
          {fallbackText.charAt(0).toUpperCase()}
        </span>
      ) : (
        <ImageIcon className="w-1/2 h-1/2 text-primary-400" />
      )}
    </div>
  )

  if (!src) {
    return fallback
  }

  return (
    <LazyImage
      src={src}
      alt={alt}
      className={`${sizeClasses[size]} rounded-full object-cover ${className}`}
      fallback={fallback}
      placeholder={fallback}
    />
  )
} 