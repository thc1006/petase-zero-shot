@echo off
REM FoldX WSL Wrapper for Windows
REM Calls Linux FoldX via WSL

wsl bash -c "cd /mnt/c/Users/thc1006/Desktop/dev/petase-zero-shot && /mnt/c/Users/thc1006/Desktop/dev/petase-zero-shot/tools/foldx/foldx_20251231 %*"
