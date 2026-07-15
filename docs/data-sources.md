# 数据源文档

## 1. 数据源分层

汛安的数据分为三个层级，每层有不同的可信度、更新频率和使用规则。

### 1.1 第一层：官方和授权数据

最高可信度，用于预警展示和风险硬约束。

| 数据源 | 内容 | 授权状态 | 刷新周期 |
|--------|------|----------|----------|
| 属地气象部门 | 暴雨/台风/雷电预警 | 需属地授权 | 实时推送或 5 分钟拉取 |
| 水务部门 | 水位、泵站、河道数据 | 需属地授权 | 5-15 分钟 |
| 应急管理部门 | 应急响应、转移指令 | 需属地授权 | 事件驱动 |
| 交通/路政部门 | 道路管制、封路信息 | 需属地授权 | 15-30 分钟 |
| 政府核验避险场所 | 场所、容量、开放状态 | 需属地授权 | 每日或事件驱动 |

**使用规则**：
- 官方预警只做事实展示，不能改写等级
- 同一事件按 `source + sourceEventId` 去重
- 预警撤销、更新和过期都产生审计事件
- 若本地气象部门使用地方标准，以属地气象部门解释为准

### 1.2 第二层：平台计算数据

基于第一层数据和规则引擎计算得出。

| 数据源 | 内容 | 计算方式 | 刷新周期 |
|--------|------|----------|----------|
| 统一空间网格风险 | 区域风险带、风险分数 | 规则引擎 | 预警触发或 5 分钟 |
| 路线风险重排 | 路线风险成本、推荐等级 | 风险匹配 + 排序 | 请求时计算 |
| 数据覆盖和新鲜度 | 各区域数据状态 | 元数据聚合 | 5 分钟 |
| 可信度分数 | 证据覆盖和一致程度 | 多因子计算 | 随风险快照 |

**使用规则**：
- 平台风险带不能冒充官方蓝、黄、橙、红预警
- 每次计算保存输入快照、规则版本和权重
- 缺失数据必须表现为"未知"，不能默认为安全

### 1.3 第三层：公众观测

可信度最低，需核验后才能升级。

| 数据源 | 内容 | 核验要求 | 刷新周期 |
|--------|------|----------|----------|
| 居民积水报告 | 积水位置、状态、照片 | 社区核验 | 实时提交 |
| 居民道路报告 | 道路受阻、原因 | 社区核验 | 实时提交 |
| 居民隐患报告 | 井盖、树木、地下空间 | 社区核验 | 实时提交 |
| 基层巡查记录 | 现场核实、处置记录 | 自动关联 | 实时提交 |

**使用规则**：
- 报告进入待核验队列，核验后才能升级可信度
- 公众可见报告位置模糊化（约 100 米范围）
- 图片和文字经过敏感信息检测
- 高危关键词进入高优先级队列

## 2. 适配器接口

所有外部数据通过适配器接入，业务层不直接依赖供应商。

### 2.1 天气预警适配器

```typescript
interface WeatherWarningProvider {
  /**
   * 获取指定区域内的生效预警
   * @param area GeoJSON Polygon 查询区域
   * @returns 标准化预警数组
   */
  fetchWarnings(area: GeoJSON.Polygon): Promise<RawWarning[]>;
}

interface RawWarning {
  sourceId: string;           // 数据源标识
  sourceEventId: string;      // 原始事件 ID
  hazardType: string;         // 灾种：暴雨、洪水、台风等
  officialLevel: string;      // 官方等级
  officialColor: string;      // 官方颜色
  geometry: GeoJSON;          // 影响区域
  issuedAt: string;           // 发布时间 (ISO 8601)
  updatedAt: string;          // 更新时间
  expiresAt: string;          // 失效时间
  revokedAt: string | null;   // 撤销时间
  rawPayload: object;         // 原始数据
  sourceUrl: string;          // 来源链接
  actionGuide: string;        // 行动指南
}
```

### 2.2 雨情观测适配器

```typescript
interface RainfallProvider {
  /**
   * 获取指定区域和时间窗口内的雨情观测
   * @param area GeoJSON Polygon 查询区域
   * @param windowMinutes 时间窗口（分钟）
   * @returns 雨情观测数组
   */
  fetchRainfall(area: GeoJSON.Polygon, windowMinutes: number): Promise<RainfallObservation[]>;
}

interface RainfallObservation {
  sourceId: string;           // 数据源标识
  stationId: string;          // 站点 ID
  geometry: GeoJSON;          // 站点位置
  rainfallMm: number;         // 降雨量 (mm)
  windowMinutes: number;      // 时间窗口
  observedAt: string;         // 观测时间
  quality: 'good' | 'suspect' | 'missing';
}
```

### 2.3 地图服务适配器

