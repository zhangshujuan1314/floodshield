# 汛安 FloodShield

AI 洪涝预警与避险平台

> 官方预警 → 风险计算 → 居民查看 → 上报 → 社区核验 → 路线更新 → 通知闭环

汛安把官方气象与应急信息、局地雨情、积水上报、道路状态和避险场所数据，转化为居民能立即执行的社区级风险提示、证据化路线建议和基层处置闭环。

## 当前进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 0 | ✅ 完成 | 仓库骨架、Docker Compose、mock 模式 |
| Phase 1 | ✅ 完成 | 领域模型、PostGIS 迁移、风险引擎 |
| Phase 2 | ✅ 完成 | 居民端闭环（6 页面）、管理后台（8 页面） |
| Phase 2.5 | ✅ 完成 | 安全加固：JWT 认证、数据库驱动预警、CheckConstraints |
| Phase 3 | ✅ 完成 | 社区/应急后台：全部端点数据库驱动（报告核验、任务管理、审计日志） |
| Phase 4 | ✅ 完成 | 真实数据适配器：气象（OpenWeatherMap）、地图（高德）、通知（Webhook/SMS） |
| Phase 5 | ✅ 完成 | AI 辅助：行动卡生成、语音播报、报告分类（含安全防护栏） |
| Phase 6 | ✅ 完成 | 演练和加固：安全中间件、集成测试、对抗性审查（评级：BETA） |

### 项目统计

| 指标 | 数值 |
|------|------|
| 源文件 | 170+ |
| 代码行数 | 25,000+ |
| 后端端点 | 35 个 |
| 测试用例 | 135+ 个（含集成测试） |
| 数据库表 | 15 张（PostGIS） |
| 数据库约束 | 5 个 CheckConstraint |
| 中间件 | 4 个（限流、安全头、净化、大小限制） |
| 数据适配器 | 4 组（气象、地图、通知、AI） |
| 前端页面 | 14 个（居民 6 + 后台 8） |
| 对抗审查 | 6 轮，0 P0 残留 |

### 安全评级

**BETA** — 经过 6 轮对抗性审查，0 个 P0 安全漏洞残留。

| 安全特性 | 状态 |
|----------|------|
| JWT 认证 + PBKDF2 | ✅ |
| SECRET_KEY 启动守卫 | ✅ |
| 登录限流（5次/分钟） | ✅ |
| 安全响应头（CSP/HSTS） | ✅ |
| AI 安全防护栏 | ✅ |
| 语音脚本安全校验 | ✅ |
| CheckConstraints | ✅ |
| 审计日志 | ✅ |
| 集成测试（关键路径） | ✅ |

### 安全加固（Phase 2.5）

经过三轮对抗性审查，系统安全性从"可演示"提升到"可部署"：

| 类别 | 修复项 | 状态 |
|------|--------|------|
| **P0 认证** | JWT 真实认证（PyJWT + PBKDF2） | ✅ |
| **P0 认证** | MOCK_MODE 默认关闭（`False`） | ✅ |
| **P0 认证** | SECRET_KEY 启动守卫（拒绝默认密钥） | ✅ |
| **P0 认证** | 密码验证不再被 MOCK_MODE 跳过 | ✅ |
| **P1 安全** | 禁用账户（`is_active=False`）无法登录 | ✅ |
| **P1 安全** | 用户名枚举时序缓解（dummy PBKDF2） | ✅ |
| **P1 安全** | 异常处理收窄（仅捕获 DB 错误） | ✅ |
| **P1 安全** | 全部数据缺失时 `risk_score=-1.0`（非 0.0） | ✅ |
| **P1 数据** | 预警端点改为数据库驱动（不再返回 fixtures） | ✅ |
| **P2 加固** | User.role / RiskSnapshot / Shelter CheckConstraints | ✅ |
| **P2 加固** | Alembic 迁移 `003_add_check_constraints.py` | ✅ |
| **P2 加固** | 风险等级对齐 SPEC：`normal/attention/high/critical` | ✅ |
| **P2 加固** | JWT 过期时间 24h → 60min | ✅ |
| **P2 加固** | 预警 upsert（source + external_id 去重） | ✅ |

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        居民端 (Taro)                         │
│  首页风险 · 地图图层 · 避险路线 · 上报 · 语音播报 · 我的      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / WSS
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI 后端服务                           │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│  │ auth │ │ geo  │ │alerts│ │ risk │ │routes│ │shelter│   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘    │
│  ┌──────────┐ ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  │observat. │ │notificat.│ │  ai  │ │audit │ │  ai  │     │
│  └──────────┘ └──────────┘ └──────┘ └──────┘ └──────┘     │
└────┬────────────┬────────────┬────────────┬─────────────────┘
     │            │            │            │
┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
│PostgreSQL│ │  Redis  │ │对象存储 │ │外部数据 │
│ + PostGIS│ │  缓存   │ │ 文件   │ │适配器   │
└─────────┘ └─────────┘ └────────┘ └─────────┘
                                    ┌─────────────────┐
                                    │ 管理后台 (Next.js)│
                                    └─────────────────┘
