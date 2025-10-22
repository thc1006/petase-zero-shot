# PETase Zero-Shot Ensemble - Quick Start Guide

## 🚀 One-Click Submission (Predictive Phase)

收到主辦方的 FASTA 檔案後，執行：

```bash
./scripts/submit_predictive.sh path/to/organizer_sequences.fasta
```

**輸出檔案** (自動生成在 `submission/` 目錄):
- `predictions_YYYYMMDD_HHMMSS.csv` → 提交給主辦方
- `METHODS_YYYYMMDD_HHMMSS.md` → 方法說明文件
- `figures_YYYYMMDD_HHMMSS/` → 分數分布直方圖

---

## 📊 模型架構（含先驗通道）

### Activity Score
1. **PLM Pseudo-likelihood** (55%) - ESM-2 zero-shot
2. **GEMME ΔE** (25%) - 演化限制 [可選]
3. **⭐ Biochemical Priors** (20%) - 文獻驅動規則
   - 催化三聯體保護 (S160/H237/D206)
   - 氧陰離子洞保護 (87, 161)
   - 有利區域獎勵 (β6-β7 loop, β8-α6 loop, N212, etc.)

### Stability Score
1. **ΔΔG Predictors** (75%) - FoldX/Rosetta/DeepDDG [可選]
2. **PLM Perplexity** (10%) - 序列似然代理
3. **⭐ Biochemical Priors** (15%) - 穩定性規則
   - 鹽橋、迴圈穩定、Ca²⁺ 結合
   - 二硫鍵、表面疏水性調控

### Expression Score
1. **Solubility Proxies** (70%) - GRAVY, pI, 電荷平衡, 長度
2. **Disorder Penalty** (30%) - IUPred 預測 [可選]

### 集成方法
- Median/MAD robust scaling
- Rank averaging with configurable weights
- Min-max normalization to [0,1]

---

## 📚 文獻先驗來源

**資料集**: `data/priors/priors_petase_2024_2025.yaml`

**30+ 篇 2024-2025 年 PETase 文獻**，包含：
- Nature Communications (Bhr-NMT, LCC-ICCG-NM, Kubu-P-NM)
- ACS Catalysis (91 novel ML-guided PETases)
- Journal of Hazardous Materials (YITA, LCC variants)
- Biomolecules (S1v1-FAST-PETase peptide tags)
- ChemBioChem (AroC thermophile, UVO pretreatment)

**每條規則都附帶 DOI/PMID 引用**，可追溯驗證。

---

## ✅ 驗證檢查

腳本自動執行：
1. ✓ 欄位檢查: `seq_id`, `activity_score`, `stability_score`, `expression_score`
2. ✓ NaN 檢查: 無缺失值
3. ✓ 範圍檢查: 所有分數在 [0,1]

---

## 🔧 進階配置

編輯 `config.yaml` 調整：

```yaml
# 功能開關
use_plm: true
use_priors: true
use_gemme: false      # 需要 MSA
use_ddg_foldx: false  # 需要 FoldX
use_disorder: false   # 需要 IUPred

# 先驗配置
priors_yaml: data/priors/priors_petase_2024_2025.yaml

# 權重（可微調）
weights:
  activity:
    plm_llr: 0.55
    priors: 0.20
  stability:
    plm_perplexity: 0.10
    priors: 0.15
```

---

## 📁 專案結構

```
petase-zero-shot/
├── scripts/
│   ├── submit_predictive.sh    ← 一鍵提交腳本
│   └── README.md               ← 腳本說明
├── data/
│   ├── priors/
│   │   └── priors_petase_2024_2025.yaml  ← 文獻規則（30 篇論文）
│   └── templates/
│       └── example_sequences.fasta
├── src/
│   ├── features/
│   │   ├── priors.py           ← 先驗計算邏輯
│   │   ├── plm_llr.py          ← ESM-2 pseudo-likelihood
│   │   └── solubility.py       ← 物化特性代理
│   ├── pipelines/
│   │   └── run_all.py          ← 主管線
│   └── ensemble/
│       └── aggregate.py        ← 分數融合
├── submission/                 ← 提交檔案（時間戳）
├── runs/                       ← 完整輸出（時間戳）
├── reports/
│   ├── petase_zero_shot_results.xlsx    ← 整合報告
│   └── petase_zero_shot_deck.pptx       ← 投影片
└── config.yaml                 ← 配置與權重
```

---

## 🎯 Zero-Shot 保證

✅ **完全無訓練資料汙染**
- 無使用任何主辦方提供的訓練標籤
- 無在 tournament data 上調參
- PLM 為預訓練模型（非微調）
- 先驗規則來自公開文獻（2024-2025）

✅ **外部驗證**
- ProteinGym benchmark
- 文獻複現實驗

---

## 📊 已生成的報告

### Excel 整合報告
`reports/petase_zero_shot_results.xlsx`
- Sheet 1: predictions (本次預測)
- Sheet 2: literature_2024_2025 (30 篇文獻摘要)

### PowerPoint 投影片
`reports/petase_zero_shot_deck.pptx`
- Slide 1: 標題（Zero-Shot Ensemble for PETase）
- Slide 2: Pipeline Flow（流程圖）
- Slide 3: Biochemical Priors（關鍵先驗）
- Slide 4: Score Distributions（分數分布圖）

---

## 🐛 故障排除

### 權限錯誤
```bash
chmod +x scripts/submit_predictive.sh
```

### 依賴缺失
```bash
pip install -r requirements.txt
```

### YAML 編碼錯誤
確保檔案為 UTF-8 編碼（已修正 `methods_scaffold.py` 和 `priors.py`）

### Bio.pairwise2 棄用警告
這是正常的 Biopython 警告，不影響功能（可考慮未來遷移至 `Bio.Align.PairwiseAligner`）

---

## 📧 聯絡資訊

**作者**: 蔡秀吉
**專案**: PETase Zero-Shot Ensemble (Predictive Phase)
**日期**: 2025-10-22

---

**準備好了嗎？執行 `./scripts/submit_predictive.sh your_sequences.fasta` 開始預測！** 🚀
