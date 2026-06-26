#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/../env.sh"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <layout.mag> <report-dir>" >&2
  exit 2
fi

LAYOUT="$1"
REPORT_DIR="$2"

command -v magic >/dev/null 2>&1 || {
  echo "missing magic on PATH" >&2
  exit 127
}

: "${PDK_ROOT:?set PDK_ROOT to your PDK root}"
PDK="${PDK:-sky130A}"
RCFILE="$PDK_ROOT/$PDK/libs.tech/magic/$PDK.magicrc"

[ -f "$RCFILE" ] || {
  echo "missing Magic rcfile: $RCFILE" >&2
  exit 1
}

mkdir -p "$REPORT_DIR"

magic -dnull -noconsole -rcfile "$RCFILE" <<EOF
load "$LAYOUT" -dereference
drc euclidean on
drc check
drc catchup
drc count total
drc listall why
quit -noprompt
EOF
