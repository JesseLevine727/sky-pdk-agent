#!/usr/bin/env bash
set -euo pipefail

PDK_ROOT="${PDK_ROOT:-$HOME/.ciel}"
PDK="${PDK:-sky130A}"
CIEL_VERSION="${CIEL_VERSION:-}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CIEL_VENV="${CIEL_VENV:-$REPO_ROOT/.tools/ciel-venv}"

if [ ! -x "$CIEL_VENV/bin/python" ]; then
  python3 -m venv "$CIEL_VENV"
fi

"$CIEL_VENV/bin/python" -m pip install --upgrade --no-cache-dir pip ciel

if command -v ciel >/dev/null 2>&1; then
  CIEL_BIN="ciel"
elif [ -x "$CIEL_VENV/bin/ciel" ]; then
  CIEL_BIN="$CIEL_VENV/bin/ciel"
else
  echo "ciel was installed but no executable was found in $CIEL_VENV/bin." >&2
  exit 1
fi

if [ -z "$CIEL_VERSION" ]; then
  CIEL_VERSION="$("$CIEL_BIN" ls-remote --pdk-family sky130 | python3 -c 'import re,sys; text=sys.stdin.read(); m=re.search(r"[0-9a-f]{40}", text); print(m.group(0) if m else "")')"
fi

if [ -z "$CIEL_VERSION" ]; then
  echo "Could not infer latest sky130 Ciel version. Set CIEL_VERSION explicitly." >&2
  exit 1
fi

PDK_ROOT="$PDK_ROOT" "$CIEL_BIN" enable --pdk-family sky130 "$CIEL_VERSION"

cat <<EOF

PDK installed or enabled.

Add these exports to your shell:
export PDK_ROOT="$PDK_ROOT"
export PDK="$PDK"

Then run:
python3 scripts/check_tools.py
EOF
