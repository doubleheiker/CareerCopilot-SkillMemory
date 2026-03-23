"""Schema validation tests for the MVP skeleton."""

from app.core.schemas import JobIngestRequest, SkillDistillRequest, UserProfile


def test_user_profile_defaults_loadable() -> None:
    profile = UserProfile(
        profile_id="u1",
        target_roles=["Agent engineer"],
        preferred_cities=["Beijing"],
        internship_types=["summer intern"],
        skill_keywords=["RAG"],
        disliked_traits=["low output"],
    )
    assert profile.locale == "zh-CN"


def test_job_ingest_request_limit_validation() -> None:
    request = JobIngestRequest(source="dewu", limit=3)
    assert request.limit == 3


def test_skill_family_restricted() -> None:
    skill = SkillDistillRequest(run_ids=["r1", "r2", "r3"], skill_family="matching")
    assert skill.skill_family == "matching"