```

## 环境要求

- Docker 24+ 与 Docker Compose v2
- Node.js 18+
- Python 3.11+
- （可选）PostgreSQL 15+ 与 PostGIS 扩展

## 快速开始

```bash
# 克隆仓库
git clone <repo-url> floodshield
cd floodshield

# 启动全部服务
docker compose up -d

# 查看日志
docker compose logs -f api
```

服务启动后：

- API 服务：http://localhost:8000
- API 文档（Swagger）：http://localhost:8000/docs
- 管理后台：http://localhost:3000
- 小程序：使用微信开发者工具导入 `apps/miniapp/`

## Mock 模式

开发阶段可启用 mock 数据源。mock provider 提供：

- 模拟官方预警（暴雨黄色/橙色/红色）
- 模拟雨情观测
- 模拟积水报告和道路事件
- 模拟避险场所
- 模拟路线规划

### 启用 Mock 模式

```bash
# 在 services/api/.env 中设置
MOCK_MODE=true
```

> ⚠️ **安全提示**：`MOCK_MODE` 默认为 `False`（认证强制开启）。启用 Mock 模式会跳过认证，仅用于本地开发。

### 切换到真实数据源

1. 在 `services/api/.env` 中配置真实 API 密钥
2. 确保 `MOCK_MODE=false`（默认值）
3. 设置 `SECRET_KEY` 为安全随机值
4. 重启 API 服务

**重要**：真实外发（短信、推送）必须显式配置凭证并经人工确认，禁止在无凭证时发送。

## 演示账号

| 角色 | 用户名 | 密码 | 权限范围 |
|------|--------|------|----------|
| 系统管理员 | admin | admin123 | 全部功能 |
| 普通居民 | user | user123 | 查看风险、上报、路线 |
| 社区工作者 | community | comm123 | 核验报告、维护场所 |
| 应急管理站 | emergency | emerg123 | 跨社区态势、规则配置 |

## 项目结构

```
floodshield/
├── apps/
│   ├── miniapp/              # Taro + React + TypeScript 居民端
│   │   ├── src/
│   │   │   ├── pages/        # 首页、地图、避险、我的
│   │   │   ├── components/   # 通用组件
│   │   │   ├── services/     # API 调用
│   │   │   └── app.ts        # 入口
│   │   └── project.config.json
│   └── admin/                # Next.js + TypeScript 管理后台
│       ├── src/
│       │   ├── app/          # 页面路由
│       │   ├── components/   # UI 组件
│       │   └── lib/          # 工具函数
│       └── next.config.js
├── services/
│   └── api/                  # FastAPI + Python 后端
│       ├── app/
│       │   ├── modules/      # 业务模块
│       │   │   ├── auth/     # 认证与权限
│       │   │   ├── geo/      # 空间查询
│       │   │   ├── alerts/   # 官方预警
│       │   │   ├── observations/  # 雨情、传感器、公众报告
│       │   │   ├── risk/     # 风险计算
│       │   │   ├── routes/   # 路线规划
│       │   │   ├── shelters/ # 避险场所
│       │   │   ├── notifications/ # 通知闭环
│       │   │   ├── ai/       # AI 辅助
│       │   │   └── audit/    # 审计日志
│       │   ├── providers/    # 外部数据适配器
│       │   ├── core/         # 配置、数据库、安全
│       │   └── main.py       # FastAPI 入口
│       ├── tests/            # 测试
│       └── requirements.txt
├── docs/                     # 项目文档
├── docker-compose.yml        # 本地开发环境
├── FLOOD_PLATFORM_SPEC.md    # 产品规格说明书
├── CLAUDE.md                 # Claude Code 项目约定
└── README.md                 # 本文件
```

## API 文档

启动 API 服务后访问：

- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- OpenAPI JSON：http://localhost:8000/openapi.json

接口统一返回 `requestId`、`dataStatus`、时间戳和来源字段。

### 主要接口

**居民端**

```
GET  /v1/health                    # 健康检查
GET  /v1/alerts                    # 官方预警列表
GET  /v1/nearby/summary?areaId=&lat=&lon=  # 附近风险摘要
GET  /v1/map/layers?areaId=&types=         # 地图图层
GET  /v1/shelters/nearby?lat=&lon=         # 附近避险场所
POST /v1/hazard-reports            # 提交隐患报告
GET  /v1/hazard-reports/{id}       # 查询报告
POST /v1/routes/evacuation         # 避险路线规划
GET  /v1/routes/{id}               # 查询路线
POST /v1/notifications/subscriptions  # 订阅通知
POST /v1/voice/announcement        # 语音播报
```

**管理后台**

```
GET   /v1/admin/risk/overview
GET   /v1/admin/reports?state=pending_review
POST  /v1/admin/reports/{id}/verify
POST  /v1/admin/reports/{id}/reject
POST  /v1/admin/tasks
POST  /v1/admin/notifications/dispatch
GET   /v1/admin/audit-logs
```

**内部采集**

```
POST /internal/ingestion/{sourceId}/warnings
POST /internal/ingestion/{sourceId}/rainfall
POST /internal/risk/recompute
```

## 测试

```bash
# 后端测试（135+ 个测试）
cd services/api
pytest -v

