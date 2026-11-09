"""Startet die lokale Web-UI auf 127.0.0.1."""

from __future__ import annotations

from pathlib import Path

import uvicorn

from ..runtime import build_service
from .app import create_app

LOCAL_HOST = "127.0.0.1"


def run_server(
    db_path: Path | None = None,
    *,
    scan_dir: Path | None = None,
    port: int = 8000,
    max_cost: float | None = None,
) -> None:
    service = build_service(db_path=db_path, scan_dir=scan_dir, max_cost=max_cost)
    uvicorn.run(create_app(service), host=LOCAL_HOST, port=port)
