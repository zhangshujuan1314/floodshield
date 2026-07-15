import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect, useCallback } from 'react'
import { useLocation } from '../../hooks/useLocation'
import { getShelters } from '../../services/api'
import { getMockShelters } from '../../services/mock'
import type { ShelterData } from '../../services/api'
import { SHELTER_STATUS, type ShelterStatusKey } from '../../utils/constants'
import LoadingState from '../../components/LoadingState'
import ErrorState from '../../components/ErrorState'
import EmptyState from '../../components/EmptyState'
import DataFreshness from '../../components/DataFreshness'
import './index.scss'

export default function SheltersPage() {
  const location = useLocation()
  const [shelters, setShelters] = useState<ShelterData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (!location.latitude || !location.longitude) return

    setLoading(true)
    setError(null)

    try {
      const res = await getShelters(location.latitude, location.longitude)
      setShelters(res.data)
    } catch {
      // 降级到模拟数据
      setShelters(getMockShelters())
    } finally {
      setLoading(false)
    }
  }, [location.latitude, location.longitude])

  useEffect(() => {
    if (location.latitude && location.longitude) {
      fetchData()
    } else if (!location.loading && location.error) {
      setLoading(false)
      setError(location.error)
    }
  }, [location, fetchData])

  const handleCall = (phone: string) => {
    if (!phone) return
    Taro.makePhoneCall({ phoneNumber: phone }).catch(() => {
      Taro.showToast({ title: '拨号失败', icon: 'none' })
    })
  }

  const handleNavigate = (shelter: ShelterData) => {
    Taro.openLocation({
      latitude: shelter.lat,
      longitude: shelter.lon,
      name: shelter.name,
      address: shelter.address,
    }).catch(() => {
      Taro.showToast({ title: '打开导航失败', icon: 'none' })
    })
  }

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  // 位置权限被拒
  if (!location.loading && location.permissionDenied) {
    return (
      <View className="container">
        <ErrorState
          icon="📍"
          title="需要位置权限"
          message={location.error || '需要位置权限才能查找附近避险点'}
          retryText="打开设置"
          onRetry={location.openSetting}
        />
      </View>
    )
  }

  // 加载中
  if (loading || location.loading) {
    return (
      <View className="container">
        <LoadingState text="查找附近避险点..." />
      </View>
    )
  }

  // 加载失败
  if (error) {
    return (
      <View className="container">
        <ErrorState message={error} onRetry={fetchData} />
      </View>
    )
  }

  // 无数据
  if (shelters.length === 0) {
    return (
      <View className="container">
        <EmptyState
          icon="🏠"
          title="暂无附近避险点"
          description="当前区域暂无登记在册的避险点，请联系当地社区或拨打110求助"
          actionText="刷新"
          onAction={fetchData}
        />
      </View>
    )
  }

  // 按距离排序
  const sortedShelters = [...shelters].sort((a, b) => a.distance - b.distance)

  return (
    <ScrollView className="shelters-page" scrollY enableFlex>
      <View className="container">
        <View className="page-header">
          <Text className="page-title">附近避险点</Text>
          <Text className="page-subtitle">
            共 {sortedShelters.length} 个避险点，按距离排序
          </Text>
        </View>

        {sortedShelters.map((shelter) => {
          const status =
            SHELTER_STATUS[shelter.status as ShelterStatusKey] ||
            SHELTER_STATUS.closed
          const capacityPercent =
            shelter.capacity > 0
              ? Math.round((shelter.currentCount / shelter.capacity) * 100)
              : 0
          const isExpanded = expandedId === shelter.id

          // 容量条颜色逻辑
          const barColor = capacityPercent >= 90
            ? SHELTER_STATUS.full.color
            : capacityPercent >= 70
              ? SHELTER_STATUS.limited.color
              : SHELTER_STATUS.open.color

          return (
            <View key={shelter.id} className="shelter-card card">
              {/* 头部：名称 + 状态 */}
              <View className="shelter-header" onClick={() => toggleExpand(shelter.id)}>
                <View className="shelter-name-area">
                  <Text className="shelter-name">{shelter.name}</Text>
                  <View className="shelter-badges">
                    {shelter.verified ? (
                      <View className="badge-verified">
                        <Text className="badge-icon">✅</Text>
                        <Text className="badge-text">已核验</Text>
                      </View>
                    ) : (
                      <View className="badge-unverified">
                        <Text className="badge-icon">⏳</Text>
                        <Text className="badge-text">待核验</Text>
                      </View>
                    )}
                  </View>
                </View>
                <View
                  className="status-pill"
                  style={{ backgroundColor: status.color + '20', borderColor: status.color }}
                >
                  <Text className="status-pill-text" style={{ color: status.color }}>
                    {status.icon} {status.label}
                  </Text>
                </View>
              </View>

              {/* 地址 */}
              <View className="shelter-row">
                <Text className="shelter-row-icon">📍</Text>
                <Text className="shelter-row-text">{shelter.address}</Text>
              </View>

              {/* 距离 */}
              <View className="shelter-row">
                <Text className="shelter-row-icon">🚶</Text>
                <Text className="shelter-row-text">
                  距离约 {shelter.distance < 1000 ? `${shelter.distance}米` : `${(shelter.distance / 1000).toFixed(1)}公里`}
                </Text>
              </View>

              {/* 容量 */}
              <View className="capacity-bar-container">
                <View className="capacity-info">
                  <Text className="capacity-label">容量</Text>
                  <Text className="capacity-numbers">
                    {shelter.currentCount}/{shelter.capacity}
                    <Text className="capacity-percent">（{capacityPercent}%）</Text>
                  </Text>
                </View>
                <View className="capacity-bar-bg">
                  <View
                    className="capacity-bar-fill"
                    style={{
                      width: `${Math.min(capacityPercent, 100)}%`,
                      backgroundColor: barColor,
                    }}
                  />
                </View>
              </View>

              {/* 无障碍 + 联系方式 */}
              <View className="shelter-features">
                {shelter.accessible && (
                  <View className="feature-tag">
                    <Text className="feature-tag-icon">♿</Text>
                    <Text className="feature-tag-text">无障碍设施</Text>
                  </View>
                )}
                {shelter.contact && (
                  <View className="feature-tag" onClick={() => handleCall(shelter.contact)}>
                    <Text className="feature-tag-icon">📞</Text>
                    <Text className="feature-tag-text">{shelter.contact}</Text>
                  </View>
                )}
              </View>

              {/* 展开详情 */}
              {isExpanded && (
                <View className="shelter-detail">
                  <View className="detail-divider" />
                  <View className="detail-row">
                    <Text className="detail-label">开放状态</Text>
                    <View className="detail-value" style={{ color: status.color }}>
                      <Text className="detail-icon">{status.icon}</Text>
                        <Text style={{ color: status.color }}>{status.label}</Text>
                    </View>
                  </View>
                  <View className="detail-row">
                    <Text className="detail-label">无障碍</Text>
                    <Text className="detail-value">
                      {shelter.accessible ? '♿ 支持' : '❌ 不支持'}
                    </Text>
                  </View>
                  <View className="detail-row">
                    <Text className="detail-label">核验状态</Text>
                    <Text className="detail-value">
                      {shelter.verified ? '✅ 已核验' : '⏳ 待核验'}
                    </Text>
                  </View>
                  <View className="detail-row">
                    <Text className="detail-label">更新时间</Text>
                    <Text className="detail-value">{formatTime(shelter.updatedAt)}</Text>
                  </View>
                </View>
              )}

              {/* 操作按钮 */}
              <View className="shelter-actions">
                <View
                  className="btn-navigate"
                  onClick={() => handleNavigate(shelter)}
                >
                  <Text className="btn-navigate-icon">🧭</Text>
                  <Text className="btn-navigate-text">导航前往</Text>
                </View>
                <View
                  className="btn-expand"
                  onClick={() => toggleExpand(shelter.id)}
                >
                  <Text className="btn-expand-text">
                    {isExpanded ? '收起详情' : '查看详情'}
                  </Text>
                </View>
              </View>

              {/* 数据更新时间 */}
              <DataFreshness freshness="fresh" updatedAt={shelter.updatedAt} />
            </View>
          )
        })}

        {/* 免责声明 */}
        <View className="disclaimer">
          <Text>
            避险点信息来源于相关部门登记数据，实际开放情况可能有变化。
            请以现场标志及官方指令为准。
          </Text>
        </View>
      </View>
    </ScrollView>
  )
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    const month = (d.getMonth() + 1).toString().padStart(2, '0')
    const day = d.getDate().toString().padStart(2, '0')
    const hour = d.getHours().toString().padStart(2, '0')
    const minute = d.getMinutes().toString().padStart(2, '0')
    return `${month}-${day} ${hour}:${minute}`
  } catch {
    return ''
  }
}
