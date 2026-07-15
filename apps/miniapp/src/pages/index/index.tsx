import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect, useCallback } from 'react'
import { useLocation } from '../../hooks/useLocation'
import { getRiskSummary, getEvidenceList } from '../../services/api'
import { getMockRiskSummary, getMockEvidence } from '../../services/mock'
import type { RiskSummaryData, EvidenceItem } from '../../services/api'
import RiskBadge from '../../components/RiskBadge'
import AlertCard from '../../components/AlertCard'
import DataFreshness from '../../components/DataFreshness'
import VoiceButton from '../../components/VoiceButton'
import LoadingState from '../../components/LoadingState'
import ErrorState from '../../components/ErrorState'
import EmptyState from '../../components/EmptyState'
import { type RiskBandKey } from '../../utils/constants'
import './index.scss'

export default function IndexPage() {
  const location = useLocation()
  const [riskData, setRiskData] = useState<RiskSummaryData | null>(null)
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (!location.latitude || !location.longitude) return

    setLoading(true)
    setError(null)

    try {
      const [riskRes, evidenceRes] = await Promise.all([
        getRiskSummary(location.latitude, location.longitude),
        getEvidenceList(location.latitude, location.longitude),
      ])
      setRiskData(riskRes.data)
      setEvidence(evidenceRes.data)
    } catch {
      // 降级到模拟数据
      setRiskData(getMockRiskSummary())
      setEvidence(getMockEvidence())
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

  const goToReport = () => Taro.navigateTo({ url: '/pages/report/index' })
  const goToRoute = () => Taro.navigateTo({ url: '/pages/route/index' })
  const goToShelters = () => Taro.switchTab({ url: '/pages/shelters/index' })

  // 位置权限被拒 — 仍可手动选择区域查看风险
  // 核心公共功能不能因位置权限拒绝而阻断
  const [manualArea, setManualArea] = useState<string | null>(null)

  if (!location.loading && location.permissionDenied && !manualArea) {
    return (
      <View className="container">
        <View className="card" style={{ padding: '32rpx', textAlign: 'center' }}>
          <Text style={{ fontSize: '48rpx', marginBottom: '16rpx' }}>📍</Text>
          <Text style={{ fontSize: '32rpx', fontWeight: 'bold', marginBottom: '16rpx' }}>
            位置权限未开启
          </Text>
          <Text style={{ fontSize: '28rpx', color: '#666', marginBottom: '32rpx' }}>
            您可以手动选择区域查看风险信息，或开启位置权限获取自动定位。
          </Text>
          <View
            className="btn-primary"
            style={{ marginBottom: '16rpx', padding: '16rpx 32rpx', background: '#1890ff', color: '#fff', borderRadius: '8rpx' }}
            onClick={location.openSetting}
          >
            <Text style={{ color: '#fff' }}>开启位置权限</Text>
          </View>
          <View
            className="btn-secondary"
            style={{ padding: '16rpx 32rpx', border: '1rpx solid #d9d9d9', borderRadius: '8rpx' }}
            onClick={() => {
              setManualArea('demo_area_001')
              fetchData()
            }}
          >
            <Text>手动选择区域</Text>
          </View>
        </View>
      </View>
    )
  }

  // 加载中
  if (loading || location.loading) {
    return (
      <View className="container">
        <LoadingState text="正在获取附近风险信息..." />
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
  if (!riskData) {
    return (
      <View className="container">
        <EmptyState
          title="暂无风险数据"
          description="当前区域暂无风险信息，请稍后再试"
          actionText="刷新"
          onAction={fetchData}
        />
      </View>
    )
  }

  return (
    <ScrollView className="index-page" scrollY enableFlex>
      <View className="container">
        {/* 位置信息 */}
        <View className="location-bar">
          <Text className="location-icon">📍</Text>
          <Text className="location-text">
            {riskData.areaName || location.address || '定位中...'}
          </Text>
        </View>

        {/* 平台风险等级卡片 */}
        <View className="risk-card card">
          <Text className="risk-card-label">平台风险等级</Text>
          <View className="risk-card-main">
            <RiskBadge
              riskKey={riskData.riskBand as RiskBandKey}
              size="large"
              showDescription
            />
            <VoiceButton text={`${riskData.areaName}，当前风险等级：${riskData.riskLabel}。${riskData.riskDescription}`} />
          </View>
          <DataFreshness
            freshness={riskData.freshness as any}
            updatedAt={riskData.updatedAt}
            source={riskData.source}
          />
        </View>

        {/* 官方预警 */}
        {riskData.officialAlerts.length > 0 && (
          <View className="section">
            <Text className="section-title">官方预警</Text>
            {riskData.officialAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                id={alert.id}
                level={alert.level}
                title={alert.title}
                content={alert.content}
                issuedAt={alert.issuedAt}
                source={alert.source}
              />
            ))}
          </View>
        )}

        {/* 建议行动 */}
        {riskData.recommendedActions.length > 0 && (
          <View className="card">
            <Text className="section-title">建议行动</Text>
            {riskData.recommendedActions.map((action, idx) => (
              <View key={idx} className="action-item">
                <Text className="action-number">{idx + 1}</Text>
                <Text className="action-text">{action}</Text>
              </View>
            ))}
          </View>
        )}

        {/* 证据列表 */}
        {evidence.length > 0 && (
          <View className="section">
            <Text className="section-title">最新动态</Text>
            {evidence.map((item) => (
              <View key={item.id} className="evidence-item card">
                <View className="evidence-header">
                  <Text className="evidence-icon">{item.icon}</Text>
                  <Text className="evidence-title">{item.title}</Text>
                </View>
                <Text className="evidence-desc">{item.description}</Text>
                <View className="evidence-footer">
                  <Text className="evidence-source">
                    来源：{item.source}
                    {item.verified ? '（已核验）' : '（待核验）'}
                  </Text>
                  <Text className="evidence-time">{formatTime(item.reportedAt)}</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* 快捷操作 */}
        <View className="quick-actions">
          <View className="quick-action-btn" onClick={goToReport}>
            <Text className="quick-action-icon">📝</Text>
            <Text className="quick-action-text">上报险情</Text>
          </View>
          <View className="quick-action-btn" onClick={goToRoute}>
            <Text className="quick-action-icon">🗺️</Text>
            <Text className="quick-action-text">安全路线</Text>
          </View>
          <View className="quick-action-btn" onClick={goToShelters}>
            <Text className="quick-action-icon">🏠</Text>
            <Text className="quick-action-text">附近避险点</Text>
          </View>
        </View>

        {/* 免责声明 */}
        <View className="disclaimer">
          <Text>
            平台风险等级基于AI分析和多源数据综合评估，仅供参考。
            官方预警以气象、水利等部门发布为准。
            请以现场标志及官方指令为准，确保人身安全。
          </Text>
        </View>
      </View>
    </ScrollView>
  )
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
