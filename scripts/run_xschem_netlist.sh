#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/../env.sh"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <schematic.sch> <out-dir>" >&2
  exit 2
fi

SCH_FILE="$1"
OUT_DIR="$2"

command -v xschem >/dev/null 2>&1 || {
  echo "missing xschem on PATH" >&2
  exit 127
}

: "${PDK_ROOT:?set PDK_ROOT to your PDK root}"
PDK="${PDK:-sky130A}"
mkdir -p "$OUT_DIR"

export PDK_ROOT
export PDK

xschem -q -x -n -o "$OUT_DIR" "$SCH_FILE"
