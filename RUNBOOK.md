# RUNBOOK.md — Agentic Implementation Protocol

## Purpose
用于约束 Claude Code 的实现流程，确保“实现质量 > 实现速度”。

## Global Rules
1. 严格增量开发：每次只完成一个小目标，不跨阶段大改。
2. 每个任务必须走闭环：PLAN -> IMPLEMENT -> VALIDATE -> DIAGNOSE -> PATCH -> RE-VALIDATE。
3. 未通过验证不得进入下一个任务。
4. 所有实现都要有可追踪证据（测试结果、日志、截图、报告之一）。
5. 遇到外部站点不稳定/反爬，优先启用 fallback（公司官网职位页或本地 mock 流程）。

---

## Standard Loop (must follow)

### 1) PLAN
- 将当前任务拆成 <= 5 个可执行步骤。
- 标注本次任务对应的参考来源（见 `docs/REFERENCE_MAP.md`）：
  - `Ref used: R?`
  - `Why this ref:`
- 输出预期产物与验收标准。

### 2) IMPLEMENT
- 仅提交最小必要改动（minimal diff）。
- 避免“顺手重构”。
- 保持模块接口稳定，优先可读、可测。

### 3) VALIDATE
至少执行以下三类验证中的两类（核心任务建议全做）：
- 单元测试（unit tests）
- 集成验证（integration check）
- 样例运行证据（sample run logs / screenshot）

### 4) DIAGNOSE
若失败，必须给出：
- 根因分析（root cause）
- 问题类型（logic / interface / data / flaky env / external blocker）
- 是否需要回滚

### 5) PATCH
- 仅做最小安全修复。
- 不引入额外功能。

### 6) RE-VALIDATE
- 重跑失败相关验证 + 关键回归验证。
- 记录修复前后差异。

### 7) LOG
更新 `CHANGELOG_DEV.md`：
- What changed
- Why changed
- Evidence
- Risk / Follow-up

---

## Definition of Done (per task)
任务完成必须同时满足：
- [ ] 代码完成且可运行
- [ ] 验证通过
- [ ] 有证据产物（log/test/report/screenshot）
- [ ] 文档同步更新（至少 CHANGELOG_DEV.md）

---

## Reference-on-demand Rule
- 不在开工时一次性加载全部论文/仓库。
- 每个功能按需查询 `docs/REFERENCE_MAP.md` 对应 R1~R4。
- 每次任务总结中必须包含：
  - `Ref used:`
  - `Adapted idea:`
  - `Project-specific change:`

---

## Failure Handling Playbook

### A. 网站反爬或页面频繁变化
- 切换稳定职位源（公司官网）
- 使用 selector fallback / text-anchor 策略
- 增加 replayable mock case，先保证流程能力

### B. LLM 输出不稳定
- 使用固定 prompt template + JSON schema 校验
- 增加 deterministic post-check
- 温度降级、重试次数上限

### C. 技能污染（坏技能被复用）
- 立即降权 + 暂停技能
- 启动 rollback 到上一版本
- 标记 hard-case 进入 designer 队列

---

## Scope Guard
- P0/P1（MVP 主链路）未完成前，禁止进入 P3（高级自动化）。
- 如出现超时风险，优先保留：
  1) HITL 建议+跳转
  2) memory->skills 最小闭环
  3) 至少一组 ablation 结果

---

## Daily End Checklist
每天结束前必须输出：
1. 今日完成项
2. 未完成阻塞项
3. 明日第一优先级
4. 当前风险与缓解措施
5. 是否偏离两周目标（Yes/No + 原因）
