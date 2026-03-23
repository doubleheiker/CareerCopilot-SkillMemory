"""Source adapter orchestration."""

from __future__ import annotations

from datetime import datetime

from app.core.config import load_source_catalog
from app.core.ingestion.adapters import BossZhipinSourceAdapter, DewuSourceAdapter
from app.core.schemas import IngestionResult, JobIngestRequest


class SourceManager:
    """Load source config and dispatch to the correct adapter."""

    def __init__(self) -> None:
        self.catalog = load_source_catalog()
        self.adapters = {
            "dewu": DewuSourceAdapter(),
            "boss_zhipin": BossZhipinSourceAdapter(),
        }

    def ingest(
        self,
        payload: JobIngestRequest,
        *,
        run_id: str,
        created_at: datetime,
        force_live: bool = False,
    ) -> IngestionResult:
        if payload.source not in self.catalog:
            raise ValueError(f"unknown source: {payload.source}")
        if payload.source not in self.adapters:
            raise ValueError(f"adapter not implemented: {payload.source}")

        config = self.catalog[payload.source]
        if not config.enabled:
            raise ValueError(f"source disabled: {payload.source}")

        adapter = self.adapters[payload.source]
        return adapter.ingest(
            payload=payload,
            config=config,
            run_id=run_id,
            created_at=created_at,
            force_live=force_live,
        )
