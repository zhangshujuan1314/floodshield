import Taro from '@tarojs/taro'

declare const API_BASE_URL: string

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
  header?: Record<string, string>
  showToast?: boolean
}

interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

function getBaseUrl(): string {
  return API_BASE_URL || 'http://localhost:3000/api'
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

    throw new Error((response.data as ApiResponse)?.message || '请求失败')
  } catch (err) {
    if (showToast) {
      const message = err instanceof Error ? err.message : '网络异常，请稍后重试'
      Taro.showToast({ title: message, icon: 'none' })
    }
    throw err
  }
}

// ===== 风险概览 =====

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
  freshness: string
  updatedAt: string
  source: string
}

export function getRiskSummary(lat: number, lng: number) {
  return request<RiskSummaryData>('/risk/summary', {
    method: 'GET',
    data: { lat, lng },
  })
}

// ===== 避难所 =====

export interface ShelterData {
  id: string
  name: string
  address: string
  lat: number
  lng: number
  status: string
  capacity: number
  currentCount: number
  accessible: boolean
  contact: string
  verified: boolean
  distance: number
  updatedAt: string
}

export function getShelters(lat: number, lng: number, radius = 5000) {
  return request<ShelterData[]>('/shelters', {
    method: 'GET',
    data: { lat, lng, radius },
  })
}

// ===== 路线规划 =====

export interface RouteData {
  id: string
  origin: { name: string; lat: number; lng: number }
  destination: { name: string; lat: number; lng: number }
  segments: Array<{
    distance: number
    duration: number
    riskLabel: string
    riskColor: string
    evidence: string[]
    unknownRisk: boolean
  }>
  totalDistance: number
  totalDuration: number
  overallRisk: string
  expiresAt: string
  source: string
}

export function getRoutes(
  originLat: number,
  originLng: number,
  destLat: number,
  destLng: number,
) {
  return request<RouteData[]>('/routes', {
    method: 'POST',
    data: {
      origin: { lat: originLat, lng: originLng },
      destination: { lat: destLat, lng: destLng },
    },
  })
}

// ===== 上报 =====

export interface ReportSubmitData {
  eventType: string
  waterLevel?: string
  lat: number
  lng: number
  address?: string
  description?: string
  photoUrls?: string[]
}

export function submitReport(data: ReportSubmitData) {
  return request<{ id: string; status: string }>('/reports', {
    method: 'POST',
    data: data as unknown as Record<string, unknown>,
  })
}

export function getReportHistory() {
  return request<
    Array<{
      id: string
      eventType: string
      status: string
      createdAt: string
      address: string
    }>
  >('/reports/history')
}

// ===== 证据列表 =====

export interface EvidenceItem {
  id: string
  type: string
  title: string
  description: string
  source: string
  reportedAt: string
  verified: boolean
  icon: string
}

export function getEvidenceList(lat: number, lng: number, radius = 2000) {
  return request<EvidenceItem[]>('/evidence', {
    method: 'GET',
    data: { lat, lng, radius },
  })
}

// ===== 地图图层 =====

export interface MapLayerData {
  alerts: Array<{
    id: string
    level: string
    title: string
    area: string
    polygons: Array<{ lat: number; lng: number }>
  }>
  risks: Array<{
    id: string
    level: string
    area: string
    polygons: Array<{ lat: number; lng: number }>
  }>
  reports: Array<{
    id: string
    type: string
    lat: number
    lng: number
    status: string
  }>
  roadEvents: Array<{
    id: string
    type: string
    description: string
    polyline: Array<{ lat: number; lng: number }>
  }>
  shelters: ShelterData[]
}

export function getMapLayers(lat: number, lng: number, zoom: number) {
  return request<MapLayerData>('/map/layers', {
    method: 'GET',
    data: { lat, lng, zoom },
  })
}

// ===== 用户设置 =====

export function updateSubscription(areas: string[]) {
  return request('/user/subscriptions', {
    method: 'PUT',
    data: { areas: areas as unknown as Record<string, unknown> },
  })
}

export function updatePreferences(preferences: {
  fontSize?: string
  highContrast?: boolean
  voiceEnabled?: boolean
}) {
  return request('/user/preferences', {
    method: 'PUT',
    data: preferences as unknown as Record<string, unknown>,
  })
}