# 带覆盖率
pytest --cov=app --cov-report=html
```

### 测试套件

| 套件 | 数量 | 覆盖 |
|------|------|------|
| API 集成 | 25 | 所有端点、错误格式、请求 ID |
| 风险引擎 | 16 | 正常/过期/缺失/冲突/越界/未知/回放 |
| 通知安全 | 13 | 幂等性/状态生命周期/渠道/批量 |
| 路线安全 | 10 | 3 种场景/几何/安全字段 |
| 健康检查 | 3 | 请求 ID 传播 |
| 认证安全 | 16 | JWT 创建/验证/过期/角色检查 |
| 预警数据库 | 17 | 数据库查询/过滤/MOCK 回退/转换 |
| **AI 安全** | **31** | **安全校验/schema 验证/注入防御/降级** |
| **地图适配器** | **18** | **高德 API/缓存/错误处理** |
| **气象适配器** | **17** | **OpenWeatherMap/TTL 缓存/降级** |
| **集成测试** | **4** | **关键路径端到端** |

### 安全关键测试

- `test_all_missing_returns_unknown_risk_level` — 缺失数据 ≠ 安全（risk_score=-1.0）
- `test_no_data_unknown_risk` — 无数据时风险为 unknown，不是 normal
- `test_verify_token_expired` — 过期 JWT 拒绝
- `test_get_current_user_no_token_non_mock_401` — 非 Mock 模式无 token 返回 401
- `test_require_role_wrong_role_403` — 角色权限拦截
- `test_dangerous_output_rejected` — AI 输出含精确积水深度被拒绝
- `test_rescue_confirmation_rejected` — AI 输出含救援确认被拒绝
- `test_injection_sanitized` — 提示注入被净化
- `test_alert_to_nearby_flow` — 预警→风险→附近摘要端到端
- `test_report_verify_audit` — 报告→核验→审计日志

详见 [docs/test-matrix.md](docs/test-matrix.md)。

## 环境变量

### API 服务 (services/api/.env)

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://floodshield:floodshield@localhost:5432/floodshield
REDIS_URL=redis://localhost:6379/0

# 安全（生产环境必须修改 SECRET_KEY）
SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Mock 模式（默认关闭，认证强制开启）
MOCK_MODE=false

# 外部数据源（真实模式需要）
WEATHER_API_KEY=
WEATHER_API_URL=
MAP_API_KEY=
MAP_API_URL=
SMS_API_KEY=
SMS_API_SECRET=

# AI 服务
AI_ENABLED=true
AI_PROVIDER=mock
AI_API_KEY=
AI_MODEL=gpt-4

# 文件存储
STORAGE_TYPE=local
STORAGE_PATH=./uploads

# 日志
LOG_LEVEL=INFO
AUDIT_LOG_ENABLED=true
```

### 管理后台 (apps/admin/.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
```

### 居民端 (apps/miniapp/.env)

```bash
TARO_APP_API_URL=http://localhost:8000
TARO_APP_MAP_KEY=
```

## 贡献指南

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交前确保测试通过：`pytest && npm test`
4. 提交 PR 并描述变更内容

### 代码规范

- Python：遵循 PEP 8，使用 ruff 格式化
- TypeScript：使用 ESLint + Prettier
- 每个安全关键分支必须有对应测试
- API 改动必须同步更新 OpenAPI 文档和前端类型

### 提交规范

```
feat: 新功能
fix: 修复
docs: 文档
test: 测试
refactor: 重构
chore: 构建/工具
```

## 许可证

MIT License

## 数据安全免责声明

1. **非官方预警源**：汛安平台风险结论基于多源数据综合计算，不构成法定预警。所有预警信息以属地气象、水务、应急管理部门官方发布为准。

2. **数据时效性**：平台展示的数据带有观测时间和有效期。超过有效期的数据可能已过期，请以现场标志和官方最新指令为准。

3. **路线参考性**：路线建议基于地图供应商数据和平台风险重排，不能替代现场判断。请以实际道路标志和官方管制信息为准。

4. **位置隐私**：平台默认不做后台持续定位。公众报告的位置经过空间模糊处理（约 100 米范围）。精确位置仅在核验和救援协同等明确目的下短期保存。

5. **AI 辅助定位**：AI 功能仅用于信息摘要、分类和辅助决策，不用于决定预警等级、发布高危消息或确认救援状态。

6. **数据来源**：平台数据来自官方授权、平台计算和公众观测三个层级，每个数据来源均标注来源、授权状态和可信等级。
