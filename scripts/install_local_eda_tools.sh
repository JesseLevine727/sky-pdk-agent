#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEB_DIR="$REPO_ROOT/.tools/debs"
APT_ROOT="$REPO_ROOT/.tools/apt"

packages=(
  ngspice
  xschem
  magic
  netgen-lvs
  klayout
  libgit2-1.7
  libqt5core5t64
  libqt5designer5
  libqt5gui5t64
  libqt5multimedia5
  libqt5multimediawidgets5
  libqt5network5t64
  libqt5printsupport5t64
  libqt5sql5t64
  libqt5svg5
  libqt5widgets5t64
  libqt5xml5t64
  libqt5xmlpatterns5
  libruby3.2
  libmd4c0
  libpcre2-16-0
)

mkdir -p "$DEB_DIR" "$APT_ROOT"
cd "$DEB_DIR"
apt-get download "${packages[@]}"

cd "$REPO_ROOT"
for deb in "$DEB_DIR"/*.deb; do
  dpkg-deb -x "$deb" "$APT_ROOT"
done

chmod +x "$REPO_ROOT"/bin/* "$REPO_ROOT"/scripts/*.sh "$REPO_ROOT"/scripts/*.py

cat <<EOF
Local EDA tools extracted under:
  $APT_ROOT

Use:
  source env.sh
  python3 scripts/check_tools.py
EOF

