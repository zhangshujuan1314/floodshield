import type {
  RiskSummaryData,
  ShelterData,
  RouteData,
  EvidenceItem,
  MapLayerData,
  ReportHistoryItem,
} from './api'

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
      {
        id: 'alert-002',
        level: 'blue',
        title: '洪水蓝色预警',
        content:
          '省水文水资源勘测局2026年07月15日08时发布秦淮河洪水蓝色预警：受上游来水影响，预计秦淮河东山站水位将超警戒水位0.3米。',
        issuedAt: '2026-07-15T08:00:00+08:00',
        source: '省水文水资源勘测局',
      },
    ],
    recommendedActions: [
      '关注气象预警信息，做好防雨准备',
      '避免前往低洼易涝区域',
      '出行携带雨具，注意路面湿滑',
      '车辆避免停放在地下车库',
    ],
    evidence: [
      {
        id: 'ev-mock-001',
        icon: '📍',
        title: '市民上报：东山路上元大街路口积水',
        description: '路面湿滑，脚踝以下积水，行人可通行',
        source: '市民上报',
        verified: true,
        reportedAt: '2026-07-15T09:45:00+08:00',
      },
      {
        id: 'ev-mock-002',
        icon: '🚧',
        title: '交通管制：竹山路部分路段封闭',
        description: '因积水施工，竹山路（上元大街-天元路段）临时封闭',
        source: '交警部门',
        verified: true,
        reportedAt: '2026-07-15T08:30:00+08:00',
      },
      {
        id: 'ev-mock-003',
        icon: '🏢',
        title: '市民上报：地下车库进水',
        description: '某小区B1层有少量进水，物业已设置警示',
        source: '市民上报',
        verified: false,
        reportedAt: '2026-07-15T09:20:00+08:00',
      },
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
      lon: 118.8398,
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
      lon: 118.8456,
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
      lon: 118.8301,
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
      lon: 118.8523,
      status: 'full',
      capacity: 200,
      currentCount: 200,
      accessible: true,
      contact: '025-5217xxxx',
      verified: true,
      distance: 3200,
      updatedAt: '2026-07-15T09:15:00+08:00',
    },
    {
      id: 'shelter-005',
      name: '胜太路社区服务中心',
      address: '江宁区胜太路36号',
      lat: 31.9456,
      lon: 118.8512,
      status: 'closed',
      capacity: 150,
      currentCount: 0,
      accessible: true,
      contact: '025-5220xxxx',
      verified: true,
      distance: 4500,
      updatedAt: '2026-07-14T18:00:00+08:00',
    },
  ]
}

/** 路线模拟数据 */
export function getMockRoutes(): RouteData[] {
  return [
    {
      id: 'route-001',
      routeLabel: '推荐路线',
      origin: { name: '当前位置', lat: 31.95, lon: 118.84 },
      destination: { name: '东山街道应急避难所', lat: 31.9534, lon: 118.8398 },
      segments: [
        {
          roadName: '上元大街',
          riskLevel: 'normal',
          riskLabel: '正常',
          riskColor: '#52c41a',
          distance: 400,
          duration: 5,
          evidence: ['路面干燥，无积水报告'],
          unknownRisk: false,
        },
        {
          roadName: '东山南路',
          riskLevel: 'attention',
          riskLabel: '需关注',
          riskColor: '#faad14',
          distance: 400,
          duration: 6,
          evidence: [
            '30分钟前有人报告轻微积水',
            '气象台发布暴雨黄色预警',
          ],
          unknownRisk: false,
        },
      ],
      totalDistance: 800,
      totalTime: 11,
      overallRisk: 'attention',
      expiresAt: '2026-07-15T11:00:00+08:00',
      source: '平台AI规划 + 用户上报',
    },
    {
      id: 'route-002',
      routeLabel: '备选路线',
      origin: { name: '当前位置', lat: 31.95, lon: 118.84 },
      destination: { name: '东山街道应急避难所', lat: 31.9534, lon: 118.8398 },
      segments: [
        {
          roadName: '天元路',
          riskLevel: 'normal',
          riskLabel: '正常',
          riskColor: '#52c41a',
          distance: 600,
          duration: 8,
          evidence: ['主干道通行正常'],
          unknownRisk: false,
        },
        {
          roadName: '竹山路（绕行段）',
          riskLevel: 'normal',
          riskLabel: '正常',
          riskColor: '#52c41a',
          distance: 500,
          duration: 7,
          evidence: ['无异常报告'],
          unknownRisk: false,
        },
      ],
      totalDistance: 1100,
      totalTime: 15,
      overallRisk: 'normal',
      expiresAt: '2026-07-15T11:00:00+08:00',
      source: '平台AI规划',
    },
    {
      id: 'route-003',
      routeLabel: '高风险路线',
      origin: { name: '当前位置', lat: 31.95, lon: 118.84 },
      destination: { name: '东山街道应急避难所', lat: 31.9534, lon: 118.8398 },
      segments: [
        {
          roadName: '竹山路（封闭段附近）',
          riskLevel: 'high',
          riskLabel: '高风险',
          riskColor: '#ff4d4f',
          distance: 300,
          duration: 15,
          evidence: [
            '该路段积水较深，车辆无法通行',
            '有市民报告膝部深度积水',
          ],
          unknownRisk: false,
        },
        {
          roadName: '小巷绕行',
          riskLevel: 'unknown',
          riskLabel: '数据不足',
          riskColor: '#8c8c8c',
          distance: 500,
          duration: 10,
          evidence: [],
          unknownRisk: true,
        },
      ],
      totalDistance: 800,
      totalTime: 25,
      overallRisk: 'high',
      expiresAt: '2026-07-15T11:00:00+08:00',
      source: '平台AI规划（低置信度）',
    },
  ]
}

