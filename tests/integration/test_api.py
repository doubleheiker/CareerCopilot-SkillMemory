"""Integration checks for the FastAPI skeleton."""

from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_profile_load_endpoint() -> None:
    response = client.post("/profile/load")
    payload = response.json()
    assert response.status_code == 200
    assert payload["profile"]["preferred_cities"] == ["Beijing"]


def test_jobs_ingest_endpoint() -> None:
    response = client.post(
        "/jobs/ingest",
        json={"source": "dewu", "query": "Agent engineer", "limit": 2, "use_live_browser": False},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["jobs_ingested"] == 2
    assert len(payload["job_ids"]) == 2
    assert payload["job_ids"][0] == "dewu-9001"


def test_feedback_endpoint() -> None:
    response = client.post(
        "/feedback",
        json={
            "run_id": "run-1",
            "job_id": "dewu-1",
            "decision": "accept",
            "comment": "职位方向匹配",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["stored"] is True
    assert payload["profile_updates"] == ["记录用户偏好信号: accept"]


def test_runs_endpoint_returns_persisted_ingest_trajectory() -> None:
    ingest = client.post(
        "/jobs/ingest",
        json={"source": "boss_zhipin", "query": "Agent engineer", "limit": 2, "use_live_browser": False},
    )
    run_id = ingest.json()["run_id"]

    response = client.get(f"/runs/{run_id}")
    payload = response.json()
    assert response.status_code == 200
    assert payload["run"]["task_type"] == "jobs_ingest"
    assert payload["trajectory_summary"] == "boss_zhipin ingestion finished in fixture mode."
    assert len(payload["events"]) == 2


def test_match_and_suggestion_end_to_end() -> None:
    ingest = client.post(
        "/jobs/ingest",
        json={"source": "dewu", "query": "Agent engineer", "limit": 3, "use_live_browser": False},
    )
    job_ids = ingest.json()["job_ids"]

    match = client.post("/jobs/match", json={"job_ids": job_ids, "top_k": 2})
    match_payload = match.json()
    assert match.status_code == 200
    assert len(match_payload["recommendations"]) == 2
    assert match_payload["recommendations"][0]["title"] == "Agent Engineer Intern"
    assert match_payload["recommendations"][0]["location"] == "Beijing"

    suggestions = client.post("/suggestions/generate", json={"job_ids": job_ids, "top_k": 2})
    suggestion_payload = suggestions.json()
    assert suggestions.status_code == 200
    assert len(suggestion_payload["suggestions"]) == 2
    assert suggestion_payload["suggestions"][0]["url"].startswith("https://")
    assert "城市符合偏好" in suggestion_payload["suggestions"][0]["reason"]

    run = client.get(f"/runs/{suggestion_payload['run_id']}")
    run_payload = run.json()
    assert run.status_code == 200
    assert run_payload["trajectory_summary"] == "HITL suggestion generation finished with 2 suggestions."
    assert len(run_payload["events"]) == 2
