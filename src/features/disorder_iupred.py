"""
Intrinsic disorder prediction for expression channel improvement.
Uses metapredict (fast, pip-installable) as primary method with fallback to simple heuristics.

Lower disorder = better expression (ordered proteins express better).
"""

def disorder_proxy_scores(seqs, cfg):
    """
    Calculate disorder scores for protein sequences.

    Args:
        seqs: List of (seq_id, sequence) tuples
        cfg: Configuration dict (currently unused, reserved for future options)

    Returns:
        dict: {seq_id: disorder_score} where lower disorder = better expression

    Implementation:
        1. Try metapredict (accurate ML-based disorder predictor)
        2. Fallback to sequence-based heuristics if metapredict unavailable

    Score interpretation:
        - Lower values = more ordered = better expression
        - Higher values = more disordered = worse expression
        - Typical range: 0.0 (fully ordered) to 1.0 (fully disordered)
    """

    # Try metapredict first (best accuracy)
    try:
        import metapredict as meta
        return _disorder_metapredict(seqs)
    except ImportError:
        # Fallback to sequence-based heuristics
        return _disorder_heuristic(seqs)


def _disorder_metapredict(seqs):
    """
    Use metapredict to compute disorder scores.
    Returns mean disorder score across the entire sequence.
    """
    import metapredict as meta

    out = {}
    for sid, seq in seqs:
        if not seq or len(seq) == 0:
            # Empty sequence: assign neutral score
            out[sid] = 0.5
            continue

        try:
            # Get per-residue disorder scores
            disorder_scores = meta.predict_disorder(seq)

            # Calculate mean disorder (0.0 = ordered, 1.0 = disordered)
            mean_disorder = sum(disorder_scores) / len(disorder_scores)

            # Return negated score so lower disorder = higher score
            # This aligns with "lower disorder = better expression"
            out[sid] = float(mean_disorder)

        except Exception as e:
            # If prediction fails, use heuristic fallback for this sequence
            out[sid] = _disorder_heuristic_single(seq)

    return out


def _disorder_heuristic(seqs):
    """
    Fallback heuristic-based disorder prediction.
    Uses amino acid composition features correlated with disorder.
    """
    out = {}
    for sid, seq in seqs:
        out[sid] = _disorder_heuristic_single(seq)
    return out


def _disorder_heuristic_single(seq):
    """
    Simple heuristic disorder predictor based on amino acid composition.

    Disorder-promoting residues: P, E, K, S, Q, A, G, D, R
    Order-promoting residues: W, F, Y, I, V, L, C, M, N, T

    Returns float in [0, 1] where higher = more disordered.
    """
    if not seq or len(seq) == 0:
        return 0.5  # Neutral for empty

    # Disorder-promoting residues (flexible, charged, small)
    disorder_promoting = set('PEKSQAGDR')

    # Order-promoting residues (hydrophobic, aromatic, structured)
    order_promoting = set('WFYIVLCMNT')

    disorder_count = sum(1 for aa in seq if aa in disorder_promoting)
    order_count = sum(1 for aa in seq if aa in order_promoting)

    # Calculate disorder propensity
    total = len(seq)
    disorder_fraction = disorder_count / total
    order_fraction = order_count / total

    # Simple linear combination (0 = fully ordered, 1 = fully disordered)
    # Higher disorder_fraction and lower order_fraction = higher disorder score
    disorder_score = 0.5 + 0.5 * (disorder_fraction - order_fraction)

    # Clamp to [0, 1]
    disorder_score = max(0.0, min(1.0, disorder_score))

    return float(disorder_score)
