# REFERENCE_MAP.md

> Purpose: give Claude Code **on-demand** reference links and extraction guidance.
> Rule: do not import full external repos first. Read only the section needed for the current task.

## R1 — A-MEM (memory organization)
- Paper: https://arxiv.org/abs/2502.12110
- Repo: https://github.com/agiresearch/A-mem
- Use for:
  - memory note schema
  - note linking / relation edges
  - periodic consolidation/evolution logic
- Do NOT copy directly:
  - repo-specific storage internals

## R2 — MemSkill (memory skills evolution)
- Paper: https://arxiv.org/abs/2602.02474
- Use for:
  - controller -> select skill subset
  - executor -> apply selected memory/skill ops
  - designer -> analyze hard cases and evolve skills
- MVP mapping:
  - implement lightweight controller scoring + hard-case queue

## R3 — SkillWeaver (trajectory-to-skill + repair)
- Note: if official repo/paper is unavailable in runtime, use concept-level fallback from project notes.
- Use for:
  - extract candidate skills from successful traces
  - replay validation
  - failure-driven patching

## R4 — Voyager (experience->skill baseline)
- Paper: https://arxiv.org/abs/2305.16291
- Use for:
  - skill library growth pattern
  - reuse-over-regenerate policy

## Implementation policy
1. Every time a feature uses R1/R2/R3/R4, annotate PR/commit note:
   - `Ref used:`
   - `What adapted:`
   - `What changed for this project:`
2. Keep local abstraction first; no hard coupling to external codebase APIs.
3. If a reference is ambiguous, create a minimal experiment and decide by metric.
