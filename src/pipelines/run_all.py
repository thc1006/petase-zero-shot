"""
Main pipeline orchestrator for PETase variant scoring.

This module coordinates all feature extraction methods (PLM, MSA, ΔΔG, etc.)
and generates predictions with reporting outputs.
"""
import os
from src.utils_seq import read_fasta
from src.ensemble.aggregate import fuse_scores
from src.reporting.methods_scaffold import write_methods
from src.reporting.figures import plot_distributions

def run_pipeline(fasta_path, outdir, cfg):
    """
    Run the complete PETase variant prediction pipeline.

    Args:
        fasta_path: Path to input FASTA file with protein sequences
        outdir: Output directory for predictions and reports
        cfg: Configuration dict with feature flags (use_plm, use_gemme, etc.)

    Returns:
        None. Writes predictions.csv, figures, and METHODS.md to outdir.

    Raises:
        ValueError: If FASTA file contains no sequences
    """
    seqs = read_fasta(fasta_path)
    if not seqs:
        raise ValueError('No sequences in FASTA')
    scores = {'activity':{}, 'stability':{}, 'expression':{}}

    # Lazy imports inside try blocks allow pipeline to continue if dependencies missing
    # pylint: disable=import-outside-toplevel,broad-exception-caught
    if cfg.get('use_plm', True):
        try:
            from src.features.plm_llr import plm_activity_scores, plm_perplexity_proxy
            scores['activity']['plm_llr'] = plm_activity_scores(seqs, cfg)
            scores['stability']['plm_perplexity'] = plm_perplexity_proxy(seqs, cfg)
        except Exception as e:  # Catch all to ensure pipeline resilience
            print('[WARN] PLM failed:', e)

    if cfg.get('use_gemme', False):
        try:
            from src.features.msa_gemme import gemme_scores
            scores['activity']['gemme'] = gemme_scores(seqs, cfg)
        except Exception as e:  # Catch all to ensure pipeline resilience
            print('[WARN] GEMME failed:', e)

    if cfg.get('use_ddg_foldx', False):
        try:
            from src.features.ddg_foldx import ddg_foldx_scores
            scores['stability']['ddg_foldx'] = ddg_foldx_scores(seqs, cfg)
        except Exception as e:  # Catch all to ensure pipeline resilience
            print('[WARN] FoldX failed:', e)

    if cfg.get('use_ddg_rosetta', False):
        try:
            from src.features.ddg_rosetta import ddg_rosetta_scores
            scores['stability']['ddg_rosetta'] = ddg_rosetta_scores(seqs, cfg)
        except Exception as e:  # Catch all to ensure pipeline resilience
            print('[WARN] Rosetta failed:', e)

    if cfg.get('use_deepddg', False):
        try:
            from src.features.ddg_deepddg import ddg_deepddg_scores
            scores['stability']['ddg_deepddg'] = ddg_deepddg_scores(seqs, cfg)
        except Exception as e:  # Catch all to ensure pipeline resilience
            print('[WARN] DeepDDG failed:', e)

    # Expression
    try:
        from src.features.solubility import solubility_proxy_scores
        scores['expression']['solubility_proxy'] = solubility_proxy_scores(seqs, cfg)
    except Exception as e:  # Catch all to ensure pipeline resilience
        print('[WARN] Solubility proxy failed:', e)

    if cfg.get('use_disorder', False):
        try:
            from src.features.disorder_iupred import disorder_proxy_scores
            scores['expression']['disorder_proxy'] = disorder_proxy_scores(seqs, cfg)
        except Exception as e:  # Catch all to ensure pipeline resilience
            print('[WARN] Disorder proxy failed:', e)

    # === Priors (Activity & Stability) ===
    if cfg.get('use_priors', False):
        try:
            from src.features.priors import prior_scores
            a_prior, s_prior = prior_scores(seqs, cfg)
            scores['activity']['priors'] = a_prior
            scores['stability']['priors'] = s_prior
        except Exception as e:  # Catch all to ensure pipeline resilience
            print('[WARN] Priors channel failed:', e)

    pred = fuse_scores(seqs, scores, cfg)
    out_csv = os.path.join(outdir, 'predictions.csv')
    pred.to_csv(out_csv, index=False)

    os.makedirs(os.path.join(outdir,'figures'), exist_ok=True)
    plot_distributions(pred, os.path.join(outdir,'figures'))

    write_methods(scores, cfg, os.path.join(outdir,'METHODS.md'))
    print('[OK] wrote', out_csv)
