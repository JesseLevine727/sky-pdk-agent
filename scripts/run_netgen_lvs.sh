#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/../env.sh"

if [ "$#" -lt 4 ]; then
  echo "usage: $0 <extracted.spice> <schematic.spice> <cell-name> <report-file>" >&2
  exit 2
fi

EXTRACTED="$1"
SCHEMATIC="$2"
CELL="$3"
REPORT="$4"

command -v netgen >/dev/null 2>&1 || {
  echo "missing netgen on PATH" >&2
  exit 127
}

: "${PDK_ROOT:?set PDK_ROOT to your PDK root}"
PDK="${PDK:-sky130A}"
SETUP="$PDK_ROOT/$PDK/libs.tech/netgen/${PDK}_setup.tcl"

[ -f "$SETUP" ] || {
  echo "missing Netgen setup: $SETUP" >&2
  exit 1
}

mkdir -p "$(dirname "$REPORT")"
netgen -batch lvs "$EXTRACTED $CELL" "$SCHEMATIC $CELL" "$SETUP" "$REPORT"
