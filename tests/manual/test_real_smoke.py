"""Kostenpflichtiger Smoke-Test gegen das echte Modell."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from knobeln.application import KnobelnService
from knobeln.llm.client import OpenRouterClient
from knobeln.store import SQLiteStore

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


@pytest.mark.manual
def test_real_model_smoke(tmp_path: Path) -> None:
    load_dotenv(".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY fehlt")

    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=OpenRouterClient(
            api_key=api_key,
            model="deepseek/deepseek-v4.1-flash",
            reasoning="low",
        ),
        scan_dir=tmp_path / "scans",
        max_cost=0.15,
    )
    turnier = service.create_turnier("Smoke")
    durchgang = service.create_durchgang(turnier.id, 1)
    service.import_scan(
        dateiname="img1.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
    )

    assert service.process_pending_jobs() == 1
    bogen = service.list_bogen(durchgang.id)[0]
    assert bogen.job_status == "fertig"
    assert len(service.list_gruppen_for_bogen(bogen.id)) == 4
