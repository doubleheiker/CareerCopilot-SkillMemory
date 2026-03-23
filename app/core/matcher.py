"""Profile-driven matching utilities for the P0 workflow."""

from __future__ import annotations

import re
from collections import Counter

from app.core.schemas import JobRecord, Recommendation, ScoreBreakdown, UserProfile


def build_recommendations(
    *,
    jobs: list[JobRecord],
    profile: UserProfile,
    accepted_titles: list[str],
    rejected_titles: list[str],
    top_k: int,
) -> list[Recommendation]:
    """Score jobs against the current profile and historical feedback."""
    accepted_tokens = Counter(_tokens(" ".join(accepted_titles)))
    rejected_tokens = Counter(_tokens(" ".join(rejected_titles)))

    scored: list[Recommendation] = []
    for job in jobs:
        title_tokens = _tokens(job.title)
        keyword_overlap = _overlap(title_tokens, profile.skill_keywords + profile.target_roles)
        title_role_overlap = _overlap(title_tokens, profile.target_roles)
        location_match = 1.0 if _contains(job.location, profile.preferred_cities) else 0.2
        internship_hint = 1.0 if _contains(job.title, profile.internship_types) else 0.4
        dislike_penalty = 0.4 if _contains(job.title, profile.disliked_traits) else 0.0

        accepted_bonus = 0.05 * sum(accepted_tokens[token] for token in title_tokens)
        rejected_penalty = 0.05 * sum(rejected_tokens[token] for token in title_tokens)

        semantic = min(1.0, 0.25 + 0.2 * keyword_overlap + 0.2 * title_role_overlap + accepted_bonus)
        preference = min(1.0, 0.2 + 0.45 * location_match + 0.2 * internship_hint)
        feasibility = min(1.0, 0.35 + 0.15 * (1.0 if job.url else 0.0))
        risk = min(1.0, dislike_penalty + rejected_penalty)

        total = semantic * 0.45 + preference * 0.35 + feasibility * 0.2 - risk * 0.3
        total = max(0.0, min(1.0, total))

        scored.append(
            Recommendation(
                job_id=job.job_id,
                title=job.title,
                company=job.company,
                location=job.location,
                url=job.url,
                total_score=round(total, 3),
                score_breakdown=ScoreBreakdown(
                    semantic=round(semantic, 3),
                    preference=round(preference, 3),
                    feasibility=round(feasibility, 3),
                    risk=round(risk, 3),
                ),
            )
        )

    scored.sort(key=lambda item: item.total_score, reverse=True)
    return scored[:top_k]


def build_suggestion_reason(recommendation: Recommendation, profile: UserProfile) -> str:
    """Create a concise Chinese reason string for HITL suggestions."""
    reasons: list[str] = []
    if _contains(recommendation.title, profile.target_roles):
        reasons.append("标题与目标岗位接近")
    if _contains(recommendation.title, profile.skill_keywords):
        reasons.append("包含画像关键词")
    if _contains(recommendation.location, profile.preferred_cities):
        reasons.append("城市符合偏好")
    if _contains(recommendation.title, profile.internship_types):
        reasons.append("实习类型匹配")
    if not reasons:
        reasons.append("综合分在当前候选中较高")
    return "；".join(reasons) + "。"


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_+-]+", text)]


def _overlap(tokens: list[str], candidates: list[str]) -> float:
    if not candidates:
        return 0.0
    candidate_tokens = set(_tokens(" ".join(candidates)))
    if not candidate_tokens:
        return 0.0
    hits = sum(1 for token in tokens if token in candidate_tokens)
    return min(1.0, hits / max(1, len(candidate_tokens)))


def _contains(text: str, patterns: list[str]) -> bool:
    lower_text = text.lower()
    return any(pattern.lower() in lower_text for pattern in patterns if pattern)
