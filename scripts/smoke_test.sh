#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

ROOT="$(pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
MAX_COST="${MAX_COST:-0.15}"
fail=0

for name in img img1 img2; do
  echo "=== $name ==="
  mkdir -p "$TMP/$name/input"
  cp "examples/$name.jpg" "$TMP/$name/input/"

  set +e
  uv run knobeln \
    --input "$TMP/$name/input" \
    --output "$TMP/$name/auswertung.csv" \
    --review "$TMP/$name/review" \
    --keep-input \
    --reprocess \
    --no-cache \
    --max-cost "$MAX_COST"
  rc=$?
  set -e

  if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
    echo "FAIL: knobeln exit $rc"
    fail=1
    continue
  fi

  if ! uv run python scripts/compare_golden.py \
    "$TMP/$name/auswertung.csv" \
    "tests/manual/golden/$name.json"; then
    fail=1
  fi
done

exit "$fail"
