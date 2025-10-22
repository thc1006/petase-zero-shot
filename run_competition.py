#!/usr/bin/env python3
"""
Zero-Shot Protein Activity Prediction - Competition Runner

Usage:
    python run_competition.py <input.fasta> [output_dir]

Example:
    python run_competition.py data/competition/variants.fasta results/
"""

import sys
import subprocess
import pandas as pd
from pathlib import Path


def run_prediction(input_fasta: str, output_dir: str = "data/competition/output"):
    """Run prediction pipeline and generate submission file."""

    print("=" * 80)
    print("ZERO-SHOT PROTEIN ACTIVITY PREDICTION")
    print("=" * 80)
    print(f"\nInput:  {input_fasta}")
    print(f"Output: {output_dir}")

    # Check input exists
    if not Path(input_fasta).exists():
        print(f"\n[ERROR] Input file not found: {input_fasta}")
        return False

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Step 1: Run prediction
    print("\n[STEP 1/3] Running multi-channel prediction...")
    print("-" * 80)

    cmd = [
        sys.executable, "-m", "src.cli",
        "--input", input_fasta,
        "--outdir", output_dir,
        "--config", "config.yaml"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] Prediction failed!")
        print(result.stderr)
        return False

    print("[OK] Prediction completed")

    # Step 2: Calculate rankings
    print("\n[STEP 2/3] Calculating final rankings...")
    print("-" * 80)

    pred_file = Path(output_dir) / "predictions.csv"
    if not pred_file.exists():
        print(f"[ERROR] Predictions file not found: {pred_file}")
        return False

    df = pd.read_csv(pred_file)

    # Calculate final score (weighted combination)
    df['final_score'] = (
        df['activity_score'] * 0.50 +
        df['stability_score'] * 0.30 +
        df['expression_score'] * 0.20
    )

    # Rank variants
    df_ranked = df.sort_values('final_score', ascending=False).reset_index(drop=True)
    df_ranked.index = df_ranked.index + 1
    df_ranked.index.name = 'rank'

    print(f"[OK] Ranked {len(df_ranked)} variants")

    # Step 3: Generate submission file
    print("\n[STEP 3/3] Generating submission file...")
    print("-" * 80)

    submission = df_ranked[['seq_id', 'final_score']].copy()
    submission_file = Path(output_dir) / "SUBMISSION.csv"
    submission.to_csv(submission_file, index=True)

    print(f"[OK] Submission file created: {submission_file}")

    # Show top 5 predictions
    print("\n" + "=" * 80)
    print("TOP 5 PREDICTIONS:")
    print("=" * 80)

    for idx in range(min(5, len(df_ranked))):
        row = df_ranked.iloc[idx]
        variant_name = row['seq_id'].split('|')[0] if '|' in row['seq_id'] else row['seq_id']
        print(f"\n{idx+1}. {variant_name}")
        print(f"   Final Score: {row['final_score']:.4f}")
        print(f"   Activity: {row['activity_score']:.3f} | "
              f"Stability: {row['stability_score']:.3f} | "
              f"Expression: {row['expression_score']:.3f}")

    print("\n" + "=" * 80)
    print("SUBMISSION READY!")
    print("=" * 80)
    print(f"\nSubmission file: {submission_file}")
    print(f"Total variants: {len(df_ranked)}")
    print(f"Top variant: {df_ranked.iloc[0]['seq_id'].split('|')[0] if '|' in df_ranked.iloc[0]['seq_id'] else df_ranked.iloc[0]['seq_id']}")
    print("\n" + "=" * 80)

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_fasta = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/competition/output"

    success = run_prediction(input_fasta, output_dir)
    sys.exit(0 if success else 1)
