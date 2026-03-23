"""Fixture-backed source adapters for Dewu and Boss Zhipin."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from app.core.ingestion.live_fetch import (
    build_url_with_query,
    fetch_dewu_job_posts_via_playwright,
    fetch_text_via_curl,
    live_fetch_enabled,
)
from app.core.schemas import (
    IngestionResult,
    JobIngestRequest,
    JobRecord,
    SourceDefinition,
    TrajectoryEvent,
)


class BaseSourceAdapter(ABC):
    """Base class for all source adapters."""

    source_name: str

    @abstractmethod
    def ingest(
        self,
        payload: JobIngestRequest,
        config: SourceDefinition,
        run_id: str,
        created_at: datetime,
        force_live: bool = False,
    ) -> IngestionResult:
        """Ingest jobs from a configured source."""

    def _fixture_path(self, config: SourceDefinition) -> Path:
        if not config.fixture_path:
            raise ValueError(f"source {config.name} missing fixture_path")
        return Path(config.fixture_path)

    def _base_events(
        self,
        *,
        created_at: datetime,
        source: str,
        mode: str,
        detail: str,
    ) -> list[TrajectoryEvent]:
        return [
            TrajectoryEvent(
                step_no=1,
                state="source_selected",
                action=f"adapter:{source}",
                outcome=mode,
                ts=created_at,
            ),
            TrajectoryEvent(
                step_no=2,
                state="ingestion_completed",
                action="parse_fixture",
                outcome=detail,
                ts=created_at,
            ),
        ]

    def _load_fixture_text(self, config: SourceDefinition) -> str:
        return self._fixture_path(config).read_text(encoding="utf-8")

    def _load_fixture_json(self, config: SourceDefinition) -> dict:
        with self._fixture_path(config).open("r", encoding="utf-8") as handle:
            return json.load(handle)


class DewuSourceAdapter(BaseSourceAdapter):
    """Adapter for the Dewu career page."""

    source_name = "dewu"

    def ingest(
        self,
        payload: JobIngestRequest,
        config: SourceDefinition,
        run_id: str,
        created_at: datetime,
        force_live: bool = False,
    ) -> IngestionResult:
        notes: list[str] = []
        mode = "fixture"
        records: list[dict] = []

        if live_fetch_enabled(force=force_live):
            try:
                live_url = build_url_with_query(config.start_urls[0], keywords=payload.query or "")
                response = fetch_dewu_job_posts_via_playwright(live_url)
                records = self._parse_live_response(response)
                if records:
                    mode = "live"
                    notes.append("live fetch succeeded via Playwright-captured signed request.")
                else:
                    notes.append("live fetch returned no parseable Dewu job records; fallback to fixture.")
            except Exception as exc:  # pragma: no cover - exercised only in live mode
                notes.append(f"live fetch failed: {exc}; fallback to fixture.")

        if not records:
            raw = self._load_fixture_json(config)
            records = raw.get("data", {}).get("records", [])

        jobs: list[JobRecord] = []
        for record in records[: payload.limit]:
            jobs.append(
                JobRecord(
                    job_id=f"{self.source_name}-{record['positionId']}",
                    source=self.source_name,
                    title=record["positionName"],
                    company="得物",
                    location=record["cityName"],
                    url=urljoin(config.start_urls[0], f"/detail/{record['positionId']}"),
                    raw_payload=record,
                    created_at=created_at,
                )
            )

        return IngestionResult(
            source=self.source_name,
            mode=mode,
            jobs=jobs,
            events=self._base_events(
                created_at=created_at,
                source=self.source_name,
                mode=mode,
                detail=f"parsed {len(jobs)} jobs",
            ),
            notes=notes
            + [
                "Dewu live fetch uses Playwright to capture the signed browser request, then falls back to fixture if needed.",
                f"entry_url={config.start_urls[0]}",
            ],
        )

    @staticmethod
    def _parse_live_response(payload: dict) -> list[dict]:
        """Normalize the live Dewu API response into fixture-like records."""
        records = []
        for item in payload.get("data", {}).get("job_post_list", []):
            city = item.get("city_info", {}) or {}
            city_name = city.get("name", "")
            if not city_name:
                city_list = item.get("city_list") or item.get("city_info_list_for_delivery") or []
                if city_list:
                    first_city = city_list[0] or {}
                    city_name = first_city.get("name", "")
            records.append(
                {
                    "positionId": item.get("id", ""),
                    "positionName": item.get("title", ""),
                    "cityName": city_name,
                }
            )
        return records


class BossZhipinSourceAdapter(BaseSourceAdapter):
    """Adapter for the Boss Zhipin job board."""

    source_name = "boss_zhipin"
    _card_pattern = re.compile(
        r'<li class="job-card"\s+data-job-id="(?P<job_id>[^"]+)"\s+'
        r'data-title="(?P<title>[^"]+)"\s+'
        r'data-company="(?P<company>[^"]+)"\s+'
        r'data-location="(?P<location>[^"]+)"\s+'
        r'data-url="(?P<url>[^"]+)">',
    )
    _live_card_pattern = re.compile(
        r'<a href="(?P<url>/job_detail/[^"]+)"[^>]*class="job-info"[^>]*>.*?'
        r'<p class="name">(?P<title>.*?)</p>.*?'
        r'<p class="job-text">\s*<span>(?P<location>.*?)</span>.*?</a>.*?'
        r'<a href="/gongsi/[^"]+"[^>]*class="user-info"[^>]*>.*?<span class="name">(?P<company>.*?)</span>',
        re.S,
    )

    def ingest(
        self,
        payload: JobIngestRequest,
        config: SourceDefinition,
        run_id: str,
        created_at: datetime,
        force_live: bool = False,
    ) -> IngestionResult:
        notes: list[str] = []
        mode = "fixture"
        jobs = []

        if live_fetch_enabled(force=force_live):
            try:
                html = fetch_text_via_curl(config.start_urls[0])
                jobs = self._parse_live_jobs(html=html, payload=payload, created_at=created_at)
                if jobs:
                    mode = "live"
                    notes.append("live fetch succeeded via curl.")
                else:
                    notes.append("live fetch produced no parseable Boss job cards; fallback to fixture.")
            except Exception as exc:  # pragma: no cover - exercised only in live mode
                notes.append(f"live fetch failed: {exc}; fallback to fixture.")

        if not jobs:
            html = self._load_fixture_text(config)
            jobs = self._parse_fixture_jobs(html=html, payload=payload, created_at=created_at)

        return IngestionResult(
            source=self.source_name,
            mode=mode,
            jobs=jobs,
            events=self._base_events(
                created_at=created_at,
                source=self.source_name,
                mode=mode,
                detail=f"parsed {len(jobs)} jobs",
            ),
            notes=notes
            + [
                "Boss adapter supports live HTML parsing from the landing page and falls back to fixture when needed.",
                f"entry_url={config.start_urls[0]}",
            ],
        )

    def _parse_fixture_jobs(
        self,
        *,
        html: str,
        payload: JobIngestRequest,
        created_at: datetime,
    ) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        for index, match in enumerate(self._card_pattern.finditer(html), start=1):
            if index > payload.limit:
                break
            jobs.append(
                JobRecord(
                    job_id=f"{self.source_name}-{match.group('job_id')}",
                    source=self.source_name,
                    title=match.group("title"),
                    company=match.group("company"),
                    location=match.group("location"),
                    url=urljoin("https://www.zhipin.com", match.group("url")),
                    raw_payload={
                        "job_id": match.group("job_id"),
                        "title": match.group("title"),
                        "company": match.group("company"),
                        "location": match.group("location"),
                    },
                    created_at=created_at,
                )
            )
        return jobs

    def _parse_live_jobs(
        self,
        *,
        html: str,
        payload: JobIngestRequest,
        created_at: datetime,
    ) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        for index, match in enumerate(self._live_card_pattern.finditer(html), start=1):
            if index > payload.limit:
                break
            title = _strip_html(match.group("title"))
            company = _strip_html(match.group("company"))
            location = _strip_html(match.group("location"))
            job_url = urljoin("https://www.zhipin.com", match.group("url"))
            job_id = match.group("url").split("/")[-1].replace(".html", "")
            jobs.append(
                JobRecord(
                    job_id=f"{self.source_name}-{job_id}",
                    source=self.source_name,
                    title=title,
                    company=company,
                    location=location,
                    url=job_url,
                    raw_payload={
                        "job_id": job_id,
                        "title": title,
                        "company": company,
                        "location": location,
                    },
                    created_at=created_at,
                )
            )
        return jobs


def _strip_html(value: str) -> str:
    """Remove nested tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", "", value)
    return " ".join(text.split())
