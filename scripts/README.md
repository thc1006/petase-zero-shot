# Submission Scripts

## Quick Start

### Predictive Phase Submission

When you receive the organizer's FASTA file, run:

```bash
./scripts/submit_predictive.sh path/to/organizer_sequences.fasta
```

**What it does:**

1. ✅ Runs the zero-shot pipeline with all channels:
   - PLM (ESM-2 pseudo-likelihood)
   - Solubility proxies (GRAVY, pI, charge, length)
   - **Biochemical priors (literature-derived)**

2. ✅ Validates output:
   - Checks column names match requirements
   - Ensures no NaN values
   - Verifies all scores in [0,1] range

3. ✅ Packages submission files with timestamp:
   - `submission/predictions_YYYYMMDD_HHMMSS.csv`
   - `submission/METHODS_YYYYMMDD_HHMMSS.md`
   - `submission/figures_YYYYMMDD_HHMMSS/` (3 histograms)

### Example Output

```
=========================================
PETase Zero-Shot Predictive Submission
=========================================
Input:  data/organizer_data.fasta
Output: runs/run_20251022_105559
Time:   20251022_105559
=========================================

[OK] wrote runs/run_20251022_105559/predictions.csv
[OK] predictions.csv validated (1250 sequences)
     Columns: ['seq_id', 'activity_score', 'stability_score', 'expression_score']
     No NaN values
     All scores in [0,1]

=========================================
[DONE] Submission files ready!
=========================================
  predictions: submission/predictions_20251022_105559.csv
  methods:     submission/METHODS_20251022_105559.md
  figures:     submission/figures_20251022_105559/
=========================================
```

## Configuration

Edit `config.yaml` to adjust:

- Feature toggles (`use_plm`, `use_priors`, etc.)
- Channel weights (`weights.activity.priors`, etc.)
- Priors YAML path (`priors_yaml`)

## Priors Channel

The **biochemical priors channel** (weighted at 20% activity, 15% stability) includes:

- **Hard constraints**: Catalytic triad (S160/H237/D206), oxyanion hole (87, 161)
- **Favorable regions**: β6-β7 loop, β8-α6 loop, N212 glycosylation site
- **Literature source**: 30+ peer-reviewed PETase variants (2024-2025)
- **Reference**: `data/priors/priors_petase_2024_2025.yaml`

All rules include DOI/PMID citations.

## Troubleshooting

### Script won't run

Make sure it's executable:
```bash
chmod +x scripts/submit_predictive.sh
```

### Dependencies missing

Install required packages:
```bash
pip install -r requirements.txt
```

### YAML loading error

Check that `data/priors/priors_petase_2024_2025.yaml` exists and is valid UTF-8.

## Directory Structure

```
petase-zero-shot/
├── scripts/
│   └── submit_predictive.sh  ← One-click submission script
├── submission/                ← Generated submission files (timestamped)
├── runs/                      ← Full pipeline outputs (timestamped)
├── data/
│   └── priors/                ← Literature-derived rules (YAML)
├── src/
│   ├── features/
│   │   └── priors.py          ← Priors scoring logic
│   └── pipelines/
│       └── run_all.py         ← Main pipeline orchestrator
└── config.yaml                ← Configuration & weights
```

## Zero-Shot Guarantee

✅ **No tournament data used**
✅ **No organizer-provided training labels**
✅ **All priors from public literature (2024-2025)**
✅ **Validated on external benchmarks only (ProteinGym)**

---

**Questions?** Check `METHODS.md` for detailed methodology.
