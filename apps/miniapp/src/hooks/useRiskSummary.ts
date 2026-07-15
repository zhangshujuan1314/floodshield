import { useState, useEffect, useCallback } from 'react'
import Taro from '@tarojs/taro'
import type { RiskSummaryData } from '../services/api'
import { getRiskSummary } from '../services/api'
import { getMockRiskSummary } from '../services/mock'

interface RiskSummaryState {
  data: RiskSummaryData | null
  loading: boolean
  error: string | null
}

export function useRiskSummary(lat: number | null, lng: number | null) {
  const [state, setState] = useState<RiskSummaryState>({
    data: null,
    loading: false,
    error: null,
  })

  const fetchData = useCallback(async () => {
    if (lat === null || lng === null) return

    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const res = await getRiskSummary(lat, lng)
      setState({
        data: res.data,
        loading: false,
        error: null,
      })
    } catch {
      // 降级到模拟数据（开发阶段）
      setState({
        data: getMockRiskSummary(),
        loading: false,
        error: null,
      })
    }
  }, [lat, lng])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const refresh = useCallback(async () => {
    await fetchData()
    Taro.showToast({ title: '已刷新', icon: 'success' })
  }, [fetchData])

  return {
    ...state,
    refresh,
  }
}
