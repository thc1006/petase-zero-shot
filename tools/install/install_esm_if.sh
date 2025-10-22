#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "[esm-if] installing fair-esm if needed"
pip install --upgrade fair-esm
CKPT="${ESM_IF_CKPT:-$ROOT/tools/esm_if1_gvp4_t16_142M_UR50.pt}"
if [ ! -s "$CKPT" ]; then
  echo "[esm-if] trying to fetch checkpoint to $CKPT"
  mkdir -p "$(dirname "$CKPT")"
  # Fetch from official release if available; otherwise model loader will auto-download into cache.
  URL="https://dl.fbaipublicfiles.com/fair-esm/models/esm_if1_gvp4_t16_142M_UR50.pt"
  if command -v curl >/dev/null 2>&1; then
    curl -L "$URL" -o "$CKPT" || true
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$CKPT" "$URL" || true
  fi
fi
echo "[esm-if] ready"
