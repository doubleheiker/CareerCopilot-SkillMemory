"""Configuration loaders for local YAML config files."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.core.schemas import SourceDefinition

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "configs"
SOURCES_PATH = CONFIG_DIR / "sources.yaml"


def load_source_catalog() -> dict[str, SourceDefinition]:
    """Load source adapter definitions from YAML."""
    with SOURCES_PATH.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    sources = payload.get("sources", {})
    catalog: dict[str, SourceDefinition] = {}
    for name, config in sources.items():
        catalog[name] = SourceDefinition.model_validate({"name": name, **config})
    return catalog
