# ARCHITECTURE.md — CareerCopilot-SkillMemory

## 1) 系统流程（System Flow）
1. Source Ingestion：抓取职位数据（公司官网/招聘平台）
2. Matching：结合 USER_PROFILE 做职位匹配打分与解释
3. HITL Suggestion：生成建议列表与可点击 URL，由用户确认
4. Trajectory Logging：记录执行轨迹（state/action/outcome/error）
5. Memory Update：将有效信息写入 memory_store（note/link/summarize）
6. Skill Distillation：从成功轨迹生成候选技能（Skill DSL）
7. Skill Validation：重放验证，失败则进入 patch/retry
8. Governance：对技能进行评分、TTL、冲突消解、回滚
9. Online Reuse：后续任务优先检索并复用高质量技能

## 2) MVP contract
- Single-user only: 只服务一个固定用户画像，不做多租户
- HITL-first: 默认只推荐并给出链接，不自动投递
- Interview-demo-first: 设计目标是展示 agent 能力与工程质量，而不是研究型结果
- Feedback-driven optimization: 以用户 `accept / reject / ignore` 反馈驱动后续排序与记忆更新
- FastAPI required: 后端能力必须可经由 API 调用；Streamlit 只是展示层
- Minimal credible loop:
  1. 从稳定来源采集职位
  2. 对职位做规则 + 语义匹配
  3. 输出建议与解释
  4. 用户点击 URL
  5. 记录反馈
  6. 从重复成功轨迹中沉淀一个可复用 skill

## 3) 支持的数据源策略
### Priority A: 稳定来源（P0 必做）
- 公司官网职位页
- P0 首选实现：得物
- 初始目标公司：
  - 腾讯
  - 高德
  - 阿里巴巴
  - 美团
  - 蚂蚁
  - 华为
  - 得物
  - 字节跳动
  - 京东
  - 小红书
  - bilibili
  - 米哈游
  - 拼多多

### Priority B: 招聘平台（best effort）
- P0 首选实现：Boss直聘
- Boss直聘
- 牛客
- 拉勾
- 脉脉

说明：
- MVP 不要求所有来源都稳定支持
- 只要 2 个以上来源能完成端到端演示即可；默认组合为「得物 + Boss直聘」
- 若页面结构不稳定或存在反爬，优先切回公司官网或本地 replay fixture

## 4) 系统核心模块
1. `trajectory_collector`：统一采集任务执行轨迹
2. `memory_store`：长期记忆存储、关联、压缩
3. `skill_distiller`：轨迹 -> 候选技能
4. `skill_registry`：技能版本管理与状态管理
5. `skill_selector`：按上下文选择技能（controller-lite）
6. `governance_engine`：质量评分、TTL、回滚、冲突策略
7. `user_model`：读取与更新个体画像
8. `matcher`：职位匹配、排序、解释
9. `demo_ui`：展示与操作入口（Streamlit）

## 5) Skill definition for this project
- Skill follows the OpenAI Codex skill concept: a focused package of instructions, optional references, and optional scripts with clear trigger boundaries.
- In this project, a skill is not a vague "ability". It is a replayable workflow unit.
- Initial skill families:
  - `job_ingestion_skill`: 从某类页面提取职位结构化信息
  - `matching_skill`: 在特定上下文下生成排序或解释
  - `hitl_suggestion_skill`: 生成建议列表、解释、链接输出格式
- Minimal skill schema fields:
  - `name`
  - `description`
  - `trigger`
  - `inputs`
  - `steps`
  - `expected_output`
  - `constraints`
  - `source_run_ids`
  - `validation_status`
  - `score`
  - `version`

## 6) 数据库设计
### SQLite（事务型元数据）
- `jobs(job_id, source, title, company, location, url, raw_json, created_at)`
- `runs(run_id, task_type, status, started_at, ended_at, notes)`
- `trajectory_events(event_id, run_id, step_no, state, action, outcome, error, ts)`
- `skills(skill_id, version, status, trigger, risk_level, ttl, created_at, updated_at)`
- `skill_metrics(skill_id, version, success_rate, avg_steps, reuse_count, last_used_at)`
- `skill_lineage(parent_skill_id, parent_version, child_skill_id, child_version, reason)`
- `hard_cases(case_id, run_id, failure_type, summary, status, created_at)`
- `user_feedback(feedback_id, run_id, job_id, decision, comment, ts)`
- `recommendations(rec_id, run_id, job_id, total_score, reason_json, created_at)`

### Chroma / Vector Store（语义检索）
- `memory_notes`（长期记忆片段）
- `skill_docs`（技能文本、触发条件、上下文）
- `job_embeddings`（职位语义向量）

## 7) 重要设计细节
- HITL-first：默认不自动提交申请
- Replay-first Validation：技能重放验证后才能激活
- Governance-first Reuse：低分/失效技能自动降权或下线
- Explainability：匹配分可解释（semantic/preference/feasibility/risk）
- Attribution：外部借鉴记录到 `docs/ATTRIBUTION.md`
- On-demand Reference：按需查 `docs/REFERENCE_MAP.md`
- User feedback is the primary online signal: `accept / reject / ignore`
- Personalization starts explicit, not inferred: 初期以 `USER_PROFILE.yaml` + feedback 更新为主
- API-first backend: 核心能力应可通过 FastAPI 调用，便于后续 UI / automation 接入
- Default UI and content language: 中文

## 8) 推荐项目结构
```text
careercopilot-skillmemory/
  app/
    api/
    core/
      matcher/
      memory/
      skills/
      governance/
      user_model/
    agents/
    ui/
  data/
    sqlite/
    chroma/
    logs/
  configs/
    USER_PROFILE.yaml
    prompts/
  docs/
    REFERENCE_MAP.md
    ATTRIBUTION.md
    ARCHITECTURE.md
    API.md
  tests/
    unit/
    integration/
    e2e/
  scripts/
    eval/
    replay/
    bootstrap/
  deliverables/
  AGENTS.md
  IMPLEMENTATION_PLAN.md
  RUNBOOK.md
  CHANGELOG_DEV.md
  MILESTONES.md
```
