# MILESTONES.md — 2-week milestones

## M0 — Setup & Schema
- repo/env 初始化
- Skill DSL + USER_PROFILE + MemoryNote schema
- FastAPI skeleton
- 验收：schema tests pass + API health endpoint works

## M1 — MVP主链路跑通
- 抓取 -> 匹配 -> 建议+跳转(HITL) -> 轨迹记录
- 用户反馈 accept / reject / ignore 可写入
- 验收：2+ 稳定来源可用，端到端可演示

## M2 — Memory→Skills闭环
- distill candidate skill
- registry + selector
- replay validator + patch
- 验收：至少 1 个技能完成“生成-验证-复用”

## M3 — Governance与个性化
- quality score / disable / TTL / rollback / conflict
- profile更新驱动排序变化
- 验收：策略至少触发 1 次并有证据

## M4 — Demo与交付
- demo, report, interview materials
- 可复现运行脚本
- 验收：deliverables 可直接用于面试讲解
