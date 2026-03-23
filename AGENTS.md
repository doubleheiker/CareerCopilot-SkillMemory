# CLAUDE.md — CareerCopilot-SkillMemory Project Spec (v6)

## Project Overview
CareerCopilot-SkillMemory: 面向个人求职的 Agent 项目，用于展示 agent system design、tool use、workflow reliability、memory、personalization 能力，并服务于我自己的求职流程。
MVP 定位：**single-user, HITL-first, interview-demo-first**。
技术核心：**Job Ingestion -> Matching -> HITL Suggestions -> Trajectory Logging -> Memory -> Skills Reuse**。  
目标周期：2周（MVP优先）。
项目通过对“experience→skills / memory→skills”领域方案进行调研（调研参考：`docs/REFERENCE_MAP.md`），借鉴调研方案的思路，完成以下面向落地实现的构建思路。

> Detailed architecture and structure: `docs/ARCHITECTURE.md`

## Primary Goals
1. 实现单用户求职主链路：抓取职位 -> 匹配排序 -> 生成建议 -> 给出可点击跳转链接
2. 记录任务轨迹与用户反馈（accept / reject / ignore），并据此更新记忆与偏好
3. 从重复成功轨迹中蒸馏可复用技能（Skill DSL / skill package）
4. 实现最小可用的技能治理（quality score / disable / cooldown / TTL / rollback）
5. 产出可直接用于面试展示的 demo、日志、设计说明与 evidence

## Non-Goals (MVP)
- 不做模型微调/强化学习训练
- 不追求复杂前端（优先快速可验证）
- 不做自动投递/自动提交申请
- 不保证所有招聘网站自动化（优先稳定可演示源）
- 不做多用户系统
- 不以研究论文式 ablation 为强制交付

## Tech Stack
- Python 3.11
- LangGraph（可回退自定义状态机）
- Playwright
- FastAPI
- Streamlit（dashboard/demo）
- SQLite + Chroma（or pgvector optional）
- OpenAI API（default）
- pytest + basic e2e scripts

## MVP Product Contract
- User scope: 仅服务于我自己的求职画像（single-user）
- Supported decision loop: agent 输出职位建议列表与 URL，用户决定点击哪一个或多个链接
- Success signal: 用户反馈 `accept / reject / ignore`
- Matching optimization target: 让后续推荐更符合用户反馈
- Skill definition: 参考 OpenAI Codex skill 概念，skill 是带有清晰触发条件的能力包，包含 instructions、optional references、optional scripts；在本项目中主要用于 job ingestion / matching / HITL suggestion 等可重复工作流
- Backend requirement: 必须提供 FastAPI 服务；Streamlit 用于 demo / dashboard
- Interview priority: 优先展示 agent workflow、memory、skill reuse、evidence，而不是追求复杂自动化或论文级实验

## MVP Defaults
- Primary language: 中文
- P0 company career source: 得物
- P0 job board source: Boss直聘
- Initial target role: Agent engineer
- Preferred city: Beijing
- Internship type: summer intern / daily intern
- Skill keywords: LLM watermarking、agent memory、RAG
- Disliked traits: low output

## Initial Data Source Scope
- Job boards (best effort): Boss直聘、牛客、拉勾、脉脉
- Preferred stable sources: 公司官网职位页
- Initial company list: 腾讯、高德、阿里巴巴、美团、蚂蚁、华为、得物、字节跳动、京东、小红书、bilibili、米哈游、拼多多
- Runtime expansion is allowed, but P0/P1 only require a small stable subset to run end-to-end

## External references (on-demand only)
- Canonical map: `docs/REFERENCE_MAP.md`
- Rule: 实现某功能时再查对应参考，不在项目开始时一次性加载全部论文/仓库。
- Rule: 参考“思想与接口模式”，不直接搬运外部项目核心实现。
- Rule: 借鉴记录写入 `docs/ATTRIBUTION.md`。

## Development Mode
- GitHub repo workflow（`main` 保护）
- Branch naming: `feat/*`, `fix/*`, `exp/*`, `docs/*`
- PR 模板必须包含：
  - Problem
  - Change
  - Ref used (R?)
  - Evidence（测试/日志/截图）
  - Risk & rollback
- 开发文档自动化：
  - 目标文档：`docs/ARCHITECTURE.md`, `docs/API.md`, `docs/CHANGELOG_AUTO.md`, `deliverables/REPORT.md`
  - 建议脚本：`scripts/docs/generate_docs.py`
  - 本地命令：`make docs`
  - CI 触发：push `main` 或打 tag

## Agentic Development Loop (must follow)
Implement -> Validate -> Analyze failure -> Patch -> Re-validate  
No large blind rewrites.

## Linked working docs (read on demand)
- Architecture / DB / project structure: `docs/ARCHITECTURE.md`
- API contract: `docs/API.md`
- Milestones: `MILESTONES.md`
- Implementation plan (day-by-day): `IMPLEMENTATION_PLAN.md`
- Execution protocol: `RUNBOOK.md`

## Priority Order
P0: end-to-end suggestion + jump workflow with HITL  
P1: distillation + registry + selection  
P2: governance + personalization  
P3: richer automation (prefill before submit, optional stretch)
