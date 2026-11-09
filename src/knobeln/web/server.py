"""Startet die lokale Web-UI auf 127.0.0.1."""

from __future__ import annotations

from pathlib import Path

import uvicorn

from ..application import KnobelnService
from ..store import SQLiteStore
from .app import create_app

DEFAULT_DB = Path("knobeln.db")
LOCAL_HOST = "127.0.0.1"


def run_server(
    db_path: Path | None = None,
    *,
    port: int = 8000,
) -> None:
    path = Path(db_path) if db_path is not None else DEFAULT_DB
    service = KnobelnService(SQLiteStore(path))
    uvicorn.run(create_app(service), host=LOCAL_HOST, port=port)
