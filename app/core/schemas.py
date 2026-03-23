"""Pydantic schemas for the MVP backend contract."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DecisionType = Literal["accept", "reject", "ignore"]


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str
    version: str


class UserProfile(BaseModel):
    """Single-user preference profile used for matching."""

    profile_id: str
    locale: str = "zh-CN"
    target_roles: list[str]
    preferred_cities: list[str]
    internship_types: list[str]
    skill_keywords: list[str]
    disliked_traits: list[str]
    notes: list[str] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    """Request to update fields in the user profile."""

    patch: dict[str, Any]
    reason: str


class ProfileUpdateResponse(BaseModel):
    """Response after updating the user profile."""

    profile: UserProfile
    updated_fields: list[str]


class JobIngestRequest(BaseModel):
    """Request to ingest jobs from a single source."""

    source: str
    query: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    use_live_browser: bool = False


class JobIngestResponse(BaseModel):
    """Ingestion response summary."""

    run_id: str
    source: str
    jobs_ingested: int
    job_ids: list[str]
    errors: list[str]


class JobMatchRequest(BaseModel):
    """Request to match jobs against the current profile."""

    job_ids: list[str]
    top_k: int = Field(default=5, ge=1, le=20)


class ScoreBreakdown(BaseModel):
    """Explainable score parts for one recommendation."""

    semantic: float
    preference: float
    feasibility: float
    risk: float


class Recommendation(BaseModel):
    """Recommendation result with explainability payload."""

    job_id: str
    title: str
    company: str
    location: str
    url: str
    total_score: float
    score_breakdown: ScoreBreakdown


class JobMatchResponse(BaseModel):
    """Response with matched recommendations."""

    run_id: str
    recommendations: list[Recommendation]


class SuggestionGenerateRequest(BaseModel):
    """Request to generate HITL suggestions."""

    job_ids: list[str]
    top_k: int = Field(default=5, ge=1, le=20)


class SuggestionRecord(BaseModel):
    """Suggested job with explanation and URL."""

    job_id: str
    title: str
    company: str
    location: str
    reason: str
    url: str


class SuggestionGenerateResponse(BaseModel):
    """Response for suggestion generation."""

    run_id: str
    suggestions: list[SuggestionRecord]


class UserFeedbackRequest(BaseModel):
    """Request to record user feedback on one suggestion."""

    run_id: str
    job_id: str
    decision: DecisionType
    comment: str | None = None


class UserFeedbackResponse(BaseModel):
    """Response after persisting feedback."""

    stored: bool
    memory_updates: list[str]
    profile_updates: list[str]


class TrajectoryEvent(BaseModel):
    """One stored event in a run trajectory."""

    step_no: int
    state: str
    action: str
    outcome: str
    error: str | None = None
    ts: datetime


class RunSummary(BaseModel):
    """Metadata for one run."""

    run_id: str
    task_type: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    notes: str | None = None


class RunDetailResponse(BaseModel):
    """Detailed run response."""

    run: RunSummary
    trajectory_summary: str
    events: list[TrajectoryEvent]


class SkillRecord(BaseModel):
    """Reusable skill package distilled from successful trajectories."""

    skill_id: str
    version: int
    status: str
    trigger: str
    risk_level: str
    ttl_days: int
    score: float
    name: str
    description: str
    inputs: dict[str, Any]
    steps: list[str]
    expected_output: dict[str, Any]
    constraints: list[str]
    source_run_ids: list[str]
    validation_status: str


class SkillDistillRequest(BaseModel):
    """Request to distill a new candidate skill."""

    run_ids: list[str]
    skill_family: Literal["job_ingestion", "matching", "hitl_suggestion"]


class SkillDistillResponse(BaseModel):
    """Response with candidate skills."""

    candidate_skills: list[SkillRecord]


class SkillValidateRequest(BaseModel):
    """Request to validate a candidate skill."""

    skill_id: str
    version: int


class SkillValidateEvidence(BaseModel):
    """Structured evidence item emitted by validation."""

    type: str
    detail: str


class SkillValidateResponse(BaseModel):
    """Validation result for a skill."""

    validation_status: str
    evidence: list[SkillValidateEvidence]
    patch_suggestion: str


class SkillListResponse(BaseModel):
    """Response containing stored skills."""

    skills: list[SkillRecord]


class MemoryNote(BaseModel):
    """Normalized memory note schema."""

    note_id: str
    note_type: Literal["feedback", "preference", "summary", "observation"]
    content: str
    related_note_ids: list[str] = Field(default_factory=list)
    source_run_id: str | None = None
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime


class JobRecord(BaseModel):
    """Normalized job record emitted by a source adapter."""

    job_id: str
    source: str
    title: str
    company: str
    location: str
    url: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SourceDefinition(BaseModel):
    """Source adapter configuration loaded from YAML."""

    name: str
    kind: str
    enabled: bool = True
    priority: str
    start_urls: list[str]
    notes: list[str] = Field(default_factory=list)
    fixture_path: str | None = None


class IngestionResult(BaseModel):
    """Adapter ingestion result with jobs and trajectory evidence."""

    source: str
    mode: str
    jobs: list[JobRecord]
    events: list[TrajectoryEvent]
    notes: list[str] = Field(default_factory=list)
