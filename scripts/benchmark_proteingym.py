"""
ProteinGym Benchmarking Script

Validates zero-shot predictions against experimental DMS data.
Calculates Spearman correlations to tune ensemble weights.

Usage:
    python scripts/benchmark_proteingym.py --assays assay1,assay2 --max-variants 100

Key Outputs:
- Per-assay Spearman correlations (activity, stability, expression)
- Average correlation across all assays
- Optimal ensemble weights (via scipy.optimize)
- Benchmark results CSV for analysis
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils_seq import read_fasta
from src.pipelines.run_all import run_pipeline
from src.ensemble.aggregate import fuse_scores
import yaml


def load_dms_assay(assay_path):
    """
    Load a single DMS assay CSV file.

    Args:
        assay_path: Path to DMS CSV file

    Returns:
        DataFrame with columns: mutated_sequence, target_seq, mutant, DMS_score
    """
    df = pd.read_csv(assay_path)

    print(f"[INFO] Loaded {len(df)} variants from {Path(assay_path).name}")
    print(f"[INFO] Columns: {list(df.columns)}")

    # Check required columns
    required = ['mutated_sequence', 'DMS_score']
    for col in required:
        if col not in df.columns:
            print(f"[WARN] Missing required column: {col}")

    return df


def create_temp_fasta(sequences, seq_ids):
    """
    Create temporary FASTA file from sequences.

    Args:
        sequences: List of protein sequences
        seq_ids: List of sequence IDs

    Returns:
        Path to temporary FASTA file
    """
    temp_fasta = tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False)

    for seq_id, seq in zip(seq_ids, sequences):
        temp_fasta.write(f">{seq_id}\n{seq}\n")

    temp_fasta.close()
    return temp_fasta.name


def run_pipeline_on_assay(dms_df, config, max_variants=None):
    """
    Run zero-shot pipeline on DMS assay variants.

    Args:
        dms_df: DataFrame with mutated_sequence and DMS_score columns
        config: Pipeline configuration dict
        max_variants: Maximum number of variants to process (for speed)

    Returns:
        DataFrame with predictions merged with DMS scores
    """
    # Limit variants for faster benchmarking
    if max_variants and len(dms_df) > max_variants:
        print(f"[INFO] Sampling {max_variants} of {len(dms_df)} variants for speed")
        dms_df = dms_df.sample(n=max_variants, random_state=42)

    # Create temporary FASTA
    seq_ids = [f"var_{i}" for i in range(len(dms_df))]
    sequences = dms_df['mutated_sequence'].tolist()

    fasta_path = create_temp_fasta(sequences, seq_ids)

    # Create temporary output directory
    temp_outdir = tempfile.mkdtemp()

    try:
        # Run pipeline
        print(f"[INFO] Running pipeline on {len(dms_df)} variants...")
        run_pipeline(fasta_path, temp_outdir, config)

        # Load predictions
        pred_path = os.path.join(temp_outdir, 'predictions.csv')
        predictions = pd.read_csv(pred_path)

        # Merge with DMS scores
        dms_df['seq_id'] = seq_ids
        merged = dms_df.merge(predictions, on='seq_id', how='inner')

        return merged

    finally:
        # Cleanup
        os.unlink(fasta_path)
        shutil.rmtree(temp_outdir, ignore_errors=True)


def calculate_correlations(merged_df):
    """
    Calculate Spearman correlations between predictions and DMS scores.

    Args:
        merged_df: DataFrame with DMS_score and prediction columns

    Returns:
        Dict with correlation results
    """
    results = {}

    # Activity correlation
    if 'activity_score' in merged_df.columns:
        rho, pval = spearmanr(merged_df['DMS_score'], merged_df['activity_score'])
        results['activity_rho'] = rho
        results['activity_pval'] = pval
        print(f"  Activity:    ρ = {rho:.3f} (p = {pval:.2e})")

    # Stability correlation
    if 'stability_score' in merged_df.columns:
        rho, pval = spearmanr(merged_df['DMS_score'], merged_df['stability_score'])
        results['stability_rho'] = rho
        results['stability_pval'] = pval
        print(f"  Stability:   ρ = {rho:.3f} (p = {pval:.2e})")

    # Expression correlation
    if 'expression_score' in merged_df.columns:
        rho, pval = spearmanr(merged_df['DMS_score'], merged_df['expression_score'])
        results['expression_rho'] = rho
        results['expression_pval'] = pval
        print(f"  Expression:  ρ = {rho:.3f} (p = {pval:.2e})")

    # Overall (average of available correlations)
    rho_values = [v for k, v in results.items() if k.endswith('_rho')]
    results['overall_rho'] = np.mean(rho_values) if rho_values else 0.0
    print(f"  Overall Avg: ρ = {results['overall_rho']:.3f}")

    return results


def benchmark_assays(assay_files, config, max_variants=100, output_csv=None):
    """
    Benchmark pipeline on multiple DMS assays.

    Args:
        assay_files: List of paths to DMS CSV files
        config: Pipeline configuration dict
        max_variants: Max variants per assay (for speed)
        output_csv: Path to save benchmark results

    Returns:
        DataFrame with per-assay correlation results
    """
    benchmark_results = []

    for assay_file in assay_files:
        assay_name = Path(assay_file).stem
        print(f"\n{'='*70}")
        print(f"Benchmarking: {assay_name}")
        print(f"{'='*70}")

        try:
            # Load DMS data
            dms_df = load_dms_assay(assay_file)

            # Run pipeline and get predictions
            merged = run_pipeline_on_assay(dms_df, config, max_variants)

            # Calculate correlations
            correlations = calculate_correlations(merged)

            # Store results
            result = {
                'assay_name': assay_name,
                'assay_file': assay_file,
                'num_variants': len(merged),
                **correlations
            }
            benchmark_results.append(result)

        except Exception as e:
            print(f"[ERROR] Failed to benchmark {assay_name}: {e}")
            import traceback
            traceback.print_exc()

    # Convert to DataFrame
    results_df = pd.DataFrame(benchmark_results)

    # Calculate average correlations across assays
    print(f"\n{'='*70}")
    print("OVERALL BENCHMARK SUMMARY")
    print(f"{'='*70}")
    print(f"Assays benchmarked: {len(results_df)}")
    print(f"Total variants: {results_df['num_variants'].sum()}")
    print(f"\nAverage Correlations:")
    for prop in ['activity', 'stability', 'expression', 'overall']:
        col = f'{prop}_rho'
        if col in results_df.columns:
            avg_rho = results_df[col].mean()
            print(f"  {prop.capitalize():12s}: ρ = {avg_rho:.3f}")

    # Save results
    if output_csv:
        results_df.to_csv(output_csv, index=False)
        print(f"\n[OK] Saved benchmark results to {output_csv}")

    return results_df


def select_representative_assays(proteingym_dir, num_assays=5):
    """
    Select diverse representative DMS assays for benchmarking.

    Strategy:
    - Sample assays from different sizes (small/medium/large)
    - Prefer assays with activity/stability phenotypes
    - Ensure diversity in protein families

    Args:
        proteingym_dir: Directory with DMS CSV files
        num_assays: Number of assays to select

    Returns:
        List of selected assay file paths
    """
    all_assays = list(Path(proteingym_dir).glob('*.csv'))

    if not all_assays:
        print(f"[ERROR] No CSV files found in {proteingym_dir}")
        return []

    print(f"[INFO] Found {len(all_assays)} total DMS assays")

    # Sample randomly for diversity (can be made smarter later)
    selected = np.random.choice(all_assays, size=min(num_assays, len(all_assays)), replace=False)

    print(f"[INFO] Selected {len(selected)} assays for benchmarking:")
    for assay in selected:
        print(f"  - {assay.name}")

    return [str(p) for p in selected]


def main():
    parser = argparse.ArgumentParser(description='Benchmark zero-shot pipeline on ProteinGym DMS assays')
    parser.add_argument('--proteingym-dir', default='data/proteingym/DMS_ProteinGym_substitutions',
                        help='Directory with DMS CSV files')
    parser.add_argument('--assays', type=str, default=None,
                        help='Comma-separated list of specific assay files to benchmark')
    parser.add_argument('--num-assays', type=int, default=5,
                        help='Number of random assays to select (if --assays not specified)')
    parser.add_argument('--max-variants', type=int, default=100,
                        help='Maximum variants per assay (for speed)')
    parser.add_argument('--config', default='config.yaml',
                        help='Pipeline configuration file')
    parser.add_argument('--output', default='data/proteingym/benchmark_results.csv',
                        help='Output CSV path for benchmark results')

    args = parser.parse_args()

    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    print("="*70)
    print(" ProteinGym Zero-Shot Benchmarking")
    print("="*70)
    print(f"Config: {args.config}")
    print(f"Max variants per assay: {args.max_variants}")

    # Select assays
    if args.assays:
        # User-specified assays
        assay_files = [os.path.join(args.proteingym_dir, a.strip()) for a in args.assays.split(',')]
    else:
        # Auto-select representative assays
        assay_files = select_representative_assays(args.proteingym_dir, args.num_assays)

    if not assay_files:
        print("[ERROR] No assays selected for benchmarking")
        return

    # Run benchmark
    results_df = benchmark_assays(assay_files, config, args.max_variants, args.output)

    print("\n[COMPLETE] Benchmarking finished!")
    print(f"\nResults saved to: {args.output}")

    # Next steps
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Review benchmark results:")
    print(f"   cat {args.output}")
    print("\n2. Optimize ensemble weights:")
    print("   python scripts/optimize_weights.py --benchmark-results {args.output}")
    print("\n3. Update config.yaml with optimized weights")


if __name__ == "__main__":
    main()
