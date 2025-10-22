#!/usr/bin/env bash
set -euo pipefail

IN_FASTA="${1:-}"
if [[ -z "$IN_FASTA" ]]; then
  echo "Usage: $0 path/to/organizer_sequences.fasta"
  exit 1
fi

STAMP=$(date +%Y%m%d_%H%M%S)
OUTDIR="runs/run_${STAMP}"
mkdir -p "$OUTDIR"

echo "========================================="
echo "PETase Zero-Shot Predictive Submission"
echo "========================================="
echo "Input:  $IN_FASTA"
echo "Output: $OUTDIR"
echo "Time:   $STAMP"
echo "========================================="
echo ""

# Run the pipeline
python -m src.cli --input "$IN_FASTA" --outdir "$OUTDIR" --config config.yaml

# Validate predictions.csv
python - "$OUTDIR/predictions.csv" << 'PY'
import pandas as pd
import sys

csv_path = sys.argv[1]
df = pd.read_csv(csv_path)

# Check columns
expected_cols = {"seq_id", "activity_score", "stability_score", "expression_score"}
actual_cols = set(df.columns)
assert actual_cols == expected_cols, f"Column mismatch: {actual_cols} != {expected_cols}"

# Check for NaN
assert not df.isna().any().any(), "Found NaN values in predictions!"

# Check score range [0,1]
score_cols = ["activity_score", "stability_score", "expression_score"]
for col in score_cols:
    assert (df[col] >= 0).all() and (df[col] <= 1).all(), f"{col} has values outside [0,1]"

print(f"[OK] predictions.csv validated ({len(df)} sequences)")
print(f"     Columns: {list(df.columns)}")
print(f"     No NaN values")
print(f"     All scores in [0,1]")
PY

# Package submission files
mkdir -p submission
cp "$OUTDIR/predictions.csv" "submission/predictions_${STAMP}.csv"
cp "$OUTDIR/METHODS.md" "submission/METHODS_${STAMP}.md"

# Copy figures if they exist
if [ -d "$OUTDIR/figures" ]; then
    mkdir -p "submission/figures_${STAMP}"
    cp "$OUTDIR/figures/"*.png "submission/figures_${STAMP}/"
fi

echo ""
echo "========================================="
echo "[DONE] Submission files ready!"
echo "========================================="
echo "  predictions: submission/predictions_${STAMP}.csv"
echo "  methods:     submission/METHODS_${STAMP}.md"
if [ -d "submission/figures_${STAMP}" ]; then
    echo "  figures:     submission/figures_${STAMP}/"
fi
echo "========================================="
