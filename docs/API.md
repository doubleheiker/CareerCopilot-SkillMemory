# API.md — MVP backend contract

## Goal
FastAPI is the required backend for the MVP. The API should expose the core agent workflow so the Streamlit demo and future automation can call the same backend.

## Design rules
- Single-user only in MVP
- API-first backend, UI-second
- Every major run gets a `run_id`
- User feedback is a first-class input signal
- Prefer stable JSON contracts over ad hoc text responses
- Default locale is Chinese

## Initial endpoint set

### `GET /health`
- Purpose: service health check
- Response:
  - `status`
  - `version`

### `POST /profile/load`
- Purpose: load `USER_PROFILE.yaml`
- Response:
  - `profile`

### `POST /profile/update`
- Purpose: apply explicit profile changes or derived preference updates
- Request:
  - `patch`
  - `reason`
- Response:
  - `profile`
  - `updated_fields`

### `POST /jobs/ingest`
- Purpose: ingest jobs from one source adapter
- Request:
  - `source`
  - `query`
  - `limit`
  - `use_live_browser`
- Response:
  - `run_id`
  - `source`
  - `jobs_ingested`
  - `job_ids`
  - `errors`

### `POST /jobs/match`
- Purpose: score stored jobs against the current user profile
- Request:
  - `job_ids` or filter
  - `top_k`
- Response:
  - `run_id`
  - `recommendations`
  - `score_breakdown`

### `POST /suggestions/generate`
- Purpose: produce HITL suggestions with explanations and clickable URLs
- Request:
  - `job_ids`
  - `top_k`
- Response:
  - `run_id`
  - `suggestions`
  - `reasons`
  - `urls`

### `POST /feedback`
- Purpose: record user decision for a recommendation
- Request:
  - `run_id`
  - `job_id`
  - `decision` (`accept | reject | ignore`)
  - `comment`
- Response:
  - `stored`
  - `memory_updates`
  - `profile_updates`

### `GET /runs/{run_id}`
- Purpose: inspect run status and trace summary
- Response:
  - `run`
  - `trajectory_summary`
  - `events`

### `POST /skills/distill`
- Purpose: distill candidate skills from repeated successful runs
- Request:
  - `run_ids`
  - `skill_family`
- Response:
  - `candidate_skills`

### `POST /skills/validate`
- Purpose: replay and validate a candidate skill
- Request:
  - `skill_id`
  - `version`
- Response:
  - `validation_status`
  - `evidence`
  - `patch_suggestion`

### `GET /skills`
- Purpose: list skills with version and status
- Response:
  - `skills`

## Source adapter note
MVP should treat each source as an adapter with a common contract:
- input: source config + query context
- output: normalized `JobRecord`

Recommended priority:
1. 得物 career page
2. Boss直聘 with stable selectors
3. local replay fixtures for flaky sources

## Non-goals for API v1
- auth
- multi-user routing
- auto-apply
- async distributed workers
- public API hardening
