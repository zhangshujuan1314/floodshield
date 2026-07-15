/** 风险等级 — 包含 unknown 状态，防止缺失数据被误判为安全 */
export const RISK_BANDS = {
  unknown: {
    key: 'unknown',
    label: '暂无数据',
    color: '#8c8c8c',
    bgColor: '#f5f5f5',
    icon: '?',
    description: '当前数据不足，无法评估风险，请参考官方预警',
  },
  normal: {
    key: 'normal',
    label: '正常',
    color: '#52c41a',
    bgColor: '#f6ffed',
    icon: '✓',
    description: '当前区域未检测到洪涝风险',
  },
  attention: {
    key: 'attention',
    label: '需关注',
    color: '#faad14',
    bgColor: '#fffbe6',
    icon: '!',
    description: '存在潜在风险，请留意预警信息',
  },
  high: {
    key: 'high',
    label: '高风险',
    color: '#ff4d4f',
    bgColor: '#fff2f0',
    icon: '⚠',
    description: '风险较高，建议提前规划避险路线',
  },
  critical: {
    key: 'critical',
    label: '立即避险',
    color: '#cf1322',
    bgColor: '#fff1f0',
    icon: '✕',
    description: '危险区域，请立即撤离至安全地带',
  },
} as const

export type RiskBandKey = keyof typeof RISK_BANDS

/** 事件类型 */
export const EVENT_TYPES = [
  { key: 'waterlogging', label: '积水', icon: '💧' },
  { key: 'road_blocked', label: '道路无法通行', icon: '🚫' },
  { key: 'basement_flood', label: '地下空间进水', icon: '🏢' },
  { key: 'manhole_damaged', label: '井盖破损', icon: '⚠️' },
  { key: 'person_trapped', label: '人员受困', icon: '🆘' },
  { key: 'other', label: '其他', icon: '📝' },
] as const

export type EventTypeKey = (typeof EVENT_TYPES)[number]['key']

/** 积水深度 */
export const WATER_LEVELS = [
  { key: 'wet', label: '路面湿滑', icon: '💧' },
  { key: 'ankle', label: '脚踝以下', icon: '💦' },
  { key: 'knee', label: '膝部以下', icon: '🌊' },
  { key: 'vehicle_blocked', label: '车辆无法通行', icon: '🚗' },
  { key: 'unknown', label: '无法判断', icon: '❓' },
] as const

export type WaterLevelKey = (typeof WATER_LEVELS)[number]['key']

/** 上报状态 */
export const REPORT_STATES = {
  pending: { key: 'pending', label: '待核验', color: '#faad14' },
  verified: { key: 'verified', label: '已核验', color: '#52c41a' },
  rejected: { key: 'rejected', label: '未通过', color: '#999999' },
} as const

export type ReportStateKey = keyof typeof REPORT_STATES

/** 避难所状态 */
export const SHELTER_STATUS = {
  open: { key: 'open', label: '开放', color: '#52c41a', icon: '✓' },
  limited: { key: 'limited', label: '容量紧张', color: '#faad14', icon: '!' },
  full: { key: 'full', label: '满员', color: '#ff4d4f', icon: '✕' },
  closed: { key: 'closed', label: '关闭', color: '#999999', icon: '-' },
} as const

export type ShelterStatusKey = keyof typeof SHELTER_STATUS

/** 数据新鲜度 */
export const FRESHNESS_LEVELS = {
  fresh: { key: 'fresh', label: '数据实时', color: '#52c41a' },
  partial: { key: 'partial', label: '部分过期', color: '#faad14' },
  stale: { key: 'stale', label: '数据过期', color: '#ff4d4f' },
  unknown: { key: 'unknown', label: '未知', color: '#999999' },
} as const

export type FreshnessKey = keyof typeof FRESHNESS_LEVELS
