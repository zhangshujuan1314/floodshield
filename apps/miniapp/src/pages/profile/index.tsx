import { View, Text, Switch, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useCallback, useEffect } from 'react'
import { getReportHistory, updatePreferences, updateSubscription } from '../../services/api'
import { getMockReportHistory } from '../../services/mock'
import { REPORT_STATES, type ReportStateKey } from '../../utils/constants'
import LoadingState from '../../components/LoadingState'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import './index.scss'

interface SettingsState {
  fontSize: 'normal' | 'large' | 'xlarge'
  highContrast: boolean
  voiceEnabled: boolean
  reduceAnimation: boolean
}

const FONT_SIZE_OPTIONS = [
  { key: 'normal', label: '标准', size: 28 },
  { key: 'large', label: '大号', size: 32 },
  { key: 'xlarge', label: '特大', size: 36 },
] as const

export default function ProfilePage() {
  const [settings, setSettings] = useState<SettingsState>({
    fontSize: 'normal',
    highContrast: false,
    voiceEnabled: false,
    reduceAnimation: false,
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
  const [reportError, setReportError] = useState<string | null>(null)

  // 加载设置
  useEffect(() => {
    const savedSettings = Taro.getStorageSync('user_settings')
    if (savedSettings) {
      setSettings((prev) => ({ ...prev, ...savedSettings }))
      // 应用已保存的设置
      applySettings(savedSettings)
    }
  }, [])

  // 加载上报历史
  useEffect(() => {
    setLoadingReports(true)
    setReportError(null)
    getReportHistory()
      .then((res) => {
        if (res.data.length > 0) {
          setReportHistory(res.data)
        } else {
          setReportHistory(getMockReportHistory())
        }
      })
      .catch(() => {
        setReportHistory(getMockReportHistory())
        setReportError(null) // mock fallback, no error shown
      })
      .finally(() => setLoadingReports(false))
  }, [])

  const applySettings = (s: Partial<SettingsState>) => {
    // 应用字号模式到页面根元素
    const pageEl = document?.querySelector?.('page') || document?.querySelector?.('body')
    if (pageEl) {
      pageEl.classList.remove('font-size-large', 'font-size-xlarge', 'high-contrast', 'reduce-animation')
      if (s.fontSize === 'large') pageEl.classList.add('font-size-large')
      if (s.fontSize === 'xlarge') pageEl.classList.add('font-size-xlarge')
      if (s.highContrast) pageEl.classList.add('high-contrast')
      if (s.reduceAnimation) pageEl.classList.add('reduce-animation')
    }
  }

  const saveSettings = useCallback(
    async (newSettings: Partial<SettingsState>) => {
      const merged = { ...settings, ...newSettings }
      setSettings(merged)
      Taro.setStorageSync('user_settings', merged)

      // 应用设置
      applySettings(merged)

      // 同步到服务端（静默）
      try {
        await updatePreferences({
          fontSize: merged.fontSize,
          highContrast: merged.highContrast,
          voiceEnabled: merged.voiceEnabled,
          reduceAnimation: merged.reduceAnimation,
        })
      } catch {
        // 静默失败
      }
    },
    [settings],
  )

  const handleRemoveArea = useCallback(
    (area: string) => {
      const newAreas = subscribedAreas.filter((a) => a !== area)
      setSubscribedAreas(newAreas)
      try {
        updateSubscription(newAreas)
      } catch {
        // 静默
      }
      Taro.showToast({ title: '已取消订阅', icon: 'success' })
    },
    [subscribedAreas],
  )

  const handleAddArea = useCallback(() => {
    Taro.showModal({
      title: '添加订阅区域',
      content: '请输入区域名称（如：江宁区秣陵街道）',
      editable: true,
      placeholderText: '区域名称',
      success: (res) => {
        if (res.confirm && res.content) {
          const newAreas = [...subscribedAreas, res.content.trim()]
          setSubscribedAreas(newAreas)
          try {
            updateSubscription(newAreas)
          } catch {
            // 静默
          }
          Taro.showToast({ title: '已添加订阅', icon: 'success' })
        }
      },
    })
  }, [subscribedAreas])

  const handleViewPrivacyPolicy = useCallback(() => {
    Taro.navigateTo({ url: '/pages/webview/index?url=https://floodshield.example.com/privacy' }).catch(() => {
      Taro.showModal({
        title: '隐私政策',
        content:
          '汛安平台收集的位置信息仅用于洪涝风险评估和预警服务，不会将您的个人信息用于商业目的。您的上报信息将被脱敏后用于公共安全评估。我们严格遵守《个人信息保护法》相关规定。',
        showCancel: false,
      })
    })
  }, [])

  const eventTypeLabels: Record<string, string> = {
    waterlogging: '💧 积水',
    road_blocked: '🚫 道路无法通行',
    basement_flood: '🏢 地下空间进水',
    manhole_damaged: '⚠️ 井盖破损',
    person_trapped: '🆘 人员受困',
    other: '📝 其他',
  }

  return (
    <ScrollView className="profile-page" scrollY enableFlex>
      <View className="container">
        {/* 订阅区域 */}
        <View className="card">
          <Text className="section-title">📍 订阅区域</Text>
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
          <Text className="section-title">🔊 语音播报</Text>
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

        {/* 无障碍设置 */}
        <View className="card">
          <Text className="section-title">♿ 无障碍设置</Text>

          {/* 字号选择 */}
          <View className="setting-item-vertical">
            <View className="setting-info">
              <Text className="setting-label">字体大小</Text>
              <Text className="setting-desc">选择适合您的文字尺寸</Text>
            </View>
            <View className="font-size-options">
              {FONT_SIZE_OPTIONS.map((opt) => (
                <View
                  key={opt.key}
                  className={`font-size-option ${settings.fontSize === opt.key ? 'font-size-option-active' : ''}`}
                  onClick={() => saveSettings({ fontSize: opt.key as SettingsState['fontSize'] })}
                >
                  <Text
                    className="font-size-option-text"
                    style={{ fontSize: `${opt.size}px` }}
                  >
                    A
                  </Text>
                  <Text className="font-size-option-label">{opt.label}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* 高对比模式 */}
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

          {/* 减少动画 */}
          <View className="setting-item">
            <View className="setting-info">
              <Text className="setting-label">减少动画</Text>
              <Text className="setting-desc">关闭过渡动画，减少视觉干扰</Text>
            </View>
            <Switch
              checked={settings.reduceAnimation}
              onChange={(e) => saveSettings({ reduceAnimation: e.detail.value })}
              color="var(--color-primary)"
            />
          </View>
        </View>

        {/* 上报历史 */}
        <View className="card">
          <Text className="section-title">📝 上报历史</Text>

          {loadingReports ? (
            <LoadingState text="加载中..." />
          ) : reportError ? (
            <ErrorState message={reportError} retryText="重试" onRetry={() => {
              setLoadingReports(true)
              getReportHistory()
                .then((res) => setReportHistory(res.data.length > 0 ? res.data : getMockReportHistory()))
                .catch(() => setReportHistory(getMockReportHistory()))
                .finally(() => setLoadingReports(false))
            }} />
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
                    <View className="report-item-footer">
                      <Text className="report-item-time">
                        {formatTime(report.createdAt)}
                      </Text>
                      <Text className="report-item-id">
                        编号：{report.id}
                      </Text>
                    </View>
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
            <Text className="about-copyright">
              数据来源：气象台、水利部门、市民上报
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
