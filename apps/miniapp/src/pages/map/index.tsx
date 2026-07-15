import { View, Text, ScrollView, Switch } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect, useCallback } from 'react'
import { useLocation } from '../../hooks/useLocation'
import { getMapLayers } from '../../services/api'
import { getMockMapLayers } from '../../services/mock'
import type { MapLayerData } from '../../services/api'
import { RISK_BANDS, SHELTER_STATUS } from '../../utils/constants'
import LoadingState from '../../components/LoadingState'
import ErrorState from '../../components/ErrorState'
import EmptyState from '../../components/EmptyState'
import './index.scss'

interface LayerToggle {
  key: string
  label: string
  icon: string
  enabled: boolean
}

export default function MapPage() {
  const location = useLocation()
  const [layerData, setLayerData] = useState<MapLayerData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mapAvailable, setMapAvailable] = useState(false)
  const [layers, setLayers] = useState<LayerToggle[]>([
    { key: 'alerts', label: '官方预警', icon: '⚠️', enabled: true },
    { key: 'risks', label: '平台风险', icon: '📊', enabled: true },
    { key: 'reports', label: '积水报告', icon: '💧', enabled: true },
    { key: 'roadEvents', label: '道路事件', icon: '🚧', enabled: true },
    { key: 'shelters', label: '避险场所', icon: '🏠', enabled: true },
  ])

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getMapLayers()
      setLayerData(res.data)
    } catch {
      // 降级到模拟数据
      setLayerData(getMockMapLayers())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // 检查地图组件是否可用（需要配置 key）
    try {
      Taro.requirePlugin?.('map')
      setMapAvailable(true)
    } catch {
      setMapAvailable(false)
    }
    fetchData()
  }, [fetchData])

  const toggleLayer = (key: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.key === key ? { ...l, enabled: !l.enabled } : l)),
    )
  }

  const enabledLayers = layers.filter((l) => l.enabled).map((l) => l.key)

  const formatTime = (isoStr: string): string => {
    try {
      const d = new Date(isoStr)
      const hour = d.getHours().toString().padStart(2, '0')
      const minute = d.getMinutes().toString().padStart(2, '0')
      return `${hour}:${minute}`
    } catch {
      return ''
    }
  }

  const getAlertLevelInfo = (level: string) => {
    const map: Record<string, { label: string; color: string; icon: string }> = {
      blue: { label: '蓝色预警', color: '#1890ff', icon: '🔵' },
      yellow: { label: '黄色预警', color: '#d48806', icon: '🟡' },
      orange: { label: '橙色预警', color: '#d4380d', icon: '🟠' },
      red: { label: '红色预警', color: '#cf1322', icon: '🔴' },
    }
    return map[level] || map.blue
  }

  const getReportTypeLabel = (type: string): string => {
    const map: Record<string, string> = {
      waterlogging: '积水',
      road_blocked: '道路无法通行',
      basement_flood: '地下空间进水',
      manhole_damaged: '井盖破损',
      person_trapped: '人员受困',
      other: '其他',
    }
    return map[type] || type
  }

  const getReportStatusInfo = (status: string) => {
    if (status === 'verified') return { label: '已核验', color: '#52c41a', icon: '✅' }
    if (status === 'rejected') return { label: '未通过', color: '#999999', icon: '❌' }
    return { label: '待核验', color: '#faad14', icon: '⏳' }
  }

  const getRoadEventTypeInfo = (type: string) => {
    if (type === '封闭' || type === 'closure') return { label: '道路封闭', color: '#ff4d4f', icon: '🚫' }
    if (type === '缓行' || type === 'slow') return { label: '道路缓行', color: '#faad14', icon: '🐢' }
    return { label: type, color: '#faad14', icon: '⚠️' }
  }

  if (loading) {
    return (
      <View className="container">
        <LoadingState text="加载地图数据..." />
      </View>
    )
  }

  if (error && !layerData) {
    return (
      <View className="container">
        <ErrorState
          title="加载失败"
          message={error}
          onRetry={fetchData}
        />
      </View>
    )
  }

  if (!layerData) {
    return (
      <View className="container">
        <EmptyState
          icon="🗺️"
          title="暂无数据"
          description="当前区域暂无图层数据"
          actionText="刷新"
          onAction={fetchData}
        />
      </View>
    )
  }

  return (
    <View className="map-page">
      {/* 地图区域 */}
      {mapAvailable && location.latitude && location.longitude ? (
        <View className="map-container">
          {/* 实际地图组件，需要配置 key 后启用 */}
          <View className="map-placeholder">
            <Text className="map-placeholder-icon">🗺️</Text>
            <Text className="map-placeholder-text">地图加载中...</Text>
            <Text className="map-placeholder-hint">请配置地图 SDK Key 后启用</Text>
          </View>
        </View>
      ) : (
        <View className="map-unavailable">
          <Text className="map-unavailable-icon">📋</Text>
          <Text className="map-unavailable-text">列表视图模式</Text>
          <Text className="map-unavailable-hint">地图暂不可用，已切换为列表视图</Text>
        </View>
      )}

      {/* 图层切换 */}
      <View className="layer-toggles">
        <Text className="layer-toggles-title">图层筛选</Text>
        <View className="layer-toggle-list">
          {layers.map((layer) => (
            <View key={layer.key} className="layer-toggle-item">
              <Text className="layer-toggle-icon">{layer.icon}</Text>
              <Text className="layer-toggle-label">{layer.label}</Text>
              <Switch
                checked={layer.enabled}
                onChange={() => toggleLayer(layer.key)}
                color="var(--color-primary)"
              />
            </View>
          ))}
        </View>
      </View>

      {/* 列表视图 */}
      <ScrollView className="list-fallback" scrollY>
        <View className="container">
          {/* 官方预警 */}
          {enabledLayers.includes('alerts') && layerData.alerts.length > 0 && (
            <View className="layer-section">
              <View className="layer-section-header">
                <Text className="layer-section-icon">⚠️</Text>
                <Text className="layer-section-title">官方预警</Text>
                <Text className="layer-section-count">{layerData.alerts.length}</Text>
              </View>
              {layerData.alerts.map((alert) => {
                const alertInfo = getAlertLevelInfo(alert.level)
                return (
                  <View key={alert.id} className="list-item card">
                    <View className="list-item-header">
                      <View className="list-item-badge" style={{ backgroundColor: alertInfo.color + '20', borderColor: alertInfo.color }}>
                        <Text className="list-item-badge-text" style={{ color: alertInfo.color }}>
                          {alertInfo.icon} {alertInfo.label}
                        </Text>
                      </View>
                      <Text className="list-item-source">{alert.source}</Text>
                    </View>
                    <Text className="list-item-title">{alert.title}</Text>
                    {alert.description && (
                      <Text className="list-item-desc">{alert.description}</Text>
                    )}
                    <View className="list-item-footer">
                      <Text className="list-item-area">{alert.area}</Text>
                      <Text className="list-item-time">{formatTime(alert.issuedAt)}</Text>
                    </View>
                  </View>
                )
              })}
            </View>
          )}

          {/* 平台风险 */}
          {enabledLayers.includes('risks') && layerData.risks.length > 0 && (
            <View className="layer-section">
              <View className="layer-section-header">
                <Text className="layer-section-icon">📊</Text>
                <Text className="layer-section-title">平台风险</Text>
                <Text className="layer-section-count">{layerData.risks.length}</Text>
              </View>
              {layerData.risks.map((risk) => {
                const band = RISK_BANDS[risk.level as keyof typeof RISK_BANDS]
                return (
                  <View key={risk.id} className="list-item card">
                    <View className="list-item-header">
                      <View className="list-item-badge" style={{ backgroundColor: band?.bgColor || '#f5f5f5', borderColor: band?.color || '#8c8c8c' }}>
                        <Text className="list-item-badge-text" style={{ color: band?.color || '#8c8c8c' }}>
                          {band?.icon || '?'} {band?.label || '未知'}
                        </Text>
                      </View>
                    </View>
                    <Text className="list-item-title">{risk.area}</Text>
                    <Text className="list-item-desc">平台风险等级</Text>
                  </View>
                )
              })}
            </View>
          )}

          {/* 积水报告 */}
          {enabledLayers.includes('reports') && layerData.reports.length > 0 && (
            <View className="layer-section">
              <View className="layer-section-header">
                <Text className="layer-section-icon">💧</Text>
                <Text className="layer-section-title">积水报告</Text>
                <Text className="layer-section-count">{layerData.reports.length}</Text>
              </View>
              {layerData.reports.map((rpt) => {
                const statusInfo = getReportStatusInfo(rpt.status)
                return (
                  <View key={rpt.id} className="list-item card">
                    <View className="list-item-header">
                      <Text className="list-item-title">{rpt.type || getReportTypeLabel(rpt.type)}</Text>
                      <View className="list-item-badge" style={{ backgroundColor: statusInfo.color + '20', borderColor: statusInfo.color }}>
                        <Text className="list-item-badge-text" style={{ color: statusInfo.color }}>
                          {statusInfo.icon} {statusInfo.label}
                        </Text>
                      </View>
                    </View>
                    {rpt.description && (
                      <Text className="list-item-desc">{rpt.description}</Text>
                    )}
                    <View className="list-item-footer">
                      <Text className="list-item-coord">
                        📍 {rpt.lat.toFixed(4)}, {rpt.lon.toFixed(4)}
                      </Text>
                      {rpt.reportedAt && (
                        <Text className="list-item-time">{formatTime(rpt.reportedAt)}</Text>
                      )}
                    </View>
                  </View>
                )
              })}
            </View>
          )}

          {/* 道路事件 */}
          {enabledLayers.includes('roadEvents') && layerData.roadEvents.length > 0 && (
            <View className="layer-section">
              <View className="layer-section-header">
                <Text className="layer-section-icon">🚧</Text>
                <Text className="layer-section-title">道路事件</Text>
                <Text className="layer-section-count">{layerData.roadEvents.length}</Text>
              </View>
              {layerData.roadEvents.map((event) => {
                const typeInfo = getRoadEventTypeInfo(event.type)
                return (
                  <View key={event.id} className="list-item card">
                    <View className="list-item-header">
                      <View className="list-item-badge" style={{ backgroundColor: typeInfo.color + '20', borderColor: typeInfo.color }}>
                        <Text className="list-item-badge-text" style={{ color: typeInfo.color }}>
                          {typeInfo.icon} {typeInfo.label}
                        </Text>
                      </View>
                    </View>
                    <Text className="list-item-desc">{event.description}</Text>
                  </View>
                )
              })}
            </View>
          )}

          {/* 避险场所 */}
          {enabledLayers.includes('shelters') && layerData.shelters.length > 0 && (
            <View className="layer-section">
              <View className="layer-section-header">
                <Text className="layer-section-icon">🏠</Text>
                <Text className="layer-section-title">避险场所</Text>
                <Text className="layer-section-count">{layerData.shelters.length}</Text>
              </View>
              {layerData.shelters.map((shelter) => {
                const status =
                  SHELTER_STATUS[shelter.status as keyof typeof SHELTER_STATUS] || SHELTER_STATUS.closed
                const capacityPercent =
                  shelter.capacity > 0
                    ? Math.round((shelter.currentCount / shelter.capacity) * 100)
                    : 0
                return (
                  <View key={shelter.id} className="list-item card">
                    <View className="list-item-header">
                      <Text className="list-item-title">{shelter.name}</Text>
                      <View className="list-item-badge" style={{ backgroundColor: status.color + '20', borderColor: status.color }}>
                        <Text className="list-item-badge-text" style={{ color: status.color }}>
                          {status.icon} {status.label}
                        </Text>
                      </View>
                    </View>
                    <Text className="list-item-desc">{shelter.address}</Text>
                    <View className="list-item-meta">
                      <Text className="list-item-meta-text">
                        容量：{shelter.currentCount}/{shelter.capacity}（{capacityPercent}%）
                      </Text>
                      {shelter.accessible && (
                        <Text className="list-item-meta-tag">♿ 无障碍</Text>
                      )}
                      {shelter.verified && (
                        <Text className="list-item-meta-tag">✅ 已核验</Text>
                      )}
                    </View>
                    <View className="list-item-footer">
                      <Text className="list-item-distance">
                        🚶 距离约 {shelter.distance < 1000 ? `${shelter.distance}米` : `${(shelter.distance / 1000).toFixed(1)}公里`}
                      </Text>
                      {shelter.contact && (
                        <Text className="list-item-contact">📞 {shelter.contact}</Text>
                      )}
                    </View>
                  </View>
                )
              })}
            </View>
          )}

          {/* 空状态 */}
          {enabledLayers.every(
            (key) => !layerData[key as keyof MapLayerData] || (layerData[key as keyof MapLayerData] as unknown[])?.length === 0,
          ) && (
            <EmptyState
              icon="📭"
              title="暂无筛选结果"
              description="当前筛选条件下没有数据，请尝试开启更多图层"
            />
          )}
        </View>
      </ScrollView>

      {/* 图例 */}
      <View className="legend">
        <Text className="legend-title">图例说明</Text>
        <View className="legend-items">
          {/* 平台风险等级 */}
          <View className="legend-group">
            <Text className="legend-group-title">平台风险等级</Text>
            {Object.values(RISK_BANDS).map((band) => (
              <View key={band.key} className="legend-item">
                <View
                  className="legend-color"
                  style={{ backgroundColor: band.color }}
                />
                <Text className="legend-text">
                  {band.icon} {band.label}
                </Text>
              </View>
            ))}
          </View>

          {/* 官方预警级别 */}
          <View className="legend-group">
            <Text className="legend-group-title">官方预警级别</Text>
            {[
              { color: '#1890ff', label: '🔵 蓝色预警' },
              { color: '#d48806', label: '🟡 黄色预警' },
              { color: '#d4380d', label: '🟠 橙色预警' },
              { color: '#cf1322', label: '🔴 红色预警' },
            ].map((item) => (
              <View key={item.label} className="legend-item">
                <View
                  className="legend-color"
                  style={{ backgroundColor: item.color }}
                />
                <Text className="legend-text">{item.label}</Text>
              </View>
            ))}
          </View>

          {/* 避难所状态 */}
          <View className="legend-group">
            <Text className="legend-group-title">避险场所状态</Text>
            {Object.values(SHELTER_STATUS).map((status) => (
              <View key={status.key} className="legend-item">
                <View
                  className="legend-color"
                  style={{ backgroundColor: status.color }}
                />
                <Text className="legend-text">
                  {status.icon} {status.label}
                </Text>
              </View>
            ))}
          </View>
        </View>
      </View>

      {/* 免责声明 */}
      <View className="disclaimer">
        <Text>平台风险等级为AI综合评估，仅供参考。请以现场标志及官方指令为准。</Text>
      </View>
    </View>
  )
}
