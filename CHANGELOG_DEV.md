# CHANGELOG_DEV.md

> 开发日志（手工维护）。每次实现闭环完成后追加一条。

## Template
- Date:
- Scope:
- Ref used:
- What changed:
- Why changed:
- Validation evidence:
- Risks / rollback:
- Next step:

## 2026-03-23
- Scope: 初始化 Python/FastAPI MVP 骨架、默认配置与测试
- Ref used: R1
- What changed:
  - 新增 `pyproject.toml`，定义 FastAPI/Pydantic/PyYAML/pytest 依赖
  - 新增 `app/` 包、API 路由、核心 schemas、本地 stub store
  - 新增 `configs/USER_PROFILE.yaml` 与 `configs/sources.yaml`
  - 新增基础单元测试与 API 集成测试
  - 更新 `README.md` 与 `.gitignore`
- Why changed:
  - 为后续 ingestion / matching / memory / skills 实现建立可运行骨架
  - 先把 API contract 与 schema contract 固化，降低后续改动成本
- Validation evidence:
  - 待安装 Python 依赖后执行 `pytest`
  - 待启动服务后验证 `/health` 与 `/profile/load`
- Risks / rollback:
  - 当前为 placeholder 行为，尚未接入真实数据源和持久化数据库
  - 若依赖安装失败，需要先解决本地 Python 环境
- Next step:
  - 安装依赖并跑通测试
  - 继续实现 schema-backed profile loading、真实 source adapter 抽象与 trajectory logging

## 2026-03-23
- Scope: P0 ingestion 适配器抽象、fixture 解析、trajectory logging
- Ref used: R1
- What changed:
  - 新增 source config loader 与 `dewu` / `boss_zhipin` 适配器管理器
  - 用真实入口 URL 替换 placeholder source config，并绑定 fixture 文件
  - `/jobs/ingest` 改为通过 adapter 执行解析并落盘 run trajectory
  - `/runs/{run_id}` 改为优先返回真实持久化的 run 详情
  - 新增 adapter 单元测试与 run 轨迹集成测试
- Why changed:
  - 按 `AGENTS.md` 的 P0 路线，把职位抓取从占位逻辑推进到可扩展的 source-adapter 架构
  - 先用 fixture 保证可验证性，再逐步接入 live site
- Validation evidence:
  - 待执行 `pytest`
  - 待检查 `/jobs/ingest` 与 `/runs/{run_id}` 的实际返回
- Risks / rollback:
  - 当前 live HTTP / Playwright 尚未接入，仍是 fixture-first
  - Boss 与得物页面结构后续可能要求额外解析策略
- Next step:
  - 运行测试并修复失败
  - 补充 live fetch 封装与更真实的 normalized job fields

## 2026-03-23
- Scope: live fetch layer for Dewu/Boss ingestion
- Ref used: R1
- What changed:
  - 新增 `live_fetch.py`，通过 `curl` 且清理代理变量执行 live HTTP 抓取
  - Boss 适配器支持 live HTML 解析职位卡片
  - 得物适配器改为使用 Playwright 捕获浏览器中的签名职位请求；无法提取职位记录时自动回退到 fixture
  - `README.md` 增加 `CAREERCOPILOT_ENABLE_LIVE_FETCH=1` 使用说明
- Why changed:
  - 用户要求重新验证 `curl` 可达性，并在可行时补 live fetch layer
  - 保持 live 能力可用的同时，不破坏当前 fixture-first 的可测性
- Validation evidence:
  - 待执行 `pytest`
  - 已人工验证 `curl` 可访问得物与 Boss 入口 URL
- Risks / rollback:
  - 得物 live fetch 依赖本地可用的 Playwright browser runtime
  - Boss live HTML 结构后续可能变化，需要补更稳健的 parser
- Next step:
  - 运行测试并确认 fallback/live parser 行为
  - 若继续推进 live 得物，需定位真实职位数据接口或 Playwright network path

## 2026-03-23
- Scope: P0 end-to-end workflow completion
- Ref used: R1
- What changed:
  - 新增 profile-driven matcher，按角色、关键词、城市、实习类型和历史反馈打分
  - `/jobs/match` 由占位逻辑改为读取持久化职位并返回真实 recommendation payload
  - `/suggestions/generate` 生成包含标题、公司、城市、原因和可点击 URL 的 HITL 建议
  - `/feedback` 现在会把反馈追加到 run trajectory，形成 audit trail
  - Dewu/Boss live ingestion 已通过 API `use_live_browser` 开关接入
  - 更新 `README.md` 和 `.gitignore`
- Why changed:
  - 按 `AGENTS.md` 完成 P0：end-to-end suggestion + jump workflow with HITL
  - 让 P0 演示可以通过真实 API 路径跑通，而不是只靠骨架代码
- Validation evidence:
  - `pytest` -> 14 passed
  - 手工样例运行已验证 `ingest -> match -> suggestions -> feedback`
- Risks / rollback:
  - Boss live HTML 结构仍可能变化
  - Dewu live fetch 依赖 Playwright 浏览器运行时
- Next step:
  - 进入 P1：candidate skill distillation、registry、selector
