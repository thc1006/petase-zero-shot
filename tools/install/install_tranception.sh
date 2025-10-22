#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO_DIR="${TRANCE_REPO:-$ROOT/tools/Tranception}"
PY="${TRANCE_PY:-python}"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "[tranception] cloning repo -> $REPO_DIR"
  git clone --depth=1 https://github.com/OATML-Markslab/Tranception "$REPO_DIR"
fi

echo "[tranception] installing python deps"
pip install -r "$REPO_DIR/requirements.txt"

CKPT_DIR="${TRANCE_CKPT_DIR:-$REPO_DIR/checkpoints}"
mkdir -p "$CKPT_DIR"
# Try to fetch small checkpoint via huggingface (if available); otherwise rely on runtime download.
if command -v huggingface-cli >/dev/null 2>&1; then
  echo "[tranception] attempting to download small checkpoints via huggingface-cli (optional)"
  # Example placeholder; adjust to actual HF repo names if needed.
  # huggingface-cli download oaatml/tranception-small --local-dir "$CKPT_DIR" || true
fi

echo "[tranception] ready at $REPO_DIR"
