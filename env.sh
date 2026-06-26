#!/usr/bin/env bash
# Source this file to use the repo-local EDA toolchain and SKY130 defaults.

if [ -n "${BASH_SOURCE[0]:-}" ]; then
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  REPO_ROOT="$(pwd)"
fi

export PATH="$REPO_ROOT/bin:$REPO_ROOT/.tools/apt/usr/bin:$PATH"
export LD_LIBRARY_PATH="$REPO_ROOT/.tools/apt/usr/lib/klayout:$REPO_ROOT/.tools/apt/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
export PDK_ROOT="${PDK_ROOT:-$HOME/.ciel}"
export PDK="${PDK:-sky130A}"
if [ -f "$PDK_ROOT/$PDK/libs.tech/ngspice/spinit" ]; then
  export SPICEINIT="${SPICEINIT:-$PDK_ROOT/$PDK/libs.tech/ngspice/spinit}"
fi
