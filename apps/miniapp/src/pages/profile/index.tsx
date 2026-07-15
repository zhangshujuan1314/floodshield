import { View, Text, Switch, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useCallback, useEffect } from 'react'
import { getReportHistory, updatePreferences } from '../../services/api'
import { REPORT_STATES, type ReportStateKey } from '../../utils/constants'
import LoadingState from '../../components/LoadingState'
import EmptyState from '../../components/EmptyState'
import './index.scss'

interface SettingsState {
  fontSize: 'normal' | 'large'
  highContrast: boolean
  voiceEnabled: boolean
}

export default function ProfilePage() {
  const [settings, setSettings] = useState<SettingsState>({
    fontSize: 'normal',
    highContrast: false,
    voiceEnabled: false,
  })
  const [subscribedAreas, setSubscribedAreas] = useState<string[]>(['江宁区东山街道'])
  const [reportHistory, setReportHistory] = useState<
    Array<{
      id: string
      eventType: string
      status: string
      createdAt: string
      address: string
    }>
  >([])
  const [loadingReports, setLoadingReports] = useState(true)

  // 加载设置
  useEffect(() => {
    const savedSettings = Taro.getStorageSync('user_settings')
    if (savedSettings) {
      setSettings((prev) => ({ ...prev, ...savedSettings }))
    }
  }, [])

  // 加载上报历史
  useEffect(() => {
    setLoadingReports(true)
    getReportHistory()
      .then((res) => setReportHistory(res.data))
      .catch(() => {
        // 使用模拟数据
        setReportHistory([
          {
            id: 'rpt-001',
            type: '积水',
            status: 'verified',
            createdAt: '2026-07-15T09:45:00+08:00',
            address: '东山路上元大街路口',
          },
          {
            id: 'rpt-002',
            type: '道路无法通行',
            status: 'pending',
            createdAt: '2026-07-15T08:30:00+08:00',
            address: '竹山路（上元大街-天元路段）',
          },
        ] as any)
      })
      .finally(() => setLoadingReports(false))
  }, [])

  const saveSettings = useCallback(
    async (newSettings: Partial<SettingsState>) => {
      const merged = { ...settings, ...newSettings }
      setSettings(merged)
      Taro.setStorageSync('user_settings', merged)

      // 同步到服务端
      try {
        await updatePreferences({
          fontSize: merged.fontSize,
          highContrast: merged.highContrast,
          voiceEnabled: merged.voiceEnabled,
        })
      } catch {
        // 静默失败
      }

      // 应用字号模式
      if (newSettings.fontSize) {
        // 通过页面 class 切换，在 app.scss 中定义
        Taro.showToast({
          title: newSettings.fontSize === 'large' ? '已切换大字号模式' : '已切换标准字号',
          icon: 'none',
        })
      }

      // 应用高对比模式
      if (newSettings.highContrast !== undefined) {
        Taro.showToast({
          title: newSettings.highContrast ? '已开启高对比模式' : '已关闭高对比模式',
          icon: 'none',
        })
      }
    },
    [settings],
  )

  const handleRemoveArea = useCallback(
    (area: string) => {
      const newAreas = subscribedAreas.filter((a) => a !== area)
      setSubscribedAreas(newAreas)
      Taro.showToast({ title: '已取消订阅', icon: 'success' })
    },
    [subscribedAreas],
  )

  const handleAddArea = useCallback(() => {
    Taro.showToast({ title: '添加订阅区域功能开发中', icon: 'none' })
  }, [])

  const handleViewPrivacyPolicy = useCallback(() => {
    Taro.navigateTo({ url: '/pages/webview/index?url=https://floodshield.example.com/privacy' }).catch(() => {
      Taro.showModal({
        title: '隐私政策',
        content:
          '汛安平台收集的位置信息仅用于洪涝风险评估和预警服务，不会将您的个人信息用于商业目的。您的上报信息将被脱敏后用于公共安全评估。',
        showCancel: false,
      })
    })
  }, [])

  const eventTypeLabels: Record<string, string> = {
    waterlogging: '积水',
    road_blocked: '道路无法通行',
    basement_flood: '地下空间进水',
    manhole_damaged: '井盖破损',
    person_trapped: '人员受困',
    other: '其他',
  }

  return (
    <ScrollView className="profile-page" scrollY enableFlex>
      <View className="container">
        {/* 订阅区域 */}
        <View className="card">
          <Text className="section-title">订阅区域</Text>
          <Text className="section-desc">接收以下区域的洪涝预警通知</Text>

          {subscribedAreas.length > 0 ? (
            <View className="area-list">
              {subscribedAreas.map((area) => (
                <View key={area} className="area-item">
                  <Text className="area-icon">📍</Text>
                  <Text className="area-name">{area}</Text>
                  <View className="area-remove" onClick={() => handleRemoveArea(area)}>
                    <Text className="area-remove-text">移除</Text>
                  </View>
                </View>
              ))}
            </View>
          ) : (
            <Text className="empty-hint">暂无订阅区域</Text>
          )}

          <View className="btn-add-area" onClick={handleAddArea}>
            <Text className="btn-add-area-icon">+</Text>
            <Text className="btn-add-area-text">添加订阅区域</Text>
          </View>
        </View>

        {/* 语音设置 */}
        <View className="card">
          <Text className="section-title">语音播报</Text>
          <View className="setting-item">
            <View className="setting-info">
              <Text className="setting-label">开启语音播报</Text>
              <Text className="setting-desc">风险信息和预警通知将通过语音播报</Text>
            </View>
            <Switch
              checked={settings.voiceEnabled}
              onChange={(e) => saveSettings({ voiceEnabled: e.detail.value })}
              color="var(--color-primary)"
            />
          </View>
        </View>

        {/* 显示设置 */}
        <View className="card">
          <Text className="section-title">显示设置</Text>

          <View className="setting-item">
            <View className="setting-info">
              <Text className="setting-label">大字号模式</Text>
              <Text className="setting-desc">增大文字尺寸，适合老年用户</Text>
            </View>
            <Switch
              checked={settings.fontSize === 'large'}
              onChange={(e) =>
                saveSettings({ fontSize: e.detail.value ? 'large' : 'normal' })
              }
              color="var(--color-primary)"
            />
          </View>

          <View className="setting-item">
            <View className="setting-info">
              <Text className="setting-label">高对比模式</Text>
              <Text className="setting-desc">增强色彩对比度，提升可读性</Text>
            </View>
            <Switch
              checked={settings.highContrast}
              onChange={(e) => saveSettings({ highContrast: e.detail.value })}
              color="var(--color-primary)"
            />
          </View>
        </View>

        {/* 上报历史 */}
        <View className="card">
          <Text className="section-title">上报历史</Text>

          {loadingReports ? (
            <LoadingState text="加载中..." />
          ) : reportHistory.length === 0 ? (
            <EmptyState
              icon="📝"
              title="暂无上报记录"
              description="您还没有上报过险情"
            />
          ) : (
            <View className="report-list">
              {reportHistory.map((report) => {
                const stateInfo =
                  REPORT_STATES[report.status as ReportStateKey] ||
                  REPORT_STATES.pending

                return (
                  <View key={report.id} className="report-item">
                    <View className="report-item-header">
                      <Text className="report-item-type">
                        {eventTypeLabels[report.eventType] || report.eventType}
                      </Text>
                      <View
                        className="report-status-badge"
                        style={{
                          backgroundColor: stateInfo.color + '20',
                          borderColor: stateInfo.color,
                        }}
                      >
                        <Text style={{ color: stateInfo.color, fontSize: 'var(--font-size-xs)', fontWeight: '600' }}>
                          {stateInfo.label}
                        </Text>
                      </View>
                    </View>
                    <Text className="report-item-addr">{report.address}</Text>
                    <Text className="report-item-time">
                      {formatTime(report.createdAt)}
                    </Text>
                  </View>
                )
              })}
            </View>
          )}
        </View>

        {/* 隐私政策 */}
        <View className="card" onClick={handleViewPrivacyPolicy}>
          <View className="menu-item">
            <Text className="menu-item-icon">🔒</Text>
            <Text className="menu-item-label">隐私政策</Text>
            <Text className="menu-item-arrow">{'>'}</Text>
          </View>
        </View>

        {/* 关于 */}
        <View className="card">
          <View className="about-section">
            <Text className="about-logo">🛡️</Text>
            <Text className="about-name">汛安 FloodShield</Text>
            <Text className="about-version">版本 0.1.0</Text>
            <Text className="about-desc">
              AI洪涝预警与避险平台
            </Text>
          </View>
        </View>

        <View className="spacer" />
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
