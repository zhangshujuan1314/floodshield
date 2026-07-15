import type { RiskSummaryData, ShelterData, RouteData, EvidenceItem, MapLayerData } from './api'

/** 风险概览模拟数据 */
export function getMockRiskSummary(): RiskSummaryData {
  return {
    areaName: '江宁区东山街道',
    riskBand: 'attention',
    riskLabel: '需关注',
    riskColor: '#faad14',
    riskDescription: '受持续降雨影响，局部地区可能出现积水，请注意出行安全',
    officialAlerts: [
      {
        id: 'alert-001',
        level: 'yellow',
        title: '暴雨黄色预警',
        content:
          '南京市气象台2026年07月15日10时发布暴雨黄色预警信号：预计未来6小时内，我市大部分地区将出现50毫米以上降水，请注意防范。',
        issuedAt: '2026-07-15T10:00:00+08:00',
        source: '南京市气象台',
      },
    ],
    recommendedActions: [
      '关注气象预警信息，做好防雨准备',
      '避免前往低洼易涝区域',
      '出行携带雨具，注意路面湿滑',
      '车辆避免停放在地下车库',
    ],
    freshness: 'fresh',
    updatedAt: '2026-07-15T10:30:00+08:00',
    source: '南京市防汛办 + 气象台 + 平台AI分析',
  }
}

/** 避难所模拟数据 */
export function getMockShelters(): ShelterData[] {
  return [
    {
      id: 'shelter-001',
      name: '东山街道应急避难所',
      address: '江宁区东山街道上元大街168号',
      lat: 31.9534,
      lng: 118.8398,
      status: 'open',
      capacity: 500,
      currentCount: 120,
      accessible: true,
      contact: '025-5218xxxx',
      verified: true,
      distance: 800,
      updatedAt: '2026-07-15T09:00:00+08:00',
    },
    {
      id: 'shelter-002',
      name: '江宁体育中心',
      address: '江宁区科学园路1号',
      lat: 31.9389,
      lng: 118.8456,
      status: 'limited',
      capacity: 2000,
      currentCount: 1800,
      accessible: true,
      contact: '025-5216xxxx',
      verified: true,
      distance: 2100,
      updatedAt: '2026-07-15T09:30:00+08:00',
    },
    {
      id: 'shelter-003',
      name: '竹山中学临时安置点',
      address: '江宁区竹山路58号',
      lat: 31.9412,
      lng: 118.8301,
      status: 'open',
      capacity: 300,
      currentCount: 45,
      accessible: false,
      contact: '025-5219xxxx',
      verified: false,
      distance: 1500,
      updatedAt: '2026-07-15T08:00:00+08:00',
    },
    {
      id: 'shelter-004',
      name: '百家湖社区避难点',
      address: '江宁区百家湖大街22号',
      lat: 31.9287,
      lng: 118.8523,
      status: 'full',
      capacity: 200,
      currentCount: 200,
      accessible: true,
      contact: '025-5217xxxx',
      verified: true,
      distance: 3200,
      updatedAt: '2026-07-15T09:15:00+08:00',
    },
  ]
}

/** 路线模拟数据 */
export function getMockRoutes(): RouteData[] {
  return [
    {
      id: 'route-001',
      origin: { name: '当前位置', lat: 31.95, lng: 118.84 },
      destination: { name: '东山街道应急避难所', lat: 31.9534, lng: 118.8398 },
      segments: [
        {
          distance: 400,
          duration: 5,
          riskLabel: '正常',
          riskColor: '#52c41a',
          evidence: ['路面干燥，无积水报告'],
          unknownRisk: false,
        },
        {
          distance: 400,
          duration: 6,
          riskLabel: '需关注',
          riskColor: '#faad14',
          evidence: [
            '30分钟前有人报告轻微积水',
            '气象台发布暴雨黄色预警',
          ],
          unknownRisk: false,
        },
      ],
      totalDistance: 800,
      totalDuration: 11,
      overallRisk: 'attention',
      expiresAt: '2026-07-15T11:00:00+08:00',
      source: '平台AI规划 + 用户上报',
    },
    {
      id: 'route-002',
      origin: { name: '当前位置', lat: 31.95, lng: 118.84 },
      destination: { name: '东山街道应急避难所', lat: 31.9534, lng: 118.8398 },
      segments: [
        {
          distance: 600,
          duration: 8,
          riskLabel: '正常',
          riskColor: '#52c41a',
          evidence: ['主干道通行正常'],
          unknownRisk: false,
        },
        {
          distance: 500,
          duration: 7,
          riskLabel: '正常',
          riskColor: '#52c41a',
          evidence: ['无异常报告'],
          unknownRisk: false,
        },
      ],
      totalDistance: 1100,
      totalDuration: 15,
      overallRisk: 'normal',
      expiresAt: '2026-07-15T11:00:00+08:00',
      source: '平台AI规划',
    },
  ]
}

/** 证据列表模拟数据 */
export function getMockEvidence(): EvidenceItem[] {
  return [
    {
      id: 'ev-001',
      type: 'user_report',
      title: '市民上报：东山路上元大街路口积水',
      description: '路面湿滑，脚踝以下积水，行人可通行',
      source: '市民上报',
      reportedAt: '2026-07-15T09:45:00+08:00',
      verified: true,
      icon: '📍',
    },
    {
      id: 'ev-002',
      type: 'road_closure',
      title: '交通管制：竹山路部分路段封闭',
      description: '因积水施工，竹山路（上元大街-天元路段）临时封闭',
      source: '交警部门',
      reportedAt: '2026-07-15T08:30:00+08:00',
      verified: true,
      icon: '🚧',
    },
    {
      id: 'ev-003',
      type: 'user_report',
      title: '市民上报：地下车库进水',
      description: '某小区B1层有少量进水，物业已设置警示',
      source: '市民上报',
      reportedAt: '2026-07-15T09:20:00+08:00',
      verified: false,
      icon: '🏢',
    },
  ]
}

/** 地图图层模拟数据 */
export function getMockMapLayers(): MapLayerData {
  return {
    alerts: [
      {
        id: 'alert-map-001',
        level: 'yellow',
        title: '暴雨黄色预警',
        area: '南京市',
        polygons: [
          { lat: 32.06, lng: 118.78 },
          { lat: 32.06, lng: 118.92 },
          { lat: 31.9, lng: 118.92 },
          { lat: 31.9, lng: 118.78 },
        ],
      },
    ],
    risks: [
      {
        id: 'risk-map-001',
        level: 'attention',
        area: '东山街道局部',
        polygons: [
          { lat: 31.955, lng: 118.835 },
          { lat: 31.955, lng: 118.845 },
          { lat: 31.945, lng: 118.845 },
          { lat: 31.945, lng: 118.835 },
        ],
      },
    ],
    reports: [
      { id: 'rpt-001', type: 'waterlogging', lat: 31.952, lng: 118.841, status: 'verified' },
      { id: 'rpt-002', type: 'road_blocked', lat: 31.948, lng: 118.837, status: 'verified' },
    ],
    roadEvents: [
      {
        id: 'road-001',
        type: 'closure',
        description: '竹山路临时封闭',
        polyline: [
          { lat: 31.948, lng: 118.833 },
          { lat: 31.941, lng: 118.833 },
        ],
      },
    ],
    shelters: getMockShelters(),
  }
}
