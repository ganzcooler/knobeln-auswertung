"""Baut den Anwendungskern für Web-UI und CLI."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from .application import KnobelnService
from .llm.cache import LLMCache
from .llm.client import OpenRouterClient
from .store import SQLiteStore

DEFAULT_DB = Path("knobeln.db")
DEFAULT_SCANS = Path("data/scans")
DEFAULT_MODEL = "deepseek/deepseek-v4.1-flash"
DEFAULT_REASONING = "medium"


def build_service(
    *,
    db_path: Path | None = None,
    scan_dir: Path | None = None,
    with_llm: bool = True,
    max_cost: float | None = None,
    model: str | None = None,
    reasoning: str | None = None,
) -> KnobelnService:
    load_dotenv()
    store = SQLiteStore(db_path or DEFAULT_DB)
    client = None
    api_key = os.getenv("OPENROUTER_API_KEY")
    if with_llm and api_key:
        client = OpenRouterClient(
            api_key=api_key,
            model=model or os.getenv("KNOBELN_MODEL") or DEFAULT_MODEL,
            reasoning=reasoning or os.getenv("KNOBELN_REASONING") or DEFAULT_REASONING,
            cache=LLMCache(Path(".cache/knobeln")),
        )
    return KnobelnService(
        store,
        llm_client=client,
        scan_dir=scan_dir or DEFAULT_SCANS,
        max_cost=max_cost,
    )
