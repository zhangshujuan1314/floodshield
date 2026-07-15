# FloodShield 项目约定

## 先读文件
- FLOOD_PLATFORM_SPEC.md
- docs/architecture.md
- docs/ai-safety.md

## 关键安全规则
- 官方预警、平台风险等级和 AI 摘要必须分开
- 缺失/过期数据不能默认为安全
- 路线必须返回证据、更新时间和失效时间
- 用户报告先待核验，核验后才能升级可信度
- 不保存后台持续定位，不把精确位置放入公开 API 或日志
- mock provider 默认开启，真实外发必须显式配置和人工确认

## 项目结构
- apps/miniapp/ — Taro + React + TypeScript 居民端
- apps/admin/ — Next.js + TypeScript 后台
- services/api/ — FastAPI + Python 后端
- docker-compose.yml — 本地开发环境

## 开发命令
- docker compose up -d — 启动所有服务
- cd services/api && uvicorn app.main:app --reload — 启动 API
- cd services/api && pytest — 运行测试
- cd apps/admin && npm run dev — 启动后台
- cd apps/miniapp && npm run dev:weapp — 启动小程序

## 开发习惯
- 先读代码和测试，再做最小改动
- 每个安全关键分支都要有测试
- API 改动同步更新 OpenAPI、前端类型和测试
- 保留用户已有修改，禁止 destructive git 命令
- 每次完成必须报告命令和结果，未验证内容单独列出

## 禁止行为
- 把模型输出当作官方预警
- 没有传感器时生成精确积水深度
- 把风险未知的路线标记为安全
- 自动发布未经核验的高危消息
- 自动确认救援已派出
- 默认后台持续定位
- 在没有凭证时发送真实短信/推送
