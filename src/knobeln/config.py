"""Konfiguration aus CLI, Umgebung und .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_MODEL = "deepseek/deepseek-v4.1-flash"
DEFAULT_REASONING = "max"


class ConfigError(RuntimeError):
    pass


@dataclass
class Config:
    input_dir: Path
    output_csv: Path
    review_dir: Path
    model: str
    reasoning: str
    api_key: str | None
    reset: bool = False
    reprocess: bool = False
    no_cache: bool = False
    keep_input: bool = False
    dry_run: bool = False
    verbose: bool = False
    backup: bool = False
    cache_dir: Path = Path(".cache/knobeln")

    def require_api_key(self) -> str:
        if not self.api_key:
            raise ConfigError(
                "OPENROUTER_API_KEY fehlt. Bitte in .env eintragen "
                "(Vorlage: .env.example)."
            )
        return self.api_key


def build_config(
    *,
    input_dir: Path | None = None,
    output_csv: Path | None = None,
    review_dir: Path | None = None,
    model: str | None = None,
    reasoning: str | None = None,
    reset: bool = False,
    reprocess: bool = False,
    no_cache: bool = False,
    keep_input: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    backup: bool = False,
) -> Config:
    load_dotenv()
    return Config(
        input_dir=Path(
            input_dir
            or os.getenv("KNOBELN_INPUT")
            or "input"
        ),
        output_csv=Path(
            output_csv
            or os.getenv("KNOBELN_OUTPUT")
            or "auswertung.csv"
        ),
        review_dir=Path(review_dir or "review"),
        model=model or os.getenv("KNOBELN_MODEL") or DEFAULT_MODEL,
        reasoning=reasoning or os.getenv("KNOBELN_REASONING") or DEFAULT_REASONING,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        reset=reset,
        reprocess=reprocess,
        no_cache=no_cache,
        keep_input=keep_input,
        dry_run=dry_run,
        verbose=verbose,
        backup=backup,
    )
