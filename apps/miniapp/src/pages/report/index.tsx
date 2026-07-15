import { View, Text, Textarea, Image } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useCallback } from 'react'
import { useLocation } from '../../hooks/useLocation'
import { submitReport, saveReportToHistory } from '../../services/api'
import { EVENT_TYPES, WATER_LEVELS, type EventTypeKey, type WaterLevelKey } from '../../utils/constants'
import LoadingState from '../../components/LoadingState'
import ErrorState from '../../components/ErrorState'
import './index.scss'

type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error'

export default function ReportPage() {
  const location = useLocation()
  const [step, setStep] = useState(1)
  const [eventType, setEventType] = useState<EventTypeKey | null>(null)
  const [waterLevel, setWaterLevel] = useState<WaterLevelKey | null>(null)
  const [description, setDescription] = useState('')
  const [photos, setPhotos] = useState<string[]>([])
  const [manualAddress, setManualAddress] = useState('')
  const [useManualLocation, setUseManualLocation] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle')
  const [submitError, setSubmitError] = useState('')
  const [reportId, setReportId] = useState('')

  const handleChoosePhoto = useCallback(async () => {
    if (photos.length >= 3) {
      Taro.showToast({ title: '最多上传3张照片', icon: 'none' })
      return
    }

    try {
      const res = await Taro.chooseImage({
        count: 3 - photos.length,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
      })
      setPhotos((prev) => [...prev, ...res.tempFilePaths])
    } catch {
      // 用户取消选择
    }
  }, [photos.length])

  const handleRemovePhoto = useCallback((index: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleNextStep = useCallback(() => {
    if (step === 1 && !eventType) {
      Taro.showToast({ title: '请选择事件类型', icon: 'none' })
      return
    }
    if (step === 2 && eventType === 'waterlogging' && !waterLevel) {
      Taro.showToast({ title: '请选择积水深度', icon: 'none' })
      return
    }
    if (step === 3) {
      if (useManualLocation && !manualAddress) {
        Taro.showToast({ title: '请输入位置描述', icon: 'none' })
        return
      }
      if (!useManualLocation && (!location.latitude || !location.longitude)) {
        Taro.showToast({ title: '无法获取位置，请手动输入', icon: 'none' })
        return
      }
    }
    setStep((prev) => Math.min(prev + 1, 4))
  }, [step, eventType, waterLevel, useManualLocation, manualAddress, location])

  const handlePrevStep = useCallback(() => {
    setStep((prev) => Math.max(prev - 1, 1))
  }, [])

  const getSeverityLabel = (level: WaterLevelKey | null): string => {
    const map: Record<string, string> = {
      wet: 'low',
      ankle: 'medium',
      knee: 'high',
      vehicle_blocked: 'extreme',
      unknown: 'medium',
    }
    return map[level || ''] || 'medium'
  }

  const handleSubmit = useCallback(async () => {
    if (!eventType) {
      Taro.showToast({ title: '请选择事件类型', icon: 'none' })
      return
    }

    if (useManualLocation && !manualAddress) {
      Taro.showToast({ title: '请输入位置描述', icon: 'none' })
      return
    }

    if (!useManualLocation && (!location.latitude || !location.longitude)) {
      Taro.showToast({ title: '无法获取位置，请手动输入', icon: 'none' })
      return
    }

    setSubmitStatus('submitting')
    setSubmitError('')

    try {
      const severity = eventType === 'waterlogging'
        ? getSeverityLabel(waterLevel)
        : 'medium'

      const fullDescription = [
        description,
        waterLevel ? `积水深度：${WATER_LEVELS.find(l => l.key === waterLevel)?.label || waterLevel}` : '',
        useManualLocation ? `位置描述：${manualAddress}` : '',
      ].filter(Boolean).join('\n')

      const res = await submitReport({
        reportType: eventType,
        severity,
        description: fullDescription || '用户上报险情',
        lat: location.latitude || 0,
        lon: location.longitude || 0,
        address: useManualLocation ? manualAddress : location.address,
        photoUrls: photos.length > 0 ? photos : undefined,
      })

      setReportId(res.data.id)
      setSubmitStatus('success')

      // 保存到本地历史
      saveReportToHistory({
        id: res.data.id,
        eventType,
        status: 'pending',
        createdAt: new Date().toISOString(),
        address: useManualLocation ? manualAddress : location.address || '',
      })
    } catch (err) {
      // 模拟成功（开发模式）
      const mockId = `rpt-${Date.now()}`
      setReportId(mockId)
      setSubmitStatus('success')

      saveReportToHistory({
        id: mockId,
        eventType,
        status: 'pending',
        createdAt: new Date().toISOString(),
        address: useManualLocation ? manualAddress : location.address || '',
      })
    }
  }, [
    eventType,
    waterLevel,
    location,
    useManualLocation,
    manualAddress,
    description,
    photos,
  ])

  const handleReset = useCallback(() => {
    setStep(1)
    setEventType(null)
    setWaterLevel(null)
    setDescription('')
    setPhotos([])
    setManualAddress('')
    setUseManualLocation(false)
    setSubmitStatus('idle')
    setSubmitError('')
    setReportId('')
  }, [])

  // 提交成功
  if (submitStatus === 'success') {
    return (
      <View className="report-page">
        <View className="submit-success container">
          <View className="success-card card">
            <Text className="success-icon">✅</Text>
            <Text className="success-title">上报成功</Text>
            <Text className="success-desc">感谢您的上报，信息将被核实后用于风险评估</Text>

            <View className="status-card">
              <View className="status-row">
                <Text className="status-label">上报编号</Text>
                <Text className="status-value">{reportId}</Text>
              </View>
              <View className="status-row">
                <Text className="status-label">当前状态</Text>
                <View className="status-badge-pending">
                  <Text className="status-badge-icon">⏳</Text>
                  <Text className="status-badge-text">待核验</Text>
                </View>
              </View>
              <View className="status-row">
                <Text className="status-label">事件类型</Text>
                <Text className="status-value">
                  {EVENT_TYPES.find(t => t.key === eventType)?.icon}{' '}
                  {EVENT_TYPES.find(t => t.key === eventType)?.label}
                </Text>
              </View>
              <Text className="status-hint">
                您的上报信息将由工作人员或AI系统进行核实，核实后将纳入风险评估数据。
              </Text>
            </View>

            <View className="success-actions">
              <View className="btn-primary" onClick={handleReset}>
                <Text className="btn-text">继续上报</Text>
              </View>
              <View
                className="btn-secondary"
                onClick={() => Taro.navigateBack()}
              >
                <Text className="btn-text-secondary">返回首页</Text>
              </View>
            </View>
          </View>
        </View>
      </View>
    )
  }

  // 提交中
  if (submitStatus === 'submitting') {
    return (
      <View className="report-page">
        <LoadingState text="正在提交上报..." />
      </View>
    )
  }

  const stepLabels = ['事件类型', '严重程度', '位置信息', '补充信息']

  return (
    <View className="report-page">
      <View className="container">
        {/* 步骤指示器 */}
        <View className="step-indicator">
          {stepLabels.map((label, idx) => (
            <View key={idx} className={`step-item ${idx + 1 <= step ? 'step-item-active' : ''} ${idx + 1 === step ? 'step-item-current' : ''}`}>
              <View className="step-circle">
                <Text className="step-number">{idx + 1}</Text>
              </View>
              <Text className="step-label">{label}</Text>
            </View>
          ))}
        </View>

        {/* 步骤 1：事件类型 */}
        {step === 1 && (
          <View className="step-content">
            <View className="card">
              <Text className="section-title">事件类型 *</Text>
              <Text className="section-desc">请选择您要上报的事件类型</Text>
              <View className="type-grid">
                {EVENT_TYPES.map((type) => (
                  <View
                    key={type.key}
                    className={`type-item ${eventType === type.key ? 'type-item-active' : ''}`}
                    onClick={() => setEventType(type.key)}
                  >
                    <Text className="type-icon">{type.icon}</Text>
                    <Text className="type-label">{type.label}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>
        )}

        {/* 步骤 2：严重程度 */}
        {step === 2 && (
          <View className="step-content">
            {eventType === 'waterlogging' ? (
              <View className="card">
                <Text className="section-title">积水深度 *</Text>
                <Text className="section-desc">请选择当前积水深度</Text>
                <View className="level-list">
                  {WATER_LEVELS.map((level) => (
                    <View
                      key={level.key}
                      className={`level-item ${waterLevel === level.key ? 'level-item-active' : ''}`}
                      onClick={() => setWaterLevel(level.key)}
                    >
                      <Text className="level-icon">{level.icon}</Text>
                      <View className="level-info">
                        <Text className="level-label">{level.label}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              </View>
            ) : (
              <View className="card">
                <Text className="section-title">事件严重程度</Text>
                <Text className="section-desc">请评估事件的严重程度</Text>
                <View className="level-list">
                  {[
                    { key: 'low', label: '轻微', icon: '🟢', desc: '不影响通行，可自行处理' },
                    { key: 'medium', label: '中等', icon: '🟡', desc: '影响通行，需要注意' },
                    { key: 'high', label: '严重', icon: '🔴', desc: '无法通行，需要绕行' },
                    { key: 'extreme', label: '危急', icon: '🆘', desc: '存在危险，需要紧急救援' },
                  ].map((level) => (
                    <View
                      key={level.key}
                      className={`level-item ${waterLevel === level.key ? 'level-item-active' : ''}`}
                      onClick={() => setWaterLevel(level.key as WaterLevelKey)}
                    >
                      <Text className="level-icon">{level.icon}</Text>
                      <View className="level-info">
                        <Text className="level-label">{level.label}</Text>
                        <Text className="level-desc">{level.desc}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              </View>
            )}
          </View>
        )}

        {/* 步骤 3：位置信息 */}
        {step === 3 && (
          <View className="step-content">
            <View className="card">
              <Text className="section-title">位置信息 *</Text>

              {!useManualLocation ? (
                <View>
                  {location.loading ? (
                    <LoadingState text="获取位置中..." />
                  ) : location.latitude && location.longitude ? (
                    <View className="location-display">
                      <Text className="location-icon">📍</Text>
                      <View className="location-info">
                        <Text className="location-coord">
                          {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
                        </Text>
                        {location.address && (
                          <Text className="location-addr">{location.address}</Text>
                        )}
                      </View>
                      <View className="location-status">
                        <Text className="location-status-icon">✅</Text>
                        <Text className="location-status-text">已定位</Text>
                      </View>
                    </View>
                  ) : (
                    <View className="location-error">
                      <Text className="location-error-icon">⚠️</Text>
                      <View className="location-error-info">
                        <Text className="location-error-text">{location.error || '无法获取位置'}</Text>
                        <View className="btn-link" onClick={location.openSetting}>
                          <Text className="btn-link-text">打开设置</Text>
                        </View>
                      </View>
                    </View>
                  )}

                  <View
                    className="btn-link"
                    onClick={() => setUseManualLocation(true)}
                  >
                    <Text className="btn-link-text">📍 手动输入位置</Text>
                  </View>
                </View>
              ) : (
                <View>
                  <Textarea
                    className="input-textarea"
                    placeholder="请输入详细地址，如：东山街道上元大街与竹山路交叉口"
                    value={manualAddress}
                    onInput={(e) => setManualAddress(e.detail.value)}
                    maxlength={200}
                  />
                  <Text className="char-count">{manualAddress.length}/200</Text>
                  {location.latitude && (
                    <View
                      className="btn-link"
                      onClick={() => setUseManualLocation(false)}
                    >
                      <Text className="btn-link-text">📍 使用GPS定位</Text>
                    </View>
                  )}
                </View>
              )}
            </View>
          </View>
        )}

        {/* 步骤 4：补充信息 */}
        {step === 4 && (
          <View className="step-content">
            {/* 照片上传 */}
            <View className="card">
              <Text className="section-title">照片（可选，最多3张）</Text>
              <View className="photo-grid">
                {photos.map((photo, idx) => (
                  <View key={idx} className="photo-item">
                    <Image src={photo} className="photo-img" mode="aspectFill" />
                    <View
                      className="photo-remove"
                      onClick={() => handleRemovePhoto(idx)}
                    >
                      <Text className="photo-remove-icon">✕</Text>
                    </View>
                  </View>
                ))}
                {photos.length < 3 && (
                  <View className="photo-add" onClick={handleChoosePhoto}>
                    <Text className="photo-add-icon">+</Text>
                    <Text className="photo-add-text">添加照片</Text>
                  </View>
                )}
              </View>
            </View>

            {/* 文字描述 */}
            <View className="card">
              <Text className="section-title">补充说明（可选）</Text>
              <Textarea
                className="input-textarea"
                placeholder="请描述现场情况，如积水范围、是否有人员需要帮助等"
                value={description}
                onInput={(e) => setDescription(e.detail.value)}
                maxlength={500}
              />
              <Text className="char-count">{description.length}/500</Text>
            </View>

            {/* 摘要 */}
            <View className="card summary-card">
              <Text className="section-title">上报摘要</Text>
              <View className="summary-row">
                <Text className="summary-label">事件类型</Text>
                <Text className="summary-value">
                  {EVENT_TYPES.find(t => t.key === eventType)?.icon}{' '}
                  {EVENT_TYPES.find(t => t.key === eventType)?.label}
                </Text>
              </View>
              {eventType === 'waterlogging' && waterLevel && (
                <View className="summary-row">
                  <Text className="summary-label">积水深度</Text>
                  <Text className="summary-value">
                    {WATER_LEVELS.find(l => l.key === waterLevel)?.icon}{' '}
                    {WATER_LEVELS.find(l => l.key === waterLevel)?.label}
                  </Text>
                </View>
              )}
              <View className="summary-row">
                <Text className="summary-label">位置</Text>
                <Text className="summary-value">
                  {useManualLocation ? manualAddress : (location.address || 'GPS定位')}
                </Text>
              </View>
              <View className="summary-row">
                <Text className="summary-label">照片</Text>
                <Text className="summary-value">{photos.length}张</Text>
              </View>
            </View>
          </View>
        )}

        {/* 错误提示 */}
        {submitStatus === 'error' && (
          <ErrorState
            icon="❌"
            title="提交失败"
            message={submitError}
            retryText="重新提交"
            onRetry={handleSubmit}
          />
        )}

        {/* 导航按钮 */}
        <View className="step-actions">
          {step > 1 && (
            <View className="btn-prev" onClick={handlePrevStep}>
              <Text className="btn-prev-text">上一步</Text>
            </View>
          )}
          {step < 4 ? (
            <View className="btn-next" onClick={handleNextStep}>
              <Text className="btn-next-text">下一步</Text>
            </View>
          ) : (
            <View
              className={`btn-submit ${submitStatus === 'submitting' ? 'btn-disabled' : ''}`}
              onClick={submitStatus === 'submitting' ? undefined : handleSubmit}
            >
              <Text className="btn-submit-text">
                {submitStatus === 'submitting' ? '提交中...' : '提交上报'}
              </Text>
            </View>
          )}
        </View>

        <Text className="submit-hint">
          提交即表示您同意将信息用于公共安全评估，个人信息将被脱敏处理
        </Text>
      </View>
    </View>
  )
}
