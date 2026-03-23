"""API route definitions for the MVP backend contract."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.ingestion.manager import SourceManager
from app.core.matcher import build_recommendations, build_suggestion_reason
from app.core.schemas import (
    HealthResponse,
    JobIngestRequest,
    JobIngestResponse,
    JobMatchRequest,
    JobMatchResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
    RunDetailResponse,
    SkillDistillRequest,
    SkillDistillResponse,
    SkillListResponse,
    SkillRecord,
    SkillValidateRequest,
    SkillValidateResponse,
    SuggestionGenerateRequest,
    SuggestionGenerateResponse,
    UserFeedbackRequest,
    UserFeedbackResponse,
    UserProfile,
)
from app.core.store import (
    build_profile_update_response,
    list_skills,
    load_feedback_titles,
    load_jobs,
    load_user_profile,
    make_placeholder_run,
    persist_feedback,
    persist_ingestion_result,
    persist_match_run,
    persist_suggestion_run,
)


class ProfileLoadResponse(BaseModel):
    """Response wrapper for profile load endpoint."""

    profile: UserProfile


router = APIRouter()
source_manager = SourceManager()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a basic health payload."""
    return HealthResponse(status="ok", version="0.1.0")


@router.post("/profile/load", response_model=ProfileLoadResponse)
def load_profile() -> ProfileLoadResponse:
    """Load the default single-user profile from disk."""
    return ProfileLoadResponse(profile=load_user_profile())


@router.post("/profile/update", response_model=ProfileUpdateResponse)
def update_profile(payload: ProfileUpdateRequest) -> ProfileUpdateResponse:
    """Echo a profile update request into a deterministic response stub."""
    return build_profile_update_response(payload)


@router.post("/jobs/ingest", response_model=JobIngestResponse)
def ingest_jobs(payload: JobIngestRequest) -> JobIngestResponse:
    """Ingest jobs via the configured source adapter and persist trajectory logs."""
    run_id = str(uuid4())
    now = datetime.now(timezone.utc)
    result = source_manager.ingest(
        payload=payload,
        run_id=run_id,
        created_at=now,
        force_live=payload.use_live_browser,
    )
    jobs = persist_ingestion_result(
        run_id=run_id,
        payload=payload.model_dump(),
        result=result,
        created_at=now,
    )
    return JobIngestResponse(
        run_id=run_id,
        source=payload.source,
        jobs_ingested=len(jobs),
        job_ids=[job.job_id for job in jobs],
        errors=[],
    )


@router.post("/jobs/match", response_model=JobMatchResponse)
def match_jobs(payload: JobMatchRequest) -> JobMatchResponse:
    """Score persisted jobs against the current user profile."""
    run_id = str(uuid4())
    now = datetime.now(timezone.utc)
    jobs = load_jobs(payload.job_ids)
    profile = load_user_profile()
    recommendations = build_recommendations(
        jobs=jobs,
        profile=profile,
        accepted_titles=load_feedback_titles("accept"),
        rejected_titles=load_feedback_titles("reject"),
        top_k=payload.top_k,
    )
    persist_match_run(
        run_id=run_id,
        payload=payload.model_dump(),
        recommendations=recommendations,
        created_at=now,
    )
    return JobMatchResponse(run_id=run_id, recommendations=recommendations)


@router.post("/suggestions/generate", response_model=SuggestionGenerateResponse)
def generate_suggestions(payload: SuggestionGenerateRequest) -> SuggestionGenerateResponse:
    """Generate HITL suggestions with explanations and clickable URLs."""
    run_id = str(uuid4())
    now = datetime.now(timezone.utc)
    profile = load_user_profile()
    jobs = load_jobs(payload.job_ids)
    recommendations = build_recommendations(
        jobs=jobs,
        profile=profile,
        accepted_titles=load_feedback_titles("accept"),
        rejected_titles=load_feedback_titles("reject"),
        top_k=payload.top_k,
    )
    suggestions = []
    for item in recommendations:
        suggestions.append(
            {
                "job_id": item.job_id,
                "title": item.title,
                "company": item.company,
                "location": item.location,
                "reason": build_suggestion_reason(item, profile),
                "url": item.url,
            }
        )
    persist_suggestion_run(
        run_id=run_id,
        payload=payload.model_dump(),
        suggestions=suggestions,
        created_at=now,
    )
    return SuggestionGenerateResponse(run_id=run_id, suggestions=suggestions)


@router.post("/feedback", response_model=UserFeedbackResponse)
def record_feedback(payload: UserFeedbackRequest) -> UserFeedbackResponse:
    """Record user feedback and emit deterministic placeholder updates."""
    record = persist_feedback(payload)
    return UserFeedbackResponse(
        stored=True,
        memory_updates=[record["memory_update"]],
        profile_updates=record["profile_updates"],
    )


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str) -> RunDetailResponse:
    """Return a placeholder run detail summary."""
    return make_placeholder_run(run_id)


@router.post("/skills/distill", response_model=SkillDistillResponse)
def distill_skills(payload: SkillDistillRequest) -> SkillDistillResponse:
    """Produce candidate skills from repeated successful run ids."""
    candidate = SkillRecord(
        skill_id=str(uuid4()),
        version=1,
        status="candidate",
        trigger=f"{payload.skill_family}:repeated-success",
        risk_level="low",
        ttl_days=14,
        score=0.5,
        name=f"{payload.skill_family}_candidate",
        description="从重复成功轨迹中蒸馏的候选技能。",
        inputs={"run_ids": payload.run_ids},
        steps=[
            "读取关联轨迹",
            "提炼稳定步骤与前置条件",
            "生成技能说明与输出约束",
        ],
        expected_output={"format": "skill-package"},
        constraints=["single-user", "hitl-first"],
        source_run_ids=payload.run_ids,
        validation_status="pending",
    )
    return SkillDistillResponse(candidate_skills=[candidate])


@router.post("/skills/validate", response_model=SkillValidateResponse)
def validate_skill(payload: SkillValidateRequest) -> SkillValidateResponse:
    """Return a placeholder validation result for a candidate skill."""
    return SkillValidateResponse(
        validation_status="pending",
        evidence=[
            {
                "type": "replay-plan",
                "detail": f"Skill {payload.skill_id} v{payload.version} queued for replay validation.",
            }
        ],
        patch_suggestion="先补齐同任务族的 3 条成功轨迹，再执行重放验证。",
    )


@router.get("/skills", response_model=SkillListResponse)
def get_skills() -> SkillListResponse:
    """List stored skills from the local JSON stub store."""
    return SkillListResponse(skills=list_skills())
