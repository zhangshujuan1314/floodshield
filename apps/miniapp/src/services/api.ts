import Taro from '@tarojs/taro'

declare const API_BASE_URL: string

// ===== 通用请求层 =====

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
  header?: Record<string, string>
  showToast?: boolean
}

interface ApiResponse<T = unknown> {
  requestId: string
  dataStatus: string
  timestamp: string
  data: T
}

function getBaseUrl(): string {
  return API_BASE_URL || 'http://localhost:3000'
}

function getAuthHeader(): Record<string, string> {
  const token = Taro.getStorageSync('auth_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T = unknown>(
  url: string,
  options: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const { method = 'GET', data, header = {}, showToast = true } = options

  try {
    const response = await Taro.request({
      url: `${getBaseUrl()}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
        ...header,
      },
    })

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return response.data as ApiResponse<T>
    }

    if (response.statusCode === 401) {
      Taro.removeStorageSync('auth_token')
      if (showToast) {
        Taro.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
      }
      throw new Error('未授权')
    }

    throw new Error((response.data as { message?: string })?.message || '请求失败')
  } catch (err) {
    if (showToast) {
      const message = err instanceof Error ? err.message : '网络异常，请稍后重试'
      Taro.showToast({ title: message, icon: 'none' })
    }
    throw err
  }
}

// ===== 前端数据类型（供页面和 mock 使用） =====

export interface RiskSummaryData {
  areaName: string
  riskBand: string
  riskLabel: string
  riskColor: string
  riskDescription: string
  officialAlerts: Array<{
    id: string
    level: string
    title: string
    content: string
    issuedAt: string
    source: string
  }>
  recommendedActions: string[]
  evidence: Array<{
    id: string
    icon: string
    title: string
    description: string
    source: string
    verified: boolean
    reportedAt: string
  }>
  freshness: string
  updatedAt: string
  source: string
}

export interface ShelterData {
  id: string
  name: string
  address: string
  lat: number
  lon: number
  status: string
  capacity: number
  currentCount: number
  accessible: boolean
  contact: string
  verified: boolean
  distance: number
  updatedAt: string
}

export interface RouteSegment {
  roadName: string
  riskLevel: string
  riskLabel: string
  riskColor: string
  distance: number
  duration: number
  evidence: string[]
  unknownRisk: boolean
}

export interface RouteData {
  id: string
  routeLabel: string
  origin: { name: string; lat: number; lon: number }
  destination: { name: string; lat: number; lon: number }
  segments: RouteSegment[]
  totalDistance: number
  totalTime: number
  overallRisk: string
  expiresAt: string
  source: string
}

export interface EvidenceItem {
  id: string
  icon: string
  title: string
  description: string
  source: string
  verified: boolean
  reportedAt: string
}

export interface MapLayerAlert {
  id: string
  level: string
  title: string
  area: string
  description: string
  source: string
  issuedAt: string
  polygons: Array<{ lat: number; lon: number }>
}

export interface MapLayerRisk {
  id: string
  level: string
  area: string
  polygons: Array<{ lat: number; lon: number }>
}

export interface MapLayerReport {
  id: string
  type: string
  lat: number
  lon: number
  status: string
  description: string
  reportedAt: string
}

export interface MapLayerRoadEvent {
  id: string
  type: string
  description: string
  polyline: Array<{ lat: number; lon: number }>
}

export interface MapLayerData {
  alerts: MapLayerAlert[]
  risks: MapLayerRisk[]
  reports: MapLayerReport[]
  roadEvents: MapLayerRoadEvent[]
  shelters: ShelterData[]
}

export interface HazardReportData {
  reportType: string
  severity: string
  description: string
  location?: { type: string; coordinates: [number, number] }
  photoUrl?: string
}

export interface ReportSubmitData {
  reportType: string
  severity: string
  description: string
  lat: number
  lon: number
  address?: string
  photoUrls?: string[]
}

export interface ReportHistoryItem {
  id: string
  eventType: string
  status: string
  createdAt: string
  address: string
}

// ===== 内部：后端响应类型 =====

interface BackendRiskEvidence {
  signal: string
  value: number
  subScore: number
  status: string
  message: string
}

interface BackendRiskSummary {
  risk: {
    areaId: string
    riskLevel: string
    riskScore: number
    confidence: number
    dataStatus: string
    evidence: BackendRiskEvidence[]
    updatedAt: string
  }
  activeAlerts: number
  nearbyShelters: number
  roadClosures: number
}

interface BackendAlert {
  id: string
  source: string
  alertType: string
  severity: string
  title: string
  description: string
  areaGeojson: { type: string; coordinates: unknown }
  effectiveAt: string
  expiresAt: string
  isActive: boolean
  createdAt: string
}

interface BackendShelter {
  id: string
  name: string
  address: string
  capacity: number
  currentOccupancy: number
  status: string
  contactPhone: string
  facilities: { medical: boolean; food: boolean; water: boolean; power: boolean; wifi: boolean }
  location: { type: string; coordinates: [number, number] }
  distanceM: number
}

interface BackendEvacuationRoute {
  id: string
  routeGeojson: { type: string; geometry: { type: string; coordinates: [number, number][] } }
  distanceM: number
  durationS: number
  safetyScore: number
  warnings: string[]
  isViable: boolean
  evidence: string[]
  dataTime: string
  expiresAt: string
  calculationTimeMs: number
}

interface BackendReport {
  id: string
  reportType: string
  severity: string
  description: string
  photoUrl: string | null
  location: { type: string; coordinates: [number, number]; precision: string }
  status: string
  createdAt: string
}

interface BackendMapLayer {
  id: string
  name: string
  type: string
  source: string
  description: string
  style: Record<string, unknown>
  updatedAt: string
}

// ===== 转换函数 =====

const RISK_LEVEL_MAP: Record<string, { band: string; label: string; color: string; description: string }> = {
  low: { band: 'normal', label: '正常', color: '#52c41a', description: '当前区域未检测到洪涝风险' },
  medium: { band: 'attention', label: '需关注', color: '#faad14', description: '存在潜在风险，请留意预警信息' },
  high: { band: 'high', label: '高风险', color: '#ff4d4f', description: '风险较高，建议提前规划避险路线' },
  extreme: { band: 'critical', label: '立即避险', color: '#cf1322', description: '危险区域，请立即撤离至安全地带' },
  unknown: { band: 'unknown', label: '暂无数据', color: '#8c8c8c', description: '当前数据不足，无法评估风险' },
}

const SEVERITY_TO_ALERT_LEVEL: Record<string, string> = {
  low: 'blue',
  medium: 'yellow',
  high: 'orange',
  extreme: 'red',
}

function transformRiskSummary(backend: BackendRiskSummary): RiskSummaryData {
  const risk = backend.risk
  const mapped = RISK_LEVEL_MAP[risk.riskLevel] || RISK_LEVEL_MAP.unknown

  const recommendedActions: string[] = []
  if (risk.riskLevel === 'medium' || risk.riskLevel === 'high' || risk.riskLevel === 'extreme') {
    recommendedActions.push('关注气象预警信息，做好防雨准备')
    recommendedActions.push('避免前往低洼易涝区域')
  }
  if (risk.riskLevel === 'high' || risk.riskLevel === 'extreme') {
    recommendedActions.push('提前规划避险路线')
    recommendedActions.push('车辆避免停放在地下车库')
  }
  if (risk.riskLevel === 'extreme') {
    recommendedActions.push('立即撤离至安全地带')
    recommendedActions.push('紧急情况请拨打110或119')
  }
  if (recommendedActions.length === 0) {
    recommendedActions.push('保持关注天气变化')
    recommendedActions.push('出行携带雨具，注意路面湿滑')
  }

  return {
    areaName: risk.areaId.replace('area-', '').replace(/-/g, '.'),
    riskBand: mapped.band,
    riskLabel: mapped.label,
    riskColor: mapped.color,
    riskDescription: mapped.description,
    officialAlerts: [],
    recommendedActions,
    evidence: risk.evidence.map((ev, idx) => ({
      id: `ev-${idx}`,
      icon: ev.status === 'ok' ? '✅' : ev.status === 'warning' ? '⚠️' : '❌',
      title: ev.signal,
      description: ev.message || `${ev.signal}: ${ev.value}`,
      source: '风险引擎',
      verified: true,
      reportedAt: risk.updatedAt,
    })),
    freshness: risk.dataStatus === 'normal' ? 'fresh' : 'partial',
    updatedAt: risk.updatedAt,
    source: '平台风险引擎',
  }
}

function transformAlert(backend: BackendAlert) {
  return {
    id: backend.id,
    level: SEVERITY_TO_ALERT_LEVEL[backend.severity] || 'blue',
    title: backend.title,
    content: backend.description,
    issuedAt: backend.effectiveAt,
    source: backend.source,
  }
}

function transformShelter(backend: BackendShelter): ShelterData {
  const coords = backend.location?.coordinates || [0, 0]
  let status = 'open'
  if (backend.status === 'nearly_full') status = 'limited'
  else if (backend.status === 'full') status = 'full'
  else if (backend.status === 'closed') status = 'closed'

  return {
    id: backend.id,
    name: backend.name,
    address: backend.address,
    lat: coords[1],
    lon: coords[0],
    status,
    capacity: backend.capacity,
    currentCount: backend.currentOccupancy,
    accessible: backend.facilities?.medical || false,
    contact: backend.contactPhone || '',
    verified: true,
    distance: backend.distanceM,
    updatedAt: new Date().toISOString(),
  }
}

function transformRoute(backend: BackendEvacuationRoute, label: string): RouteData {
  const coords = backend.routeGeojson?.geometry?.coordinates || []
  const distanceKm = backend.distanceM / 1000
  const totalTimeMin = Math.round(backend.durationS / 60)

  const riskMapped = backend.safetyScore >= 0.8
    ? RISK_LEVEL_MAP.low
    : backend.safetyScore >= 0.5
      ? RISK_LEVEL_MAP.medium
      : RISK_LEVEL_MAP.high

  const segments: RouteSegment[] = []
  if (coords.length >= 2) {
    const segCount = Math.min(3, coords.length - 1)
    const segSize = Math.floor(coords.length / segCount)
    for (let i = 0; i < segCount; i++) {
      const startIdx = i * segSize
      const endIdx = i === segCount - 1 ? coords.length - 1 : (i + 1) * segSize
      const segDist = Math.round(
        ((endIdx - startIdx) / (coords.length - 1)) * backend.distanceM,
      )
      const segTime = Math.round(
        ((endIdx - startIdx) / (coords.length - 1)) * totalTimeMin,
      )
      const isUnknown = backend.safetyScore < 0.3
      segments.push({
        roadName: `路段 ${i + 1}`,
        riskLevel: isUnknown ? 'unknown' : riskMapped.band,
        riskLabel: isUnknown ? '数据不足' : riskMapped.label,
        riskColor: isUnknown ? '#8c8c8c' : riskMapped.color,
        distance: segDist,
        duration: segTime,
        evidence: backend.evidence?.slice(0, 2) || [],
        unknownRisk: isUnknown,
      })
    }
  }

  return {
    id: backend.id,
    routeLabel: label,
    origin: { name: '起点', lat: coords[0]?.[1] || 0, lon: coords[0]?.[0] || 0 },
    destination: { name: '终点', lat: coords[coords.length - 1]?.[1] || 0, lon: coords[coords.length - 1]?.[0] || 0 },
    segments,
    totalDistance: Math.round(backend.distanceM),
    totalTime: totalTimeMin,
    overallRisk: riskMapped.band,
    expiresAt: backend.expiresAt,
    source: '平台AI规划',
  }
}

// ===== API 函数 =====

/** 风险概览 */
export async function getRiskSummary(lat: number, lon: number): Promise<ApiResponse<RiskSummaryData>> {
  const res = await request<BackendRiskSummary>(`/v1/nearby/summary?lat=${lat}&lon=${lon}`)
  return { ...res, data: transformRiskSummary(res.data) }
}

/** 官方预警列表 */
export async function getAlerts(): Promise<ApiResponse<Array<{
  id: string; level: string; title: string; content: string; issuedAt: string; source: string
}>>> {
  const res = await request<BackendAlert[]>('/v1/alerts?activeOnly=true')
  return { ...res, data: res.data.map(transformAlert) }
}

/** 地图图层 */
export async function getMapLayers(): Promise<ApiResponse<MapLayerData>> {
  const res = await request<BackendMapLayer[]>('/v1/map/layers')
  const layers: MapLayerData = {
    alerts: [],
    risks: [],
    reports: [],
    roadEvents: [],
    shelters: [],
  }
  for (const layer of res.data) {
    if (layer.source === 'official_alerts') {
      layers.alerts.push({
        id: layer.id,
        level: 'yellow',
        title: layer.name,
        area: layer.description || '',
        description: layer.description || '',
        source: '官方',
        issuedAt: layer.updatedAt,
        polygons: [],
      })
    } else if (layer.source === 'risk_engine') {
      layers.risks.push({
        id: layer.id,
        level: 'attention',
        area: layer.name,
        polygons: [],
      })
    } else if (layer.source === 'shelters') {
      // Shelters handled separately
    }
  }
  return { ...res, data: layers }
}

/** 证据列表（从风险摘要中提取，无独立端点） */
export async function getEvidenceList(lat: number, lon: number): Promise<ApiResponse<EvidenceItem[]>> {
  // 证据数据包含在风险摘要的 evidence 字段中
  const riskRes = await getRiskSummary(lat, lon)
  return {
    requestId: riskRes.requestId,
    dataStatus: riskRes.dataStatus,
    timestamp: riskRes.timestamp,
    data: riskRes.data.evidence,
  }
}

/** 避难所列表 */
export async function getShelters(lat: number, lon: number, radiusM = 5000): Promise<ApiResponse<ShelterData[]>> {
  const res = await request<BackendShelter[]>(`/v1/shelters/nearby?lat=${lat}&lon=${lon}&radiusM=${radiusM}`)
  return { ...res, data: res.data.map(transformShelter) }
}

/** 提交险情上报 */
export async function submitReport(data: ReportSubmitData): Promise<ApiResponse<{ id: string; status: string }>> {
  const body = {
    reportType: data.reportType,
    severity: data.severity,
    description: data.description,
    location: {
      type: 'Point',
      coordinates: [data.lon, data.lat],
    },
  }
  const res = await request<BackendReport>('/v1/hazard-reports', {
    method: 'POST',
    data: body as unknown as Record<string, unknown>,
  })
  return { ...res, data: { id: res.data.id, status: res.data.status } }
}

/** 获取上报详情 */
export async function getReport(reportId: string): Promise<ApiResponse<ReportHistoryItem>> {
  const res = await request<BackendReport>(`/v1/hazard-reports/${reportId}`)
  return {
    ...res,
    data: {
      id: res.data.id,
      eventType: res.data.reportType,
      status: res.data.status,
      createdAt: res.data.createdAt,
      address: res.data.description?.slice(0, 50) || '',
    },
  }
}

/** 获取上报历史（降级为本地缓存） */
export async function getReportHistory(): Promise<ApiResponse<ReportHistoryItem[]>> {
  try {
    const cached = Taro.getStorageSync('report_history') as ReportHistoryItem[] | undefined
    return {
      requestId: 'local',
      dataStatus: 'normal',
      timestamp: new Date().toISOString(),
      data: cached || [],
    }
  } catch {
    return {
      requestId: 'local',
      dataStatus: 'normal',
      timestamp: new Date().toISOString(),
      data: [],
    }
  }
}

/** 保存上报历史到本地 */
export function saveReportToHistory(report: ReportHistoryItem): void {
  try {
    const cached = (Taro.getStorageSync('report_history') as ReportHistoryItem[] | undefined) || []
    cached.unshift(report)
    Taro.setStorageSync('report_history', cached.slice(0, 50))
  } catch {
    // 静默失败
  }
}

/** 避险路线规划 */
export async function getRoutes(
  originLat: number,
  originLon: number,
  destLat: number,
  destLon: number,
): Promise<ApiResponse<RouteData[]>> {
  const body = {
    origin: { type: 'Point', coordinates: [originLon, originLat] },
    destination: { type: 'Point', coordinates: [destLon, destLat] },
    transportMode: 'walking',
    avoidHazards: true,
  }
  const res = await request<BackendEvacuationRoute>('/v1/routes/evacuation', {
    method: 'POST',
    data: body as unknown as Record<string, unknown>,
  })
  const route = transformRoute(res.data, '推荐路线')
  return { ...res, data: [route] }
}

/** 获取路线详情 */
export async function getRoute(routeId: string): Promise<ApiResponse<RouteData>> {
  const res = await request<BackendEvacuationRoute>(`/v1/routes/${routeId}`)
  return { ...res, data: transformRoute(res.data, '路线详情') }
}

/** 通知订阅 */
export async function subscribeNotifications(params: {
  channel: string
  recipient: string
  areas?: string[]
  alertTypes?: string[]
}): Promise<ApiResponse<{ id: string; isActive: boolean }>> {
  return request('/v1/notifications/subscriptions', {
    method: 'POST',
    data: params as unknown as Record<string, unknown>,
  })
}

/** 语音播报 */
export async function requestVoiceAnnouncement(params: {
  areaId: string
  message: string
  language?: string
  urgency?: string
}): Promise<ApiResponse<{ id: string; status: string; audioUrl: string | null }>> {
  return request('/v1/voice/announcement', {
    method: 'POST',
    data: params as unknown as Record<string, unknown>,
  })
}

/** 更新用户订阅区域 */
export async function updateSubscription(areas: string[]) {
  return subscribeNotifications({
    channel: 'push',
    recipient: 'miniapp_user',
    areas,
  })
}

/** 更新用户偏好 */
export async function updatePreferences(preferences: {
  fontSize?: string
  highContrast?: boolean
  voiceEnabled?: boolean
  reduceAnimation?: boolean
}) {
  Taro.setStorageSync('user_settings', preferences)
  return {
    requestId: 'local',
    dataStatus: 'normal',
    timestamp: new Date().toISOString(),
    data: preferences,
  }
}
