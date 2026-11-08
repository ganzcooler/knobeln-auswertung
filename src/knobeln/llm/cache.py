"""Kleiner JSON-Cache für LLM-Antworten."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class LLMCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    @staticmethod
    def make_key(
        *,
        bogen_id: str,
        model: str,
        prompt_version: str,
        reasoning: str,
    ) -> str:
        raw = f"{bogen_id}|{model}|{prompt_version}|{reasoning}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self._path(key)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, path)
