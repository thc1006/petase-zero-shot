# PETase Zero‑Shot Skill (AlignBio 2025 — Predictive Phase, Zero‑Shot)

This package lets you compute **activity / thermostability / expression** predictions for PETase variants **without any tournament training data** and produce a submission CSV + METHODS scaffold + figures.

### Run

```bash
pip install -r requirements.txt
# (Optional) for protein language models (faster/better): pip install -r requirements-plm.txt

python -m src.cli --input data/input/sequences.fasta --outdir data/output --config config.yaml
```

- Edit `.env.example` → `.env` to point to optional external tools (GEMME, FoldX, Rosetta, IUPred, etc.).
- If a channel is unavailable, the pipeline **skips it gracefully** and still produces predictions via rank‑average of available channels.

### Outputs
- `data/output/predictions.csv` — columns: `seq_id,activity_score,stability_score,expression_score` on \[0,1].
- `data/output/METHODS.md` — zero‑shot description scaffold with citations.
- `data/output/figures/*.png` — histograms of property scores.

### Design
- **Activity**: ESM‑style pseudo‑likelihood (zero‑shot) ± GEMME ΔE (optional).
- **Stability**: ΔΔG (FoldX / Rosetta / DeepDDG, optional) + PLM pseudo‑perplexity proxy.
- **Expression**: Solubility/aggregation/disorder proxies (sequence features only).
- **Fusion**: Robust scaling (median/MAD) → rank‑average with configurable weights → min‑max to \[0,1].

> This repo is a **scaffold**. For best results, connect real tools (e.g., fair‑esm, GEMME, FoldX) before the Predictive Phase begins.


This package contains **official-practice–aligned instruction sets** designed from Anthropic’s Help Center guidance for **Claude for Life Sciences** Connectors and **Skills**, and the documented **Claude Code** plugin/MCP commands.

> Use these files as-is in Claude chat, Claude Code, or upload the included Skill ZIP folder via **Settings → Capabilities → Skills**.

## Contents
- `prompts/claude-chat/petase_lit_scan_prompt.txt` — a copy/paste prompt for Claude (with PubMed & Scholar Gateway connectors enabled).
- `prompts/claude-code/petase_mcp_commands.txt` — the documented commands to add the Anthropic Life Sciences marketplace and install PubMed/Scholar connectors in **Claude Code**.
- `skills/petase-2024-2025-lit-scan/` — a **Skill** you can upload to Claude to make this a one-click workflow.
  - `SKILL.md` — the core skill instructions (YAML metadata + body).
  - `resources/query-strings.md` — curated advanced queries for PubMed and Scholar.
  - `resources/output-schema.csv` — the target extraction schema for the summary table.

## Install / Use (per official docs)
1) **Claude Code (MCP)** — In a Claude Code chat, run the commands in `prompts/claude-code/petase_mcp_commands.txt`.  
2) **Claude.ai (Connectors)** — Go to **Settings → Connectors** and connect *PubMed* and *Scholar Gateway*.  
3) **Skills** — Go to **Settings → Capabilities → Skills → Upload skill**, and select the folder `skills/petase-2024-2025-lit-scan` (zip the folder first if needed).

> Notes: Prompts/commands are composed to reflect Anthropic’s current official guidance for Connectors, Skills, and Claude Code plugin usage (as of 2025-10-21).