```typescript
interface MapProvider {
  /**
   * 地理编码：地址转坐标
   */
  geocode(query: string): Promise<Place[]>;

  /**
   * 逆地理编码：坐标转地址
   */
  reverseGeocode(lat: number, lng: number): Promise<Place>;

  /**
   * 路线规划
   */
  route(input: RouteRequest): Promise<RouteCandidate[]>;
}

interface RouteRequest {
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  constraints?: {
    avoidFlooded?: boolean;
    accessible?: boolean;      // 无障碍
    maxWalkingMeters?: number;
  };
}

interface RouteCandidate {
  geometry: GeoJSON;          // 路线几何
  distanceMeters: number;     // 距离
  durationSeconds: number;    // 预计耗时
  steps: RouteStep[];         // 分段详情
}
```

### 2.4 通知服务适配器

```typescript
interface NotificationProvider {
  /**
   * 发送通知
   * @param channel 渠道：sms、push、wechat
   * @param recipient 接收方标识
   * @param message 消息内容
   */
  send(channel: string, recipient: string, message: string): Promise<DeliveryResult>;
}

interface DeliveryResult {
  success: boolean;
  deliveryId: string;
  channel: string;
  sentAt: string;
  error?: string;
}
```

## 3. Mock 适配器

开发和测试阶段默认使用 mock 适配器，不发送真实外部请求。

### 3.1 MockWeatherWarningProvider

**行为**：
- 返回预设的预警数据集
- 支持按区域过滤
- 支持模拟预警撤销和过期

**预设数据**：
- 暴雨黄色预警（示例气象台，2 小时有效）
- 暴雨橙色预警（示例气象台，1 小时有效）
- 暴雨红色预警（示例气象台，30 分钟有效）

**配置**：
```python
# services/api/app/providers/weather/mock.py
MOCK_ALERTS = [
    {
        "sourceId": "mock_cma",
        "sourceEventId": "alert_001",
        "hazardType": "rainstorm",
        "officialLevel": "yellow",
        "officialColor": "yellow",
        "geometry": {...},
        "issuedAt": "2026-07-14T18:00:00+08:00",
        "expiresAt": "2026-07-14T20:00:00+08:00",
        "actionGuide": "减少外出，远离低洼地带"
    },
    # ...
]
```

### 3.2 MockRainfallProvider

**行为**：
- 返回模拟雨情数据
- 支持按时间窗口过滤
- 支持模拟数据缺失和异常

**预设数据**：
- 多个站点的 1 小时/3 小时/24 小时降雨量
- 包含 `good`、`suspect`、`missing` 三种质量状态

### 3.3 MockMapProvider

**行为**：
- 地理编码返回预设地点
- 路线规划返回 2-3 条候选路线
- 支持模拟路线穿过积水点或封路段

**预设数据**：
- 3 条候选路线：推荐、备选、风险未知
- 其中 1 条穿过模拟积水点
- 其中 1 条穿过模拟封路段

### 3.4 MockNotificationProvider

**行为**：
- 记录发送日志但不实际发送
- 返回模拟投递成功
- 支持模拟投递失败和重试

**日志格式**：
```
[MOCK] SMS sent to 138****1234: 暴雨黄色预警 - 减少外出
[MOCK] Push sent to user_001: 您所在的区域有积水报告
```

## 4. 字段映射

外部数据源字段到系统内部字段的映射规则。

### 4.1 预警字段映射

| 外部字段 | 内部字段 | 转换规则 |
|----------|----------|----------|
| `warningId` | `sourceEventId` | 直接映射 |
| `level` | `officialLevel` | 标准化为 blue/yellow/orange/red |
| `color` | `officialColor` | 保留原始颜色 |
| `type` | `hazardType` | 标准化为 rainstorm/flood/typhoon 等 |
| `area` | `geometry` | 转换为 GeoJSON |
| `publishTime` | `issuedAt` | 转换为 ISO 8601 + 时区 |
| `endTime` | `expiresAt` | 转换为 ISO 8601 + 时区 |
| `content` | `rawPayload` | 保留原始数据 |
| `source` | `sourceId` | 映射到数据源 ID |

### 4.2 雨情字段映射

| 外部字段 | 内部字段 | 转换规则 |
|----------|----------|----------|
| `station_id` | `stationId` | 直接映射 |
| `lat`, `lon` | `geometry` | 构造 Point GeoJSON |
| `rain` | `rainfallMm` | 单位统一为 mm |
| `time` | `observedAt` | 转换为 ISO 8601 |
| `quality` | `quality` | 映射到 good/suspect/missing |

### 4.3 道路事件字段映射

| 外部字段 | 内部字段 | 转换规则 |
|----------|----------|----------|
| `road_id` | `roadSegmentRef` | 直接映射 |
| `event_type` | `eventType` | 标准化枚举 |
| `severity` | `severity` | 标准化枚举 |
| `start_time` | `validFrom` | 转换为 ISO 8601 |
| `end_time` | `validUntil` | 转换为 ISO 8601 |
| `geometry` | `geometry` | 转换为 GeoJSON |

