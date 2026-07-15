import { View, Text, Textarea, Image } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useCallback } from 'react'
import { useLocation } from '../../hooks/useLocation'
import { submitReport } from '../../services/api'
import { EVENT_TYPES, WATER_LEVELS, type EventTypeKey, type WaterLevelKey } from '../../utils/constants'
import LoadingState from '../../components/LoadingState'
import './index.scss'

type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error'

export default function ReportPage() {
  const location = useLocation()
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

  const handleSubmit = useCallback(async () => {
    // 校验
    if (!eventType) {
      Taro.showToast({ title: '请选择事件类型', icon: 'none' })
      return
    }

    if (eventType === 'waterlogging' && !waterLevel) {
      Taro.showToast({ title: '请选择积水深度', icon: 'none' })
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
      const res = await submitReport({
        eventType,
        waterLevel: waterLevel || undefined,
        lat: location.latitude || 0,
        lng: location.longitude || 0,
        address: useManualLocation ? manualAddress : location.address,
        description: description || undefined,
        photoUrls: photos.length > 0 ? photos : undefined,
      })
      setReportId(res.data.id)
      setSubmitStatus('success')
    } catch (err) {
      setSubmitStatus('error')
      setSubmitError(err instanceof Error ? err.message : '提交失败，请稍后重试')
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
        <View className="submit-success">
          <Text className="success-icon">✅</Text>
          <Text className="success-title">上报成功</Text>
          <Text className="success-desc">感谢您的上报，信息将被核实后用于风险评估</Text>

          <View className="status-card card">
            <View className="status-row">
              <Text className="status-label">上报编号</Text>
              <Text className="status-value">{reportId}</Text>
            </View>
            <View className="status-row">
              <Text className="status-label">当前状态</Text>
              <View className="status-badge-pending">
                <Text className="status-badge-text">待核验</Text>
              </View>
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
    )
  }

  return (
    <View className="report-page">
      <View className="container">
        {/* 事件类型选择 */}
        <View className="card">
          <Text className="section-title">事件类型 *</Text>
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

        {/* 积水深度（仅积水类型显示） */}
        {eventType === 'waterlogging' && (
          <View className="card">
            <Text className="section-title">积水深度 *</Text>
            <View className="level-list">
              {WATER_LEVELS.map((level) => (
                <View
                  key={level.key}
                  className={`level-item ${waterLevel === level.key ? 'level-item-active' : ''}`}
                  onClick={() => setWaterLevel(level.key)}
                >
                  <Text className="level-icon">{level.icon}</Text>
                  <Text className="level-label">{level.label}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* 位置信息 */}
        <View className="card">
          <Text className="section-title">位置信息</Text>

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
                </View>
              ) : (
                <View className="location-error">
                  <Text className="location-error-text">{location.error || '无法获取位置'}</Text>
                  <View className="btn-link" onClick={location.openSetting}>
                    <Text className="btn-link-text">打开设置</Text>
                  </View>
                </View>
              )}

              <View
                className="btn-link"
                onClick={() => setUseManualLocation(true)}
              >
                <Text className="btn-link-text">手动输入位置</Text>
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
              {location.latitude && (
                <View
                  className="btn-link"
                  onClick={() => setUseManualLocation(false)}
                >
                  <Text className="btn-link-text">使用GPS定位</Text>
                </View>
              )}
            </View>
          )}
        </View>

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

        {/* 提交按钮 */}
        <View className="submit-area">
          {submitStatus === 'error' && (
            <Text className="submit-error">{submitError}</Text>
          )}
          <View
            className={`btn-submit ${submitStatus === 'submitting' ? 'btn-disabled' : ''}`}
            onClick={submitStatus === 'submitting' ? undefined : handleSubmit}
          >
            <Text className="btn-submit-text">
              {submitStatus === 'submitting' ? '提交中...' : '提交上报'}
            </Text>
          </View>
          <Text className="submit-hint">
            提交即表示您同意将信息用于公共安全评估，个人信息将被脱敏处理
          </Text>
        </View>
      </View>
    </View>
  )
}
