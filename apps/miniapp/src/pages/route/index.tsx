import { View, Text, Input, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useCallback } from 'react'
import { useLocation } from '../../hooks/useLocation'
import { getRoutes } from '../../services/api'
import { getMockRoutes } from '../../services/mock'
import type { RouteData } from '../../services/api'
import RiskBadge from '../../components/RiskBadge'
import ExpiredBanner from '../../components/ExpiredBanner'
import LoadingState from '../../components/LoadingState'
import ErrorState from '../../components/ErrorState'
import EmptyState from '../../components/EmptyState'
import { type RiskBandKey } from '../../utils/constants'
import './index.scss'

type SearchStatus = 'idle' | 'searching' | 'done' | 'error'

export default function RoutePage() {
  const location = useLocation()
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [routes, setRoutes] = useState<RouteData[]>([])
  const [searchStatus, setSearchStatus] = useState<SearchStatus>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleUseCurrentLocation = useCallback(() => {
    if (location.latitude && location.longitude) {
      setOrigin('当前位置')
    } else {
      Taro.showToast({ title: '无法获取当前位置', icon: 'none' })
    }
  }, [location])

  const handleSearch = useCallback(async () => {
    if (!origin) {
      Taro.showToast({ title: '请输入出发地', icon: 'none' })
      return
    }
    if (!destination) {
      Taro.showToast({ title: '请输入目的地', icon: 'none' })
      return
    }

    setSearchStatus('searching')
    setErrorMsg('')

    try {
      // 使用当前位置作为起点坐标（简化处理）
      const oLat = location.latitude || 31.95
      const oLng = location.longitude || 118.84
      // 目的地坐标在实际场景中需要通过地理编码获取，此处使用模拟坐标
      const dLat = 31.9534
      const dLng = 118.8398

      try {
        const res = await getRoutes(oLat, oLng, dLat, dLng)
        setRoutes(res.data)
      } catch {
        // 降级到模拟数据
        setRoutes(getMockRoutes())
      }

      setSearchStatus('done')
    } catch (err) {
      setSearchStatus('error')
      setErrorMsg(err instanceof Error ? err.message : '路线查询失败')
    }
  }, [origin, destination, location])

  return (
    <ScrollView className="route-page" scrollY enableFlex>
      <View className="container">
        {/* 搜索区域 */}
        <View className="search-card card">
          <View className="search-row">
            <Text className="search-dot search-dot-origin">起</Text>
            <Input
              className="search-input"
              placeholder="出发地"
              value={origin}
              onInput={(e) => setOrigin(e.detail.value)}
            />
            <View className="btn-locate" onClick={handleUseCurrentLocation}>
              <Text className="btn-locate-icon">📍</Text>
            </View>
          </View>

          <View className="search-divider" />

          <View className="search-row">
            <Text className="search-dot search-dot-dest">终</Text>
            <Input
              className="search-input"
              placeholder="目的地（避险点、安全区域等）"
              value={destination}
              onInput={(e) => setDestination(e.detail.value)}
            />
          </View>

          <View
            className={`btn-search ${searchStatus === 'searching' ? 'btn-disabled' : ''}`}
            onClick={searchStatus === 'searching' ? undefined : handleSearch}
          >
            <Text className="btn-search-text">
              {searchStatus === 'searching' ? '查询中...' : '查询安全路线'}
            </Text>
          </View>
        </View>

        {/* 加载中 */}
        {searchStatus === 'searching' && <LoadingState text="正在规划安全路线..." />}

        {/* 错误 */}
        {searchStatus === 'error' && (
          <ErrorState
            message={errorMsg}
            retryText="重新查询"
            onRetry={handleSearch}
          />
        )}

        {/* 无结果 */}
        {searchStatus === 'done' && routes.length === 0 && (
          <EmptyState
            icon="🗺️"
            title="未找到安全路线"
            description="无法规划从出发地到目的地的安全路线，请尝试其他地点或联系救援部门"
          />
        )}

        {/* 路线结果 */}
        {routes.length > 0 && (
          <View className="routes-section">
            <Text className="section-title">推荐路线（共{routes.length}条）</Text>

            {routes.map((route, routeIdx) => {
              const overallRiskKey = route.overallRisk as RiskBandKey
              const isExpired = checkExpired(route.expiresAt)

              return (
                <View key={route.id} className="route-card card">
                  {/* 过期提醒 */}
                  <ExpiredBanner
                    expiresAt={route.expiresAt}
                    onRefresh={handleSearch}
                  />

                  {/* 路线头部 */}
                  <View className="route-header">
                    <Text className="route-label">路线 {routeIdx + 1}</Text>
                    <RiskBadge riskKey={overallRiskKey} size="small" />
                  </View>

                  {/* 路线概览 */}
                  <View className="route-overview">
                    <View className="route-stat">
                      <Text className="route-stat-value">
                        {route.totalDistance < 1000
                          ? `${route.totalDistance}米`
                          : `${(route.totalDistance / 1000).toFixed(1)}公里`}
                      </Text>
                      <Text className="route-stat-label">总距离</Text>
                    </View>
                    <View className="route-stat-divider" />
                    <View className="route-stat">
                      <Text className="route-stat-value">{route.totalDuration}分钟</Text>
                      <Text className="route-stat-label">预计时间</Text>
                    </View>
                    <View className="route-stat-divider" />
                    <View className="route-stat">
                      <Text className="route-stat-value">{route.segments.length}段</Text>
                      <Text className="route-stat-label">路段数</Text>
                    </View>
                  </View>

                  {/* 路段详情 */}
                  <View className="route-segments">
                    {route.segments.map((seg, segIdx) => (
                      <View key={segIdx} className="segment">
                        <View className="segment-header">
                          <Text className="segment-label">路段 {segIdx + 1}</Text>
                          <View
                            className="segment-risk"
                            style={{ backgroundColor: seg.riskColor + '20', borderColor: seg.riskColor }}
                          >
                            <Text style={{ color: seg.riskColor, fontSize: 'var(--font-size-xs)', fontWeight: '600' }}>
                              {seg.riskLabel}
                            </Text>
                          </View>
                        </View>

                        <View className="segment-meta">
                          <Text className="segment-meta-text">
                            {seg.distance < 1000
                              ? `${seg.distance}米`
                              : `${(seg.distance / 1000).toFixed(1)}公里`}
                            {' · '}
                            {seg.duration}分钟
                          </Text>
                        </View>

                        {/* 证据 */}
                        {seg.evidence.length > 0 && (
                          <View className="segment-evidence">
                            <Text className="segment-evidence-title">依据：</Text>
                            {seg.evidence.map((ev, evIdx) => (
                              <Text key={evIdx} className="segment-evidence-item">
                                · {ev}
                              </Text>
                            ))}
                          </View>
                        )}

                        {/* 未知风险警告 */}
                        {seg.unknownRisk && (
                          <View className="unknown-risk-warning">
                            <Text className="unknown-risk-icon">⚠️</Text>
                            <Text className="unknown-risk-text">
                              该路段缺乏实时数据，实际风险未知，请谨慎通行
                            </Text>
                          </View>
                        )}
                      </View>
                    ))}
                  </View>

                  {/* 路线来源和过期时间 */}
                  <View className="route-footer">
                    <Text className="route-source">数据来源：{route.source}</Text>
                    <Text className="route-expires">
                      有效至 {formatTime(route.expiresAt)}
                    </Text>
                  </View>
                </View>
              )
            })}

            {/* 免责声明 */}
            <View className="disclaimer">
              <Text>
                路线风险评估基于AI分析和多源数据，仅供参考。
                路况可能随时变化，请以现场标志及官方指令为准。
                紧急情况请拨打110或119求助。
              </Text>
            </View>
          </View>
        )}

        {/* 初始状态提示 */}
        {searchStatus === 'idle' && (
          <View className="idle-hint">
            <Text className="idle-hint-icon">🗺️</Text>
            <Text className="idle-hint-title">安全路线查询</Text>
            <Text className="idle-hint-desc">
              输入出发地和目的地，系统将为您规划风险最低的避险路线
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  )
}

function checkExpired(expiresAt: string): boolean {
  try {
    return new Date(expiresAt).getTime() < Date.now()
  } catch {
    return false
  }
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    const hour = d.getHours().toString().padStart(2, '0')
    const minute = d.getMinutes().toString().padStart(2, '0')
    return `${hour}:${minute}`
  } catch {
    return ''
  }
}