## 5. 授权状态

每个数据源必须记录其授权状态。

### 5.1 授权状态枚举

| 状态 | 说明 | 使用规则 |
|------|------|----------|
| `authorized` | 已获得正式授权 | 正常使用 |
| `pending` | 授权申请中 | 仅用于测试，不进入生产 |
| `expired` | 授权已过期 | 停止采集，保留历史数据 |
| `revoked` | 授权被撤销 | 立即停止，通知管理员 |
| `mock` | Mock 数据 | 仅用于开发测试 |

### 5.2 授权记录

```json
{
  "sourceId": "cma_beijing",
  "name": "北京市气象局",
  "authorizationStatus": "authorized",
  "authorizedAt": "2026-06-01T00:00:00+08:00",
  "expiresAt": "2027-06-01T00:00:00+08:00",
  "contactPerson": "张主任",
  "contactPhone": "010-12345678",
  "dataScope": "北京市暴雨预警",
  "rateLimit": "100 requests/minute",
  "notes": "已签署数据使用协议"
}
```

### 5.3 授权检查

每次数据采集前检查授权状态：

```python
async def check_authorization(source_id: str) -> bool:
    source = await get_data_source(source_id)
    if source.authorization_status != "authorized":
        logger.warning(f"数据源 {source_id} 授权状态异常: {source.authorization_status}")
        return False
    if source.expires_at and source.expires_at < datetime.now():
        logger.warning(f"数据源 {source_id} 授权已过期")
        return False
    return True
```

## 6. 刷新周期

### 6.1 默认刷新周期

| 数据类型 | 刷新周期 | 触发方式 |
|----------|----------|----------|
| 官方预警 | 5 分钟 | 定时拉取 + 推送 |
| 雨情观测 | 5-15 分钟 | 定时拉取 |
| 道路管制 | 15-30 分钟 | 定时拉取 |
| 避险场所 | 每日 | 定时拉取 + 手动更新 |
| 公众报告 | 实时 | 事件驱动 |
| 风险快照 | 5 分钟 | 预警触发 + 定时 |
| 路线规划 | 请求时 | 按需计算 |

### 6.2 高峰期调整

暴雨期间自动缩短刷新周期：

```python
def get_refresh_interval(source_type: str, risk_level: str) -> int:
    """返回刷新间隔（秒）"""
    base_intervals = {
        "warning": 300,      # 5 分钟
        "rainfall": 300,     # 5 分钟
        "road_event": 900,   # 15 分钟
        "shelter": 86400,    # 24 小时
    }

    # 高风险时缩短间隔
    if risk_level in ("high", "critical"):
        return base_intervals[source_type] // 2

    return base_intervals[source_type]
```

### 6.3 数据过期处理

```python
async def check_data_freshness(source_id: str) -> DataStatus:
    """检查数据新鲜度"""
    last_update = await get_last_update_time(source_id)
    max_age = get_max_age(source_id)

    if last_update is None:
        return DataStatus.UNKNOWN

    age = datetime.now() - last_update
    if age < max_age * 0.5:
        return DataStatus.FRESH
    elif age < max_age:
        return DataStatus.PARTIAL
    else:
        return DataStatus.STALE
```

## 7. 数据质量指标

### 7.1 质量指标定义

| 指标 | 定义 | 目标值 |
|------|------|--------|
| 采集成功率 | 成功采集次数 / 总采集次数 | >= 99% |
| 字段完整率 | 完整记录数 / 总记录数 | >= 95% |
| 时间有效性 | 有效时间戳记录数 / 总记录数 | >= 99% |
| 空间有效性 | 有效几何记录数 / 总记录数 | >= 99% |
| 数据新鲜率 | 新鲜数据覆盖区域 / 总区域 | >= 80% |
| 多源一致性 | 一致记录数 / 总记录数 | >= 90% |

### 7.2 质量监控

```python
class DataQualityMonitor:
    async def check_source(self, source_id: str) -> QualityReport:
        return QualityReport(
            source_id=source_id,
            fetch_success_rate=await self.calc_fetch_rate(source_id),
            field_completeness=await self.calc_completeness(source_id),
            time_validity=await self.calc_time_validity(source_id),
            spatial_validity=await self.calc_spatial_validity(source_id),
            freshness=await self.calc_freshness(source_id),
            issues=await self.get_issues(source_id),
        )
```

### 7.3 质量问题处理

| 问题类型 | 处理方式 |
|----------|----------|
| 采集超时 | 保留最近一次数据，标记过期，进入重试队列 |
| 字段缺失 | 拒绝写入风险计算，进入数据质量队列 |
| 地理范围异常 | 拒绝并记录，通知管理员 |
| 时间戳倒退 | 拒绝覆盖新数据，记录异常 |
| 多源冲突 | 保留所有原始值，显示冲突，不静默平均 |
| 数据源故障 | 切换到备用源或标记数据缺失 |
