#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

fail=0

if command -v uv >/dev/null 2>&1; then
  echo "uv: $(uv --version)"
else
  echo "uv: MISSING (export PATH=\"$HOME/.local/bin:\$PATH\")"
  fail=1
fi

if [ -f .env ]; then
  if uv run python -c "
from dotenv import load_dotenv
import os
load_dotenv('.env')
print('present' if os.getenv('OPENROUTER_API_KEY') else 'missing')
" | grep -q present; then
    echo "OPENROUTER_API_KEY: present"
  else
    echo "OPENROUTER_API_KEY: MISSING in .env"
    fail=1
  fi
else
  echo ".env: MISSING (Vorlage: .env.example)"
  fail=1
fi

remote="$(git remote get-url origin 2>/dev/null || true)"
if [[ "$remote" == git@github.com:* ]]; then
  echo "git remote: SSH ($remote)"
elif [[ -n "$remote" ]]; then
  echo "git remote: $remote (HTTPS; für Push ggf. gh auth login oder SSH nutzen)"
else
  echo "git remote: MISSING"
  fail=1
fi

scratch="$(mktemp -d)"
echo "scratch: writable ($scratch)"
rmdir "$scratch"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "gh: authenticated"
else
  echo "gh: not authenticated (optional, nur für gh pr create)"
fi

exit "$fail"
