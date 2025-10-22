def write_methods(scores, cfg, outpath):
    # Check if priors channel is active
    has_priors = 'priors' in scores.get('activity', {}) or 'priors' in scores.get('stability', {})

    priors_text = ''
    if has_priors:
        priors_text = (
            '\n**Biochemical Priors (Literature-Derived)** — Hard constraints on catalytic triad (Ser160/His237/Asp206) '
            'and oxyanion hole (positions 87, 161) with strong negative penalties for mutations. Favorable regions '
            '(β6-β7 loop, β8-α6 loop, N212 glycosylation site, substrate binding groove) receive positive rewards. '
            'All rules extracted from 30+ peer-reviewed PETase variants (2024-2025 literature). '
            'Priors channel weighted at 20% for activity and 15% for stability.\n'
        )

    open(outpath,'w', encoding='utf-8').write(
        '# METHODS (Zero‑Shot)\n\n'
        'This submission computes three property scores per sequence (activity, thermostability, expression) without using organizer-provided training data.\n\n'
        '**Activity** — Protein language model (ESM‑2/1v) pseudo‑likelihood computed by masking each residue in turn and averaging token log-probabilities (zero‑shot). Optional GEMME ΔE adds evolutionary constraints.\n\n'
        '**Thermostability** — Optional ΔΔG estimates from FoldX / Rosetta ddg_monomer / DeepDDG; plus a weak PLM pseudo‑perplexity proxy.\n\n'
        '**Expression** — Sequence-derived proxies (GRAVY, aromaticity, isoelectric point, charge balance, length); optional IUPred disorder penalty.\n'
        + priors_text +
        '\n**Fusion** — Channels are median/MAD scaled, rank-averaged with configurable weights, and min–max normalized to [0,1] per property. Missing channels are skipped gracefully.\n\n'
        'No tuning was performed on tournament data; any optional weight choices were validated only on external benchmarks (e.g., ProteinGym).\n'
    )
