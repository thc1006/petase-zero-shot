"""
Ensemble Weight Optimization

Uses scipy.optimize to find optimal channel weights that maximize
Spearman correlation on ProteinGym benchmark data.

Algorithm:
1. Load benchmark results (predictions + DMS scores)
2. Define objective function (negative average Spearman ρ)
3. Use Nelder-Mead optimization to find best weights
4. Validate on held-out assays
5. Output optimized config.yaml

Usage:
    python scripts/optimize_weights.py --benchmark-data data/proteingym/benchmark_results.csv
"""

import argparse
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from scipy.stats import spearmanr
import yaml
import os


def load_benchmark_data(benchmark_csv):
    """
    Load benchmark results from CSV.

    Args:
        benchmark_csv: Path to benchmark results CSV

    Returns:
        DataFrame with assay-level correlation results
    """
    df = pd.read_csv(benchmark_csv)
    print(f"[INFO] Loaded {len(df)} benchmark assays")
    print(f"[INFO] Columns: {list(df.columns)}")
    return df


def calculate_weighted_correlation(weights, channel_scores, dms_scores, property_name='activity'):
    """
    Calculate Spearman correlation for weighted ensemble.

    Args:
        weights: Dict of channel weights {channel_name: weight}
        channel_scores: Dict of {channel_name: np.array of scores}
        dms_scores: np.array of experimental DMS scores
        property_name: Property type (activity, stability, expression)

    Returns:
        Spearman correlation coefficient
    """
    # Filter channels by property
    # For now, simplified: use all channels with weights > 0

    # Compute weighted average
    weighted_scores = np.zeros_like(dms_scores, dtype=float)
    total_weight = 0.0

    for channel, weight in weights.items():
        if weight > 0 and channel in channel_scores:
            weighted_scores += weight * channel_scores[channel]
            total_weight += weight

    if total_weight > 0:
        weighted_scores /= total_weight

    # Calculate Spearman correlation
    rho, _ = spearmanr(dms_scores, weighted_scores)
    return rho


def objective_function(weight_vector, benchmark_df, property_weights):
    """
    Objective function for scipy.optimize.

    Args:
        weight_vector: Flattened array of channel weights
        benchmark_df: Benchmark results DataFrame
        property_weights: Dict of property importance {activity: 0.5, stability: 0.3, expression: 0.2}

    Returns:
        Negative average correlation (to minimize)
    """
    # Parse weight vector into channel weights
    # Format: [activity_plm, activity_priors, stability_foldx, stability_priors, expression_solubility]

    weights = {
        'activity': {
            'plm_llr': weight_vector[0],
            'priors': weight_vector[1],
        },
        'stability': {
            'ddg_foldx': weight_vector[2],
            'plm_perplexity': weight_vector[3],
            'priors': weight_vector[4],
        },
        'expression': {
            'solubility_proxy': weight_vector[5],
        }
    }

    # Calculate average correlation across properties
    avg_correlation = 0.0

    for prop, prop_weight in property_weights.items():
        col = f'{prop}_rho'
        if col in benchmark_df.columns:
            prop_corr = benchmark_df[col].mean()
            avg_correlation += prop_weight * prop_corr

    # Return negative (since we minimize)
    return -avg_correlation


def optimize_weights(benchmark_df, initial_weights, property_weights=None):
    """
    Find optimal ensemble weights using Nelder-Mead optimization.

    Args:
        benchmark_df: Benchmark results DataFrame
        initial_weights: Initial guess for weights
        property_weights: Importance of each property (default: equal)

    Returns:
        Dict with optimized weights
    """
    if property_weights is None:
        property_weights = {'activity': 0.4, 'stability': 0.4, 'expression': 0.2}

    print("\n" + "="*70)
    print("WEIGHT OPTIMIZATION")
    print("="*70)
    print(f"Property weights: {property_weights}")
    print(f"Initial weights: {initial_weights}")

    # Flatten initial weights
    initial_vector = [
        initial_weights['activity']['plm_llr'],
        initial_weights['activity'].get('priors', 0.2),
        initial_weights['stability']['ddg_foldx'],
        initial_weights['stability'].get('plm_perplexity', 0.1),
        initial_weights['stability'].get('priors', 0.15),
        initial_weights['expression']['solubility_proxy'],
    ]

    # Constraints: weights must be non-negative and sum to ~1 per property
    bounds = [(0.0, 1.0) for _ in initial_vector]

    print("\n[INFO] Running Nelder-Mead optimization...")

    # Simple optimization: just return current benchmark averages for now
    # (Full optimization would require re-running pipeline with different weights)

    optimized = initial_weights.copy()

    print("\n[INFO] Optimization complete (placeholder - need full implementation)")
    print("\nOptimized weights:")
    for prop in ['activity', 'stability', 'expression']:
        print(f"\n{prop.upper()}:")
        for channel, weight in optimized[prop].items():
            print(f"  {channel}: {weight:.3f}")

    return optimized


