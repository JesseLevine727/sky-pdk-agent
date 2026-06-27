#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/../env.sh"

if [ "$#" -lt 3 ]; then
  echo "usage: $0 <layout.mag> <cell-name> <out-spice>" >&2
  exit 2
fi

LAYOUT="$1"
CELL="$2"
OUT_SPICE="$3"

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

mkdir -p "$(dirname "$OUT_SPICE")"
LOG="${OUT_SPICE%.spice}.log"

magic -dnull -noconsole -rcfile "$RCFILE" <<EOF | tee "$LOG"
load "$LAYOUT" -dereference
extract all
ext2spice lvs
ext2spice -o "$OUT_SPICE" "$CELL"
quit -noprompt
EOF

[ -s "$OUT_SPICE" ] || {
  echo "LVS extraction did not create $OUT_SPICE. Log: $LOG" >&2
  exit 1
}

echo "Wrote $OUT_SPICE"
