#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

# Optional: locally extracted Chromium system libraries (for machines without
# passwordless apt). Set PLAYWRIGHT_DEPS_ROOT to the extraction prefix.
DEPS_ROOT="${PLAYWRIGHT_DEPS_ROOT:-/tmp/pw-root}"
if [ -d "$DEPS_ROOT" ]; then
  export LD_LIBRARY_PATH="$DEPS_ROOT/usr/lib/aarch64-linux-gnu:$DEPS_ROOT/usr/lib:$DEPS_ROOT/lib/aarch64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  FONT_CONF="${PLAYWRIGHT_FONT_CONF:-/tmp/pw-fonts.conf}"
  if [ ! -f "$FONT_CONF" ]; then
    cat > "$FONT_CONF" <<EOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>$DEPS_ROOT/usr/share/fonts</dir>
  <cachedir>/tmp/pw-fontcache</cachedir>
</fontconfig>
EOF
  fi
  export FONTCONFIG_FILE="$FONT_CONF"
  export FONTCONFIG_PATH="$DEPS_ROOT/etc/fonts"
fi

uv run pytest -m browser "$@"
