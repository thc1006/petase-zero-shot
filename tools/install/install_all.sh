#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
source "$ROOT/.env" 2>/dev/null || true

mkdir -p "$ROOT/tools"

bash "$HERE/install_tranception.sh" || true
bash "$HERE/install_esm_if.sh" || true
bash "$HERE/install_proteinmpnn.sh" || true

echo "[bootstrap] Done. You can now run: make plugins"
