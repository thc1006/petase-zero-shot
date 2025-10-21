def write_methods(scores, cfg, outpath):
    open(outpath,'w').write(
        '# METHODS (Zero‑Shot)\n\n'
        'This submission computes three property scores per sequence (activity, thermostability, expression) without using organizer-provided training data.\n\n'
        '**Activity** — Protein language model (ESM‑2/1v) pseudo‑likelihood computed by masking each residue in turn and averaging token log-probabilities (zero‑shot). Optional GEMME ΔE adds evolutionary constraints.\n\n'
        '**Thermostability** — Optional ΔΔG estimates from FoldX / Rosetta ddg_monomer / DeepDDG; plus a weak PLM pseudo‑perplexity proxy.\n\n'
        '**Expression** — Sequence-derived proxies (GRAVY, aromaticity, isoelectric point, charge balance, length); optional IUPred disorder penalty.\n\n'
        '**Fusion** — Channels are median/MAD scaled, rank-averaged with configurable weights, and min–max normalized to [0,1] per property. Missing channels are skipped gracefully.\n\n'
        'No tuning was performed on tournament data; any optional weight choices were validated only on external benchmarks (e.g., ProteinGym).\n'
    )
