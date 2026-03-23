# CareerCopilot-SkillMemory

面向个人求职的单用户 Agent 项目，用于展示 job ingestion、matching、HITL suggestions、memory、skill reuse 等能力。

## 当前状态
- P0 已完成：`抓取 -> 匹配 -> 建议+跳转(HITL) -> 反馈记录`
- 已定义 `USER_PROFILE`、`MemoryNote`、`Skill` 等核心 schema
- 已落地默认配置：得物 + Boss直聘，中文优先，单用户画像
- 支持 fixture-first 演示，也支持 live fetch

## 本地启动
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Live Fetch
默认使用 fixture，保证测试与演示可重复。

如需启用 live fetch：
```bash
export CAREERCOPILOT_ENABLE_LIVE_FETCH=1
```

当前行为：
- `boss_zhipin` 支持 live HTML 抓取并解析职位卡片
- `dewu` 使用 Playwright 捕获浏览器发起的签名职位请求；若无法捕获或解析，则自动回退到 fixture

## P0 Workflow
1. `POST /jobs/ingest`
2. `POST /jobs/match`
3. `POST /suggestions/generate`
4. 用户点击返回的 `url`
5. `POST /feedback`
6. `GET /runs/{run_id}` 查看轨迹与审计信息

示例结果：
- 匹配结果包含 `title / company / location / url / total_score / score_breakdown`
- 建议结果包含可直接打开的职位 `url`
- feedback 会写入 memory note，并追加到 run audit trail

## 运行测试
```bash
pytest
```