/** 证据列表模拟数据 */
export function getMockEvidence(): EvidenceItem[] {
  return [
    {
      id: 'ev-001',
      icon: '📍',
      title: '市民上报：东山路上元大街路口积水',
      description: '路面湿滑，脚踝以下积水，行人可通行',
      source: '市民上报',
      reportedAt: '2026-07-15T09:45:00+08:00',
      verified: true,
    },
    {
      id: 'ev-002',
      icon: '🚧',
      title: '交通管制：竹山路部分路段封闭',
      description: '因积水施工，竹山路（上元大街-天元路段）临时封闭',
      source: '交警部门',
      reportedAt: '2026-07-15T08:30:00+08:00',
      verified: true,
    },
    {
      id: 'ev-003',
      icon: '🏢',
      title: '市民上报：地下车库进水',
      description: '某小区B1层有少量进水，物业已设置警示',
      source: '市民上报',
      reportedAt: '2026-07-15T09:20:00+08:00',
      verified: false,
    },
    {
      id: 'ev-004',
      icon: '🌧️',
      title: '气象台：未来3小时强降水持续',
      description: '预计未来3小时内仍将有30-50毫米降水，伴有雷电大风',
      source: '南京市气象台',
      reportedAt: '2026-07-15T10:15:00+08:00',
      verified: true,
    },
    {
      id: 'ev-005',
      icon: '🚗',
      title: '市政排水：全力抢排中',
      description: '东山片区已启动15台移动泵车，正在全力抢排积水',
      source: '市政排水公司',
      reportedAt: '2026-07-15T09:00:00+08:00',
      verified: true,
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
        description: '预计未来6小时内降水50毫米以上',
        source: '南京市气象台',
        issuedAt: '2026-07-15T10:00:00+08:00',
        polygons: [
          { lat: 32.06, lon: 118.78 },
          { lat: 32.06, lon: 118.92 },
          { lat: 31.9, lon: 118.92 },
          { lat: 31.9, lon: 118.78 },
        ],
      },
      {
        id: 'alert-map-002',
        level: 'blue',
        title: '洪水蓝色预警',
        area: '秦淮河流域',
        description: '秦淮河东山站水位将超警戒水位0.3米',
        source: '省水文水资源勘测局',
        issuedAt: '2026-07-15T08:00:00+08:00',
        polygons: [],
      },
    ],
    risks: [
      {
        id: 'risk-map-001',
        level: 'attention',
        area: '东山街道局部',
        polygons: [
          { lat: 31.955, lon: 118.835 },
          { lat: 31.955, lon: 118.845 },
          { lat: 31.945, lon: 118.845 },
          { lat: 31.945, lon: 118.835 },
        ],
      },
      {
        id: 'risk-map-002',
        level: 'high',
        area: '竹山路低洼段',
        polygons: [
          { lat: 31.950, lon: 118.830 },
          { lat: 31.950, lon: 118.835 },
          { lat: 31.945, lon: 118.835 },
          { lat: 31.945, lon: 118.830 },
        ],
      },
    ],
    reports: [
      {
        id: 'rpt-map-001',
        type: '积水',
        lat: 31.952,
        lon: 118.841,
        status: 'verified',
        description: '东山路上元大街路口积水，脚踝深度',
        reportedAt: '2026-07-15T09:45:00+08:00',
      },
      {
        id: 'rpt-map-002',
        type: '道路无法通行',
        lat: 31.948,
        lon: 118.837,
        status: 'verified',
        description: '竹山路（上元大街-天元路段）临时封闭',
        reportedAt: '2026-07-15T08:30:00+08:00',
      },
      {
        id: 'rpt-map-003',
        type: '地下空间进水',
        lat: 31.946,
        lon: 118.843,
        status: 'pending',
        description: '某小区B1层有少量进水',
        reportedAt: '2026-07-15T09:20:00+08:00',
      },
    ],
    roadEvents: [
      {
        id: 'road-001',
        type: '封闭',
        description: '竹山路（上元大街-天元路段）因积水临时封闭',
        polyline: [
          { lat: 31.948, lon: 118.833 },
          { lat: 31.941, lon: 118.833 },
        ],
      },
      {
        id: 'road-002',
        type: '缓行',
        description: '天元路因排水作业单向通行',
        polyline: [
          { lat: 31.950, lon: 118.838 },
          { lat: 31.950, lon: 118.845 },
        ],
      },
    ],
    shelters: getMockShelters(),
  }
}

/** 上报历史模拟数据 */
export function getMockReportHistory(): ReportHistoryItem[] {
  return [
    {
      id: 'rpt-his-001',
      eventType: 'waterlogging',
      status: 'verified',
      createdAt: '2026-07-15T09:45:00+08:00',
      address: '东山路上元大街路口',
    },
    {
      id: 'rpt-his-002',
      eventType: 'road_blocked',
      status: 'pending',
      createdAt: '2026-07-15T08:30:00+08:00',
      address: '竹山路（上元大街-天元路段）',
    },
    {
      id: 'rpt-his-003',
      eventType: 'basement_flood',
      status: 'verified',
      createdAt: '2026-07-14T16:20:00+08:00',
      address: '百家湖某小区B1层',
    },
    {
      id: 'rpt-his-004',
      eventType: 'manhole_damaged',
      status: 'rejected',
      createdAt: '2026-07-13T11:00:00+08:00',
      address: '胜太路与天元路交叉口',
    },
  ]
}
