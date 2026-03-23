"""Local file-backed persistence used by the MVP skeleton."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml

from app.core.schemas import (
    IngestionResult,
    JobRecord,
    MemoryNote,
    Recommendation,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
    RunDetailResponse,
    RunSummary,
    SkillRecord,
    TrajectoryEvent,
    UserFeedbackRequest,
    UserProfile,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "configs"
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
STUB_DIR = DATA_DIR / "stub"
PROFILE_PATH = CONFIG_DIR / "USER_PROFILE.yaml"
SKILL_STUB_PATH = STUB_DIR / "skills.json"
JOBS_PATH = STUB_DIR / "jobs.jsonl"
RECOMMENDATIONS_PATH = STUB_DIR / "recommendations.jsonl"


def _ensure_dirs() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STUB_DIR.mkdir(parents=True, exist_ok=True)


def load_user_profile() -> UserProfile:
    """Load the single-user profile from YAML."""
    with PROFILE_PATH.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return UserProfile.model_validate(payload)


def build_profile_update_response(payload: ProfileUpdateRequest) -> ProfileUpdateResponse:
    """Build a deterministic response without mutating disk yet."""
    profile = load_user_profile()
    merged = profile.model_dump()
    merged.update(payload.patch)
    updated_profile = UserProfile.model_validate(merged)
    return ProfileUpdateResponse(
        profile=updated_profile,
        updated_fields=sorted(payload.patch.keys()),
    )


def load_jobs(job_ids: list[str]) -> list[JobRecord]:
    """Load the latest stored job records for the given job ids."""
    _ensure_dirs()
    if not JOBS_PATH.exists():
        return []

    latest_by_id: dict[str, JobRecord] = {}
    with JOBS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            job = JobRecord.model_validate_json(line)
            latest_by_id[job.job_id] = job

    if not job_ids:
        return list(latest_by_id.values())
    return [latest_by_id[job_id] for job_id in job_ids if job_id in latest_by_id]


def persist_ingestion_result(
    run_id: str,
    payload: dict[str, object],
    result: IngestionResult,
    created_at: datetime,
) -> list[JobRecord]:
    """Write normalized jobs and a run log."""
    _ensure_dirs()
    with JOBS_PATH.open("a", encoding="utf-8") as handle:
        for job in result.jobs:
            handle.write(job.model_dump_json(ensure_ascii=False) + "\n")

    run_path = LOG_DIR / f"{run_id}.json"
    with run_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "run_id": run_id,
                "task_type": "jobs_ingest",
                "status": "completed",
                "started_at": created_at.isoformat(),
                "ended_at": created_at.isoformat(),
                "payload": payload,
                "jobs": [job.model_dump(mode="json") for job in result.jobs],
                "events": [event.model_dump(mode="json") for event in result.events],
                "notes": result.notes,
                "source": result.source,
                "mode": result.mode,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )
    return result.jobs


def persist_feedback(payload: UserFeedbackRequest) -> dict[str, list[str] | str]:
    """Write one feedback event and return derived preference updates."""
    _ensure_dirs()
    note = MemoryNote(
        note_id=str(uuid4()),
        note_type="feedback",
        content=f"用户对 {payload.job_id} 的反馈为 {payload.decision}",
        source_run_id=payload.run_id,
        quality_score=0.8,
        created_at=datetime.now(timezone.utc),
    )
    target = STUB_DIR / "feedback.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(note.model_dump_json(ensure_ascii=False) + "\n")
    run_path = LOG_DIR / f"{payload.run_id}.json"
    if run_path.exists():
        with run_path.open("r", encoding="utf-8") as handle:
            run_payload = json.load(handle)
        events = run_payload.setdefault("events", [])
        step_no = len(events) + 1
        events.append(
            TrajectoryEvent(
                step_no=step_no,
                state="feedback_recorded",
                action=f"decision:{payload.decision}",
                outcome=payload.job_id,
                ts=datetime.now(timezone.utc),
            ).model_dump(mode="json")
        )
        notes = run_payload.setdefault("notes", [])
        notes.append(f"feedback:{payload.job_id}:{payload.decision}")
        with run_path.open("w", encoding="utf-8") as handle:
            json.dump(run_payload, handle, ensure_ascii=False, indent=2)
    return {
        "memory_update": f"新增 feedback memory note: {note.note_id}",
        "profile_updates": [f"记录用户偏好信号: {payload.decision}"],
    }


def load_feedback_titles(decision: str) -> list[str]:
    """Load feedback-linked job titles for one decision type."""
    _ensure_dirs()
    if not (STUB_DIR / "feedback.jsonl").exists():
        return []

    job_index = {job.job_id: job.title for job in load_jobs([])}
    titles: list[str] = []
    with (STUB_DIR / "feedback.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            note = MemoryNote.model_validate_json(line)
            if f"反馈为 {decision}" in note.content and note.source_run_id:
                # feedback note content stores the job id in the text prefix
                parts = note.content.split()
                for part in parts:
                    if part in job_index:
                        titles.append(job_index[part])
    return titles


def persist_match_run(
    *,
    run_id: str,
    payload: dict[str, object],
    recommendations: list[Recommendation],
    created_at: datetime,
) -> None:
    """Persist a matching run with recommendation details."""
    _ensure_dirs()
    with RECOMMENDATIONS_PATH.open("a", encoding="utf-8") as handle:
        for item in recommendations:
            handle.write(item.model_dump_json(ensure_ascii=False) + "\n")

    run_path = LOG_DIR / f"{run_id}.json"
    events = [
        TrajectoryEvent(
            step_no=1,
            state="matching_started",
            action="load_jobs_and_profile",
            outcome=str(len(payload.get("job_ids", []))),
            ts=created_at,
        ).model_dump(mode="json"),
        TrajectoryEvent(
            step_no=2,
            state="matching_completed",
            action="score_jobs",
            outcome=str(len(recommendations)),
            ts=created_at,
        ).model_dump(mode="json"),
    ]
    with run_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "run_id": run_id,
                "task_type": "jobs_match",
                "status": "completed",
                "started_at": created_at.isoformat(),
                "ended_at": created_at.isoformat(),
                "payload": payload,
                "recommendations": [item.model_dump(mode="json") for item in recommendations],
                "events": events,
                "notes": ["profile-driven matching complete"],
                "mode": "local",
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )


def persist_suggestion_run(
    *,
    run_id: str,
    payload: dict[str, object],
    suggestions: list[dict[str, str]],
    created_at: datetime,
) -> None:
    """Persist a suggestion-generation run."""
    _ensure_dirs()
    run_path = LOG_DIR / f"{run_id}.json"
    events = [
        TrajectoryEvent(
            step_no=1,
            state="suggestion_started",
            action="load_recommendations",
            outcome=str(len(payload.get("job_ids", []))),
            ts=created_at,
        ).model_dump(mode="json"),
        TrajectoryEvent(
            step_no=2,
            state="suggestion_completed",
            action="build_hitl_suggestions",
            outcome=str(len(suggestions)),
            ts=created_at,
        ).model_dump(mode="json"),
    ]
    with run_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "run_id": run_id,
                "task_type": "suggestions_generate",
                "status": "completed",
                "started_at": created_at.isoformat(),
                "ended_at": created_at.isoformat(),
                "payload": payload,
                "suggestions": suggestions,
                "events": events,
                "notes": ["HITL suggestion list generated"],
                "mode": "local",
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )


def make_placeholder_run(run_id: str) -> RunDetailResponse:
    """Return a stored run detail when available, otherwise a placeholder."""
    run_path = LOG_DIR / f"{run_id}.json"
    if run_path.exists():
        with run_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        summary = _build_run_summary(payload)
        return RunDetailResponse(
            run=RunSummary(
                run_id=payload["run_id"],
                task_type=payload["task_type"],
                status=payload["status"],
                started_at=datetime.fromisoformat(payload["started_at"]),
                ended_at=datetime.fromisoformat(payload["ended_at"]),
                notes="; ".join(payload.get("notes", [])) or None,
            ),
            trajectory_summary=summary,
            events=[TrajectoryEvent.model_validate(event) for event in payload.get("events", [])],
        )

    now = datetime.now(timezone.utc)
    return RunDetailResponse(
        run=RunSummary(
            run_id=run_id,
            task_type="placeholder",
            status="completed",
            started_at=now,
            ended_at=now,
            notes="初始骨架返回的占位 run 详情。",
        ),
        trajectory_summary="已完成占位 run，后续将接入真实轨迹日志。",
        events=[
            TrajectoryEvent(
                step_no=1,
                state="start",
                action="initialize-run",
                outcome="ok",
                ts=now,
            ),
            TrajectoryEvent(
                step_no=2,
                state="end",
                action="return-placeholder",
                outcome="ok",
                ts=now,
            ),
        ],
    )


def list_skills() -> list[SkillRecord]:
    """Load stored skills from a local JSON stub file."""
    _ensure_dirs()
    if not SKILL_STUB_PATH.exists():
        return []
    with SKILL_STUB_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [SkillRecord.model_validate(item) for item in payload]


def _build_run_summary(payload: dict[str, object]) -> str:
    """Build a human-readable summary for a persisted run."""
    task_type = payload.get("task_type")
    if task_type == "jobs_ingest":
        return f"{payload.get('source')} ingestion finished in {payload.get('mode')} mode."
    if task_type == "jobs_match":
        recommendations = payload.get("recommendations", [])
        return f"matching finished with {len(recommendations)} recommendations."
    if task_type == "suggestions_generate":
        suggestions = payload.get("suggestions", [])
        return f"HITL suggestion generation finished with {len(suggestions)} suggestions."
    return "stored run loaded."
