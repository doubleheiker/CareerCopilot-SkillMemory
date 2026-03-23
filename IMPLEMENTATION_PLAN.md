# IMPLEMENTATION_PLAN.md (v4)

原则：先做轻量 MVP，再加可证明的能力增强；每一步都可演示、可验证。

## Reference usage rule (for Claude Code)
实现每个功能前，先去 `docs/REFERENCE_MAP.md` 查“对应参考编号（R1~R4）”，按需读取。
输出实现说明时必须附：
- `Ref used:` R?
- `Adapted idea:`
- `Project-specific change:`

---

## Week 1 — Build MVP spine

### D1: Repo & schemas
- setup repo / env / lint / tests skeleton
- define `Skill DSL` schema + `USER_PROFILE` schema + `MemoryNote` schema
- create FastAPI app skeleton and health endpoint
- initialize default Chinese profile and source config for 得物 / Boss直聘
- reference: R1 (memory schema)
- **acceptance**: schema validation tests pass + API boots

### D2: Trajectory + memory store
- implement trajectory logger (`jsonl`)
- implement memory note storage + link relation (`related_note_ids`)
- nightly/periodic summarization stub
- reference: R1
- **acceptance**: one run produces trajectories + linked memory notes

### D3: Matcher v1 + personalization
- semantic match + rule-based preference scoring
- load/update `USER_PROFILE.yaml`
- define feedback signal: `accept / reject / ignore`
- bootstrap profile defaults:
  - role: Agent engineer
  - city: Beijing
  - internship: summer intern / daily intern
  - keywords: LLM watermarking / agent memory / RAG
  - dislike: low output
- **acceptance**: top-k jobs with explainable score breakdown

### D4: HITL suggestion flow
- suggest jobs + return target page URL list (no auto submit)
- audit trail for user decisions (accept/reject/ignore)
- **acceptance**: end-to-end manual review loop works from API and demo UI

### D5: Distillation v1
- from repeated successful trajectories generate candidate skill JSON
- attach source trajectories and preconditions
- reference: R3 + R4
- note: skill families in MVP are `job_ingestion`, `matching`, `hitl_suggestion`
- **acceptance**: valid skills emitted from >=3 successful runs of the same task family

### D6: Registry + selector
- skill versioning/add/update/deprecate
- selector uses trigger + context similarity + historical score
- reference: R2 (controller-lite)
- **acceptance**: selected skills reduce avg steps vs no-skill baseline

### D7: Replay validator + patch loop
- replay candidate skill in sandbox task
- on fail: produce failure reason + patch suggestion
- reference: R3
- **acceptance**: at least 1 failed skill repaired and revalidated

---

## Week 2 — Depth & interview-grade evidence

### D8: Governance v1
- quality score, failure streak disable, cooldown
- **acceptance**: failing skill auto-disabled by policy

### D9: TTL / rollback / conflict handling
- TTL decay + rollback on regression + trigger conflict arbitration
- **acceptance**: synthetic regression test triggers rollback

### D10: Designer loop
- hard-case queue
- periodic designer proposes refine/new skill
- reference: R2 (designer)
- **acceptance**: hard-case transformed into improved skill candidate

### D11: Streamlit dashboard
- skills list, versions, score trends, memory links, audit log
- **acceptance**: one-page demo usable end-to-end

### D12: Interview evidence pack
- export representative runs, logs, screenshots, and architecture summary
- generate markdown report for demo walkthrough
- **acceptance**: report explains one complete run and one skill reuse case

### D13: Hardening
- bugfix + flaky handling + fallback sources
- finalize README + reproducible run script
- **acceptance**: clean dry-run from scratch

### D14: Packaging for interview
- architecture diagram
- resume bullets
- 3-min project pitch + Q&A prep
- **acceptance**: ready-to-present folder (`deliverables/`)

---

## Risk controls
1. Anti-bot / unstable websites -> fallback to stable company career pages.
2. LLM variance -> deterministic prompt templates + schema validation + replay tests.
3. Scope creep -> P0/P1 first, P2/P3 only after measurable baseline.
4. Over-coupling to external repos -> keep local abstractions and own interfaces.
5. Over-claiming "self-evolution" -> demo only what is actually implemented and replayable.

## Minimum success bar (2-week)
- HITL job suggestion flow works on 得物 + Boss直聘
- Memory->Skills loop demonstrated at least once (distill->validate->reuse)
- Governance policies trigger in at least one controlled test
- FastAPI backend + demo UI are both runnable
- Interview evidence pack is available and explainable
