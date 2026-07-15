import { useState, useEffect, useCallback } from 'react'
import Taro from '@tarojs/taro'

interface NetworkState {
  isConnected: boolean
  networkType: string
  isChecking: boolean
}

export function useNetwork() {
  const [state, setState] = useState<NetworkState>({
    isConnected: true,
    networkType: 'unknown',
    isChecking: true,
  })

  const checkNetwork = useCallback(async () => {
    setState((prev) => ({ ...prev, isChecking: true }))
    try {
      const res = await Taro.getNetworkType()
      const isConnected = res.networkType !== 'none'
      setState({
        isConnected,
        networkType: res.networkType,
        isChecking: false,
      })
      return isConnected
    } catch {
      setState((prev) => ({ ...prev, isChecking: false }))
      return true
    }
  }, [])

  useEffect(() => {
    checkNetwork()

    // 监听网络状态变化
    const handleNetworkChange = (res: { isConnected: boolean; networkType: string }) => {
      setState({
        isConnected: res.isConnected,
        networkType: res.networkType,
        isChecking: false,
      })
    }

    Taro.onNetworkStatusChange(handleNetworkChange)

    return () => {
      Taro.offNetworkStatusChange(handleNetworkChange)
    }
  }, [checkNetwork])

  return {
    ...state,
    checkNetwork,
  }
}

// ===== 缓存工具 =====

const CACHE_PREFIX = 'floodshield_cache_'

interface CacheEntry<T> {
  data: T
  timestamp: number
}

export function setCacheData<T>(key: string, data: T): void {
  try {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
    }
    Taro.setStorageSync(`${CACHE_PREFIX}${key}`, JSON.stringify(entry))
  } catch {
    // 静默失败
  }
}

export function getCacheData<T>(key: string): { data: T | null; timestamp: number | null } {
  try {
    const raw = Taro.getStorageSync(`${CACHE_PREFIX}${key}`)
    if (!raw) return { data: null, timestamp: null }
    const entry: CacheEntry<T> = JSON.parse(raw)
    return { data: entry.data, timestamp: entry.timestamp }
  } catch {
    return { data: null, timestamp: null }
  }
}

export function getCacheAge(timestamp: number | null): string {
  if (!timestamp) return ''
  const diffMs = Date.now() - timestamp
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}小时前`
  return `${Math.floor(diffHour / 24)}天前`
}
