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
import './index.scss'

interface LayerToggle {
  key: string
  label: string
  enabled: boolean
}

export default function MapPage() {
  const location = useLocation()
  const [layerData, setLayerData] = useState<MapLayerData | null>(null)
  const [loading, setLoading] = useState(true)
  const [mapAvailable, setMapAvailable] = useState(true)
  const [layers, setLayers] = useState<LayerToggle[]>([
    { key: 'alerts', label: '官方预警', enabled: true },
    { key: 'risks', label: '平台风险', enabled: true },
    { key: 'reports', label: '用户上报', enabled: true },
    { key: 'roadEvents', label: '道路事件', enabled: true },
    { key: 'shelters', label: '避难所', enabled: true },
  ])

  const fetchData = useCallback(async () => {
    if (!location.latitude || !location.longitude) return

    setLoading(true)
    try {
      const res = await getMapLayers(location.latitude, location.longitude, 13)
      setLayerData(res.data)
    } catch {
      setLayerData(getMockMapLayers())
    } finally {
      setLoading(false)
    }
  }, [location.latitude, location.longitude])

  useEffect(() => {
    // 检查地图组件是否可用（需要配置 key）
    try {
      Taro.requirePlugin?.('map')
    } catch {
      setMapAvailable(false)
    }

    if (location.latitude && location.longitude) {
      fetchData()
    } else if (!location.loading) {
      setLoading(false)
    }
  }, [location, fetchData])

  const toggleLayer = (key: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.key === key ? { ...l, enabled: !l.enabled } : l)),
    )
  }

  const enabledLayers = layers.filter((l) => l.enabled).map((l) => l.key)

  if (loading || location.loading) {
    return (
      <View className="container">
        <LoadingState text="加载地图数据..." />
      </View>
    )
  }

  if (location.error && !location.latitude) {
    return (
      <View className="container">
        <ErrorState
          icon="📍"
          title="需要位置权限"
          message={location.error}
          retryText="打开设置"
          onRetry={location.openSetting}
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
          {/* <Map
            latitude={location.latitude}
            longitude={location.longitude}
            scale={13}
            showLocation
            className="map-view"
          /> */}
          <View className="map-placeholder">
            <Text className="map-placeholder-icon">🗺️</Text>
            <Text className="map-placeholder-text">地图加载中...</Text>
            <Text className="map-placeholder-hint">请配置地图 SDK Key 后启用</Text>
          </View>
        </View>
      ) : (
        <View className="map-unavailable">
          <Text className="map-unavailable-icon">🗺️</Text>
          <Text className="map-unavailable-text">地图暂不可用</Text>
          <Text className="map-unavailable-hint">请使用下方列表查看附近信息</Text>
        </View>
      )}

      {/* 图层切换 */}
      <View className="layer-toggles">
        <Text className="layer-toggles-title">图层</Text>
        <View className="layer-toggle-list">
          {layers.map((layer) => (
            <View key={layer.key} className="layer-toggle-item">
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
              { color: '#1890ff', label: '蓝色预警' },
              { color: '#d48806', label: '黄色预警' },
              { color: '#d4380d', label: '橙色预警' },
              { color: '#cf1322', label: '红色预警' },
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
            <Text className="legend-group-title">避难所状态</Text>
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

      {/* 列表视图（地图不可用时的 fallback） */}
      {(!mapAvailable || !location.latitude) && layerData && (
        <ScrollView className="list-fallback" scrollY>
          <Text className="list-fallback-title">附近信息</Text>

          {enabledLayers.includes('alerts') &&
            layerData.alerts.map((alert) => (
              <View key={alert.id} className="list-item card">
                <Text className="list-item-badge" style={{ color: '#d48806' }}>
                  ⚠ 官方预警
                </Text>
                <Text className="list-item-title">{alert.title}</Text>
                <Text className="list-item-sub">{alert.area}</Text>
              </View>
            ))}

          {enabledLayers.includes('risks') &&
            layerData.risks.map((risk) => (
              <View key={risk.id} className="list-item card">
                <Text
                  className="list-item-badge"
                  style={{ color: RISK_BANDS[risk.level as keyof typeof RISK_BANDS]?.color }}
                >
                  {RISK_BANDS[risk.level as keyof typeof RISK_BANDS]?.icon}{' '}
                  {RISK_BANDS[risk.level as keyof typeof RISK_BANDS]?.label}
                </Text>
                <Text className="list-item-title">{risk.area}</Text>
                <Text className="list-item-sub">平台风险等级</Text>
              </View>
            ))}

          {enabledLayers.includes('reports') &&
            layerData.reports.map((rpt) => (
              <View key={rpt.id} className="list-item card">
                <Text className="list-item-badge" style={{ color: 'var(--color-primary)' }}>
                  📍 用户上报
                </Text>
                <Text className="list-item-title">{rpt.type}</Text>
                <Text className="list-item-sub">
                  状态：{rpt.status === 'verified' ? '已核验' : '待核验'}
                </Text>
              </View>
            ))}

          {enabledLayers.includes('shelters') &&
            layerData.shelters.map((shelter) => {
              const status =
                SHELTER_STATUS[shelter.status as keyof typeof SHELTER_STATUS]
              return (
                <View key={shelter.id} className="list-item card">
                  <View className="list-item-header">
                    <Text className="list-item-title">{shelter.name}</Text>
                    <View
                      className="status-badge"
                      style={{
                        backgroundColor: status?.color,
                      }}
                    >
                      <Text className="status-badge-text">
                        {status?.icon} {status?.label}
                      </Text>
                    </View>
                  </View>
                  <Text className="list-item-sub">{shelter.address}</Text>
                  <Text className="list-item-detail">
                    容量：{shelter.currentCount}/{shelter.capacity}
                    {shelter.accessible ? ' | 无障碍' : ''}
                  </Text>
                </View>
              )
            })}
        </ScrollView>
      )}

      {/* 免责声明 */}
      <View className="disclaimer">
        <Text>平台风险等级为AI综合评估，仅供参考。请以现场标志及官方指令为准。</Text>
      </View>
    </View>
  )
}
