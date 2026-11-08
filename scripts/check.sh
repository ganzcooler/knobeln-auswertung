#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pyright
uv run pytest
