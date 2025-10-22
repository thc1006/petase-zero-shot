# FoldX Download Instructions

The FoldX download requires manual steps due to license agreement.

## Steps to Download FoldX

1. **Visit the FoldX download page:**
   https://foldxsuite.crg.eu/academic-license-info

2. **Accept the academic license agreement**

3. **Download FoldX 5 for Windows:**
   - Direct link (after accepting license):
     https://foldxsuite.crg.eu/node/732/download/3156f5ec328fc332e2bfb19ef66f89f6

   OR

   - Go to: https://foldxsuite.crg.eu/
   - Click "Download" → "Academic License"
   - Download "FoldX 5" for Windows

4. **Extract to this directory:**
   ```
   C:\Users\thc1006\Downloads\open-source\petase-zeroshot-pipeline\tools\foldx\
   ```

5. **Expected files after extraction:**
   ```
   tools/foldx/
     ├── foldx.exe           (or foldx5.exe)
     ├── rotabase.txt        (required database file)
     └── README or LICENSE
   ```

## Alternative: Use Academic License Portal

If direct download doesn't work:

1. Visit: https://foldxsuite.crg.eu/academic-license-info
2. Fill in your academic email and institution
3. They will email you a download link
4. Extract to `tools/foldx/`

## Verify Installation

After downloading, run:
```bash
cd tools/foldx
./foldx --version
```

Or test with Python:
```python
python scripts/test_foldx.py
```

## Notes

- FoldX requires accepting academic license terms
- Windows version: foldx5.exe or foldx.exe
- License is free for academic use
- File size: ~10-20 MB

## Contact

If issues persist, email FoldX support:
support@foldxsuite.crg.eu
