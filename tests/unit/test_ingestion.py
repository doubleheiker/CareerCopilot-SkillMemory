"""Unit tests for source adapter parsing."""

from datetime import datetime, timezone

from app.core.ingestion.manager import SourceManager
from app.core.ingestion.adapters import BossZhipinSourceAdapter, DewuSourceAdapter
from app.core.schemas import JobIngestRequest


def test_dewu_adapter_parses_fixture() -> None:
    manager = SourceManager()
    result = manager.ingest(
        JobIngestRequest(source="dewu", limit=2),
        run_id="run-1",
        created_at=datetime.now(timezone.utc),
    )
    assert result.mode == "fixture"
    assert [job.title for job in result.jobs] == ["Agent Engineer Intern", "RAG Algorithm Intern"]


def test_boss_adapter_parses_fixture() -> None:
    manager = SourceManager()
    result = manager.ingest(
        JobIngestRequest(source="boss_zhipin", limit=2),
        run_id="run-2",
        created_at=datetime.now(timezone.utc),
    )
    assert result.jobs[0].company == "示例科技"
    assert result.jobs[1].location == "Beijing"


def test_boss_live_parser_extracts_jobs_from_html() -> None:
    html = """
    <li>
      <div class="sub-li">
        <a href="/job_detail/abc123.html" ka="index_rcmd_job_1" class="job-info" target="_blank">
          <p class="name">Agent Engineer Intern</p>
          <p class="job-text"><span>北京</span><span>在校/应届</span></p>
        </a>
        <a href="/gongsi/demo.html" ka="index_rcmd_company_1" class="user-info" target="_blank">
          <p><span class="name">得物技术团队</span></p>
        </a>
      </div>
    </li>
    """
    adapter = BossZhipinSourceAdapter()
    jobs = adapter._parse_live_jobs(
        html=html,
        payload=JobIngestRequest(source="boss_zhipin", limit=1),
        created_at=datetime.now(timezone.utc),
    )
    assert jobs[0].job_id == "boss_zhipin-abc123"
    assert jobs[0].title == "Agent Engineer Intern"
    assert jobs[0].company == "得物技术团队"


def test_dewu_live_parser_returns_empty_when_only_app_shell() -> None:
    payload = {"code": 0, "data": {"job_post_list": []}}
    records = DewuSourceAdapter._parse_live_response(payload)
    assert records == []


def test_dewu_live_response_parser_extracts_records() -> None:
    payload = {
        "code": 0,
        "data": {
            "job_post_list": [
                {
                    "id": "123",
                    "title": "Agent Engineer Intern",
                    "city_info": {"name": "北京"},
                }
            ]
        },
    }
    records = DewuSourceAdapter._parse_live_response(payload)
    assert records == [
        {
            "positionId": "123",
            "positionName": "Agent Engineer Intern",
            "cityName": "北京",
        }
    ]
