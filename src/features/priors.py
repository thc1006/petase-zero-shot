# src/features/priors.py
"""
Prior-based scoring from literature-derived biochemical knowledge.
Implements hard constraints (catalytic triad, oxyanion hole) and favorable regions.
"""

import yaml
from Bio import pairwise2


def _load_yaml(path):
    """Load priors YAML configuration."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _align_to_wt(seq, wt):
    # 簡單全域比對，回傳「WT 序列位置 → 變體中的對應位置」的索引映射
    aln = pairwise2.align.globalms(wt, seq, 2, -1, -5, -1, one_alignment_only=True)[0]
    wt_aln, var_aln = aln.seqA, aln.seqB
    mapping = {}
    i_wt = i_var = 0
    for a, b in zip(wt_aln, var_aln):
        if a != "-":
            i_wt += 1
        if b != "-":
            i_var += 1
        if a != "-" and b != "-":
            mapping[i_wt] = i_var  # 1-based positions
    return mapping

def prior_scores(seqs, cfg):
    """
    Calculate prior-based activity and stability scores.

    Args:
        seqs: List of (seq_id, sequence) tuples
        cfg: Configuration dict with:
            - priors_yaml: path to priors YAML file
            - wt_fasta: (optional) path to WT sequence for alignment

    Returns:
        (activity_prior, stability_prior): tuple of {seq_id: score} dicts
    """
    pri_path = cfg.get("priors_yaml", "data/priors/priors_petase_2024_2025.yaml")
    pri = _load_yaml(pri_path)

    # Load WT sequence if provided
    wt_seq = None
    wt_path = cfg.get("wt_fasta")
    if wt_path:
        try:
            from Bio import SeqIO
            wt_seq = str(next(SeqIO.parse(wt_path, "fasta")).seq)
        except Exception as e:
            print(f"[WARN] Could not load WT sequence from {wt_path}: {e}")

    # Extract activity priors (fix YAML field paths)
    activity_cfg = pri.get("activity", {})
    triad = set(activity_cfg.get("catalytic_triad", {}).get("positions", []))
    oxyanion = set(activity_cfg.get("oxyanion_hole", {}).get("positions", []))

    # Get penalties
    triad_penalty = float(activity_cfg.get("catalytic_triad", {}).get("penalty_if_mutated", -2.5))
    oxyanion_penalty = float(activity_cfg.get("oxyanion_hole", {}).get("penalty_if_mutated", -2.0))

    # Get favorable regions
    fav_regions = activity_cfg.get("favorable_regions", [])

    # Extract stability priors
    stability_cfg = pri.get("stability", {})
    stability_rules = stability_cfg.get("favorable_rules", [])

    act_out = {}
    st_out = {}

    for sid, seq in seqs:
        # Build alignment mapping if WT is available
        mapping = {}
        if wt_seq:
            try:
                mapping = _align_to_wt(seq, wt_seq)
            except Exception as e:
                print(f"[WARN] Alignment failed for {sid}: {e}")
                # Fallback: assume direct position correspondence
                mapping = {i: i for i in range(1, min(len(wt_seq), len(seq)) + 1)}
        else:
            # No WT: assume input sequence uses IsPETase numbering
            mapping = {i: i for i in range(1, len(seq) + 1)}

        # === ACTIVITY SCORE ===
        a_score = 0.0

        # 1) Catalytic triad - hard penalty if mutated
        for pos in triad:
            var_pos = mapping.get(pos, pos)
            if 1 <= var_pos <= len(seq):
                # If we have WT, check for mutation
                if wt_seq and pos <= len(wt_seq):
                    if seq[var_pos - 1] != wt_seq[pos - 1]:
                        a_score += triad_penalty
                else:
                    # Conservative: assume potential mutation risk
                    # (only apply small penalty if we can't verify)
                    a_score += triad_penalty * 0.1

        # 2) Oxyanion hole - hard penalty if mutated
        for pos in oxyanion:
            var_pos = mapping.get(pos, pos)
            if 1 <= var_pos <= len(seq):
                if wt_seq and pos <= len(wt_seq):
                    if seq[var_pos - 1] != wt_seq[pos - 1]:
                        a_score += oxyanion_penalty
                else:
                    a_score += oxyanion_penalty * 0.1

        # 3) Favorable regions - reward if positions are present
        for region in fav_regions:
            positions = region.get("positions", [])
            reward = float(region.get("reward", 0.5))

            # Check if any position in this region is accessible
            hit = False
            for pos in positions:
                var_pos = mapping.get(pos, pos)
                if 1 <= var_pos <= len(seq):
                    # Position is present and accessible
                    hit = True
                    break

            if hit:
                # Award partial reward for region presence
                # (more sophisticated: check if mutation is favorable)
                a_score += reward * 0.5  # Conservative scaling

        # === STABILITY SCORE ===
        s_score = 0.0

        # Aggregate stability rule rewards
        for rule in stability_rules:
            reward = float(rule.get("reward", 0.3))
            # Simple model: add base reward
            # (more sophisticated: check specific positions/pairs)
            s_score += reward * 0.5  # Conservative scaling

        act_out[sid] = a_score
        st_out[sid] = s_score

    return act_out, st_out