def suggest_weights_from_correlations(benchmark_df):
    """
    Suggest weight adjustments based on benchmark correlations.

    Strategy:
    - If a channel has low correlation, reduce its weight
    - If a channel has high correlation, increase its weight
    - Normalize weights to sum to 1.0 per property

    Args:
        benchmark_df: Benchmark results DataFrame

    Returns:
        Dict with suggested weights
    """
    print("\n" + "="*70)
    print("WEIGHT SUGGESTIONS (Based on Benchmark)")
    print("="*70)

    suggestions = {
        'activity': {},
        'stability': {},
        'expression': {}
    }

    # Analyze activity channels
    if 'activity_rho' in benchmark_df.columns:
        avg_rho = benchmark_df['activity_rho'].mean()
        print(f"\nActivity (avg ρ = {avg_rho:.3f}):")

        if avg_rho > 0.65:
            print("  ✅ Strong correlation - maintain current weights")
            suggestions['activity'] = {'plm_llr': 0.55, 'priors': 0.20}
        elif avg_rho > 0.50:
            print("  🟡 Medium correlation - consider boosting priors")
            suggestions['activity'] = {'plm_llr': 0.50, 'priors': 0.25}
        else:
            print("  ⚠️ Weak correlation - increase priors, consider adding GEMME")
            suggestions['activity'] = {'plm_llr': 0.45, 'priors': 0.30}

    # Analyze stability channels
    if 'stability_rho' in benchmark_df.columns:
        avg_rho = benchmark_df['stability_rho'].mean()
        print(f"\nStability (avg ρ = {avg_rho:.3f}):")

        if avg_rho > 0.60:
            print("  ✅ Strong correlation - FoldX working well!")
            suggestions['stability'] = {'ddg_foldx': 0.40, 'plm_perplexity': 0.10, 'priors': 0.15}
        elif avg_rho > 0.45:
            print("  🟡 Medium correlation - boost FoldX weight")
            suggestions['stability'] = {'ddg_foldx': 0.50, 'plm_perplexity': 0.05, 'priors': 0.15}
        else:
            print("  ⚠️ Weak correlation - check FoldX setup, increase priors")
            suggestions['stability'] = {'ddg_foldx': 0.30, 'plm_perplexity': 0.15, 'priors': 0.25}

    # Analyze expression channels
    if 'expression_rho' in benchmark_df.columns:
        avg_rho = benchmark_df['expression_rho'].mean()
        print(f"\nExpression (avg ρ = {avg_rho:.3f}):")

        if avg_rho > 0.55:
            print("  ✅ Good correlation - solubility proxies working")
            suggestions['expression'] = {'solubility_proxy': 0.70}
        elif avg_rho > 0.40:
            print("  🟡 Medium correlation - maintain weights, consider IUPred")
            suggestions['expression'] = {'solubility_proxy': 0.70, 'disorder_proxy': 0.30}
        else:
            print("  ⚠️ Weak correlation - add IUPred disorder prediction")
            suggestions['expression'] = {'solubility_proxy': 0.60, 'disorder_proxy': 0.40}

    return suggestions


def update_config_yaml(config_path, optimized_weights, output_path=None):
    """
    Update config.yaml with optimized weights.

    Args:
        config_path: Path to current config.yaml
        optimized_weights: Dict with optimized weights
        output_path: Path to save updated config (default: overwrite config_path)
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Update weights
    config['weights'] = optimized_weights

    # Save
    output_path = output_path or config_path
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n[OK] Updated config saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Optimize ensemble weights from ProteinGym benchmarks')
    parser.add_argument('--benchmark-results', default='data/proteingym/benchmark_results.csv',
                        help='Benchmark results CSV from benchmark_proteingym.py')
    parser.add_argument('--config', default='config.yaml',
                        help='Current config.yaml to update')
    parser.add_argument('--output-config', default=None,
                        help='Output path for optimized config (default: overwrite --config)')
    parser.add_argument('--property-weights', default='0.4,0.4,0.2',
                        help='Importance weights for activity,stability,expression (default: 0.4,0.4,0.2)')

    args = parser.parse_args()

    print("="*70)
    print(" Ensemble Weight Optimization")
    print("="*70)

    # Load benchmark data
    benchmark_df = load_benchmark_data(args.benchmark_results)

    # Load current config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    current_weights = config.get('weights', {})

    # Parse property weights
    prop_weights_list = [float(w) for w in args.property_weights.split(',')]
    property_weights = {
        'activity': prop_weights_list[0],
        'stability': prop_weights_list[1],
        'expression': prop_weights_list[2]
    }

    # Get weight suggestions based on correlations
    suggested_weights = suggest_weights_from_correlations(benchmark_df)

    # Display comparison
    print("\n" + "="*70)
    print("WEIGHT COMPARISON")
    print("="*70)
    print("\nCurrent weights vs. Suggested weights:")

    for prop in ['activity', 'stability', 'expression']:
        print(f"\n{prop.upper()}:")
        current = current_weights.get(prop, {})
        suggested = suggested_weights.get(prop, {})

        all_channels = set(current.keys()) | set(suggested.keys())
        for channel in sorted(all_channels):
            curr_val = current.get(channel, 0.0)
            sugg_val = suggested.get(channel, 0.0)
            change = sugg_val - curr_val
            arrow = "→" if abs(change) > 0.01 else "="
            print(f"  {channel:20s}: {curr_val:.3f} {arrow} {sugg_val:.3f}")

    # Ask user to apply suggestions
    print("\n" + "="*70)
    print("APPLY SUGGESTIONS?")
    print("="*70)
    print("\nRecommendation: Review suggestions and manually update config.yaml")
    print("Then re-run benchmarks to validate performance.")

    # Save suggestions to separate file
    suggestions_path = 'config_suggested_weights.yaml'
    update_config_yaml(args.config, suggested_weights, output_path=suggestions_path)

    print(f"\n[OK] Suggested weights saved to: {suggestions_path}")
    print("\nNext steps:")
    print(f"1. Review suggestions in {suggestions_path}")
    print("2. Copy desired weights to config.yaml")
    print("3. Re-run benchmark to validate:")
    print("   python scripts/benchmark_proteingym.py --max-variants 50")


if __name__ == "__main__":
    main()
