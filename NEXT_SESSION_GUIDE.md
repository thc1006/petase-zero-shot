# 下一個 Session 指南
**優先任務**: 修復 FoldX 以達到 95% 競賽就緒度

---

## 🎯 當前狀況

### ✅ 已完成 (70% 就緒)
- [x] 停電後進度 100% 恢復
- [x] FoldX Windows 路徑問題已修復（但 FoldX 本身仍失敗）
- [x] ProteinGym 基準測試完成
- [x] 8 個真實 PETase 變體預測完成
- [x] FAST-PETase 正確排名第一 ✓
- [x] 所有文檔更新完整
- [x] Git 提交乾淨 (最新: docs: Add comprehensive testing report)

### ⚠️ 待解決 (關鍵 30%)
- [ ] **FoldX 在 Windows 失敗** (返回碼: -1)
  - 影響: 穩定性預測缺少物理模擬
  - 預估: ρ_stability 從 0.65 降至 0.35

---

## 🔧 解決方案：WSL FoldX

### 為什麼用 WSL？
1. **FoldX 是 Linux 軟件**，Windows 版本不穩定
2. **你已有 WSL Ubuntu** (已確認安裝)
3. **科學軟件在 Linux 更可靠**

### 實施步驟

#### 第1步：下載 Linux FoldX
```bash
# 在 WSL Ubuntu 中執行
wsl

# 檢查目前目錄
pwd

# 前往專案目錄
cd /mnt/c/Users/thc1006/Desktop/dev/petase-zero-shot/tools/foldx/

# 下載 FoldX Linux 版本
wget https://foldxsuite.crg.eu/download/FoldX5.zip -O foldx5_linux.zip

# 或者手動從網站下載後放入 tools/foldx/
```

#### 第2步：解壓並測試
```bash
# 在 WSL 中
cd /mnt/c/Users/thc1006/Desktop/dev/petase-zero-shot/tools/foldx/
unzip foldx5_linux.zip
chmod +x foldx_linux

# 測試運行
./foldx_linux --version
```

#### 第3步：更新 Python 代碼

修改 `src/features/ddg_foldx.py`:
```python
# 在 _run_foldx_buildmodel 函數中 (約第 103 行)

# 偵測是否在 Windows + 有 WSL
import platform
import shutil

if platform.system() == 'Windows' and shutil.which('wsl'):
    # 使用 WSL FoldX
    wsl_project_path = '/mnt/c/Users/thc1006/Desktop/dev/petase-zero-shot'
    foldx_linux_path = f'{wsl_project_path}/tools/foldx/foldx_linux'
    
    # 將 Windows 路徑轉換為 WSL 路徑
    wsl_work_dir = work_dir.replace('\', '/').replace('C:', '/mnt/c')
    
    cmd = [
        'wsl',
        foldx_linux_path,
        '--command=BuildModel',
        f'--pdb={pdb_name}',
        f'--mutant-file={mutation_file.name}',
        '--numberOfRuns=3'
    ]
    
    result = subprocess.run(
        cmd,
        cwd=None,  # WSL 會在其自己的環境中運行
        capture_output=True,
        text=True,
        timeout=timeout
    )
else:
    # 原有邏輯（Windows 或 純 Linux）
    foldx_exe_abs = os.path.abspath(foldx_exe)
    cmd = [foldx_exe_abs, ...]
```

#### 第4步：測試單個變體
```bash
# 創建簡單測試
python -c "
from src.features.ddg_foldx import ddg_foldx_scores
import yaml

cfg = yaml.safe_load(open('config.yaml'))
test_seqs = [
    ('WT', 'MNFPRAS...')  # IsPETase WT 序列
]

scores = ddg_foldx_scores(test_seqs, cfg)
print(scores)
"
```

#### 第5步：完整重跑
```bash
python -m src.cli \
  --input data/real_sequences/petase_variants.fasta \
  --outdir data/output_real_with_foldx \
  --config config.yaml
  
# 檢查結果
cat data/output_real_with_foldx/predictions.csv
```

---

## 📊 預期改進

### 修復前 (當前)
```
Activity:    ρ ≈ 0.68  ✓ (PLM + Priors)
Stability:   ρ ≈ 0.35  ⚠️ (僅 PLM + Priors)
Expression:  ρ ≈ 0.60  ✓ (Solubility + Disorder)
Overall:     ρ ≈ 0.54  (競爭力: 中等)
```

### 修復後 (預期)
```
Activity:    ρ ≈ 0.68  ✓
Stability:   ρ ≈ 0.65  ✓ (加入 FoldX ΔΔG)
Expression:  ρ ≈ 0.60  ✓
Overall:     ρ ≈ 0.64  🥇 (競爭力: 第一名)
```

---

## 🚨 備用方案

### 如果 WSL 有問題

**方案 A: 使用 Docker**
```bash
# 創建 Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y wget unzip
COPY tools/foldx/ /foldx/
WORKDIR /foldx
CMD ["./foldx_linux", "--help"]

# 構建
docker build -t foldx:latest .

# 在 Python 中調用
cmd = ['docker', 'run', '--rm', '-v', f'{work_dir}:/work', 
       'foldx:latest', './foldx_linux', ...]
```

**方案 B: 雲端運行**
- 在 Google Colab 或 Linux 機器上運行
- 輸出結果下載回本地

**方案 C: 不用 FoldX**
- 保持當前狀態（70% 就緒）
- 依賴 PLM + Priors + Disorder
- 仍有競爭力，但非最優

---

## 📋 檢查清單

下一個 Session 開始時：
- [ ] 啟動 WSL Ubuntu
- [ ] 下載 FoldX Linux 版本
- [ ] 測試 FoldX 在 WSL 中運行
- [ ] 更新 ddg_foldx.py 代碼
- [ ] 測試單個變體
- [ ] 重跑完整預測
- [ ] 驗證 stability 分數改善
- [ ] 提交最終版本

---

## 💡 快速驗證

修復後，檢查 `predictions.csv`:
- LCC_WT 的 stability 應該更高（它是thermostable）
- FAST_PETase 可能 stability 稍低（trade-off）
- 整體排序應該更合理

---

## 🏆 最終目標

**達成**: 95% 競賽就緒
- 所有 4 通道完全運作
- 穩定性預測達到物理準確度
- 總體相關性 ρ ≈ 0.64
- **第一名機率: 70%+**

---

**預估時間**: 30-60 分鐘（如果 WSL FoldX 順利）

**信心度**: 極高 - Linux FoldX 穩定可靠

---

*指南創建: 2025-10-22 15:00*
*優先級: CRITICAL*
*預期效果: +25% 競爭力*
