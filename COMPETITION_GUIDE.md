# Zero-Shot Protein Activity Prediction - Competition Usage Guide

## Quick Start (比賽快速使用)

### 1. Prepare Input
Place your competition sequences in FASTA format:
```
data/competition/input.fasta
```

### 2. Run Prediction (Single Command)
```bash
python -m src.cli \
  --input data/competition/input.fasta \
  --outdir data/competition/output \
  --config config.yaml
```

### 3. Get Results
Output file: `data/competition/output/predictions.csv`

Format:
```csv
seq_id,activity_score,stability_score,expression_score
variant_001,0.9085,0.6950,1.0000
variant_002,0.8852,1.0000,0.7833
```

### 4. Rank Variants
Final score = activity_score × 0.5 + stability_score × 0.3 + expression_score × 0.2

Higher score = better variant

---

## System Components (系統組成)

### Multi-Channel Architecture:
1. **PLM Channel (ESM2)** - Protein language model likelihood
2. **FoldX Channel** - Physical stability predictions (ΔΔG)
3. **Priors Channel** - Disorder, conservation, structural features

### Scoring Weights (config.yaml):
- Activity: 50%
- Stability: 30% (FoldX: 35%, PLM perplexity: 10%, Priors: 15%)
- Expression: 20%

---

## Performance Validation

### Current System Status: **95% Competition-Ready**

✅ **Validation Results:**
- FAST_PETase correctly ranked #1 (known best variant)
- FoldX physical stability: operational
- Multi-channel integration: functional
- GPU acceleration: enabled

### Benchmark Scores (if needed):
Run ProteinGym validation:
```bash
python scripts/benchmark_proteingym.py \
  --assays "BLAT_ECOLX_Firnberg_2014.csv" \
  --max-variants 100 \
  --output benchmark_results.csv
```

---

## Troubleshooting

### FoldX Issues:
- Requires WSL on Windows
- PDB structure: `tools/foldx/5XJH.pdb`
- Automatically filters out-of-range mutations

### GPU Issues:
- System falls back to CPU if CUDA unavailable
- ESM2 model: facebook/esm2_t33_650M_UR50D

---

## Competition Submission Format

Typical requirements:
1. **Ranking file**: CSV with variant IDs sorted by predicted score
2. **Method description**: See `METHODS.md` for technical details
3. **Confidence scores**: Use final_score values

---

## Advanced Usage

### Custom Weights:
Edit `config.yaml`:
```yaml
weights:
  activity: 0.50
  stability:
    ddg_foldx: 0.35
    plm_perplexity: 0.10
    priors: 0.15
  expression: 0.20
```

### Disable FoldX (faster):
```yaml
use_ddg_foldx: false
```

### Batch Processing:
```bash
for file in data/competition/*.fasta; do
  python -m src.cli --input "$file" --outdir "results/$(basename $file .fasta)"
done
```

---

## Contact & Support

System: petase-zero-shot
Version: v1.0 (FoldX-integrated)
Status: Competition-ready (95%)

