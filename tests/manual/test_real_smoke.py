"""Kostenpflichtiger Smoke-Test gegen das echte Modell."""

from __future__ import annotations

import os
import subprocess

import pytest
from dotenv import load_dotenv


@pytest.mark.manual
def test_real_model_smoke() -> None:
    load_dotenv(".env")
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY fehlt")

    result = subprocess.run(
        ["./scripts/smoke_test.sh"],
        text=True,
        capture_output=True,
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0
