#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/.tools/src/magic"
PREFIX="$ROOT/.tools/local/magic-8.3.668"
MAGIC_REF="${MAGIC_REF:-60061ea33fac62be6277f2ee2f54711849d586dc}"
DEB_DIR="$ROOT/.tools/debs"
APT_ROOT="$ROOT/.tools/apt"
TCL_CONFIG_DIR="$ROOT/.tools/build/magic-tcl-config"
LOCAL_LIB="$APT_ROOT/usr/lib/x86_64-linux-gnu"
LOCAL_INC="$APT_ROOT/usr/include/tcl8.6"

mkdir -p "$DEB_DIR" "$APT_ROOT" "$ROOT/.tools/src" "$ROOT/.tools/local" "$TCL_CONFIG_DIR"

if [ ! -f "$LOCAL_LIB/tclConfig.sh" ] || [ ! -f "$LOCAL_LIB/tkConfig.sh" ]; then
  (
    cd "$DEB_DIR"
    apt-get download tcl-dev tcl8.6-dev tk-dev tk8.6-dev
  )
  for deb in "$DEB_DIR"/tcl-dev_*.deb "$DEB_DIR"/tcl8.6-dev_*.deb "$DEB_DIR"/tk-dev_*.deb "$DEB_DIR"/tk8.6-dev_*.deb; do
    dpkg-deb -x "$deb" "$APT_ROOT"
  done
fi

cp "$LOCAL_LIB/tclConfig.sh" "$TCL_CONFIG_DIR/tclConfig.sh"
cp "$LOCAL_LIB/tkConfig.sh" "$TCL_CONFIG_DIR/tkConfig.sh"
python3 - "$TCL_CONFIG_DIR" "$LOCAL_LIB" <<'PY'
from pathlib import Path
import sys

config_dir = Path(sys.argv[1])
local_lib = sys.argv[2]
replacements = {
    "TCL_STUB_LIB_SPEC='-L/usr/lib/x86_64-linux-gnu -ltclstub8.6'": f"TCL_STUB_LIB_SPEC='-L{local_lib} -ltclstub8.6'",
    "TK_STUB_LIB_SPEC='-L/usr/lib/x86_64-linux-gnu -ltkstub8.6'": f"TK_STUB_LIB_SPEC='-L{local_lib} -ltkstub8.6'",
}
for path in [config_dir / "tclConfig.sh", config_dir / "tkConfig.sh"]:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
PY

if [ ! -d "$SRC/.git" ]; then
  git init "$SRC"
  git -C "$SRC" remote add origin https://github.com/RTimothyEdwards/magic.git
fi
git -C "$SRC" fetch --depth 1 origin "$MAGIC_REF"
git -C "$SRC" checkout --detach FETCH_HEAD

(
  cd "$SRC"
  ./configure \
    --prefix="$PREFIX" \
    --libdir="$PREFIX/lib" \
    --without-cairo \
    --without-opengl \
    --with-tcl="$TCL_CONFIG_DIR" \
    --with-tk="$TCL_CONFIG_DIR" \
    --with-tclincls="$LOCAL_INC" \
    --with-tkincls="$LOCAL_INC"
  make clean >/dev/null 2>&1 || true
  make -j"${JOBS:-2}"
  make install
)

"$PREFIX/bin/magic" --version
