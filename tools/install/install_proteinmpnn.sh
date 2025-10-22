#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO="${MPNN_REPO:-$ROOT/tools/ProteinMPNN}"

if [ ! -d "$REPO/.git" ]; then
  echo "[mpnn] cloning repo -> $REPO"
  git clone --depth=1 https://github.com/dauparas/ProteinMPNN "$REPO"
fi

echo "[mpnn] installing python deps"
pip install -r "$REPO/requirements.txt" || true  # repo uses torch/numpy; already installed

echo "[mpnn] ready at $REPO"
