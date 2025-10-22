# FoldX Download Guide for Windows

## Your Link Analysis

Your link: `https://foldxsuite.crg.eu/node/732/download/3156f5ec328fc332e2bfb19ef66f89f6`

This appears to be **FoldX 5** for Windows (node 732 = Windows version).

## What You Need to Download

**For Windows, you want: FoldX 5 (Windows version)**

### Option 1: Use Your Direct Link (Recommended)
1. Open your browser (Chrome, Firefox, Edge)
2. Go to: https://foldxsuite.crg.eu/academic-license-info
3. **Accept the academic license agreement** (check the box)
4. Then paste your link:
   ```
   https://foldxsuite.crg.eu/node/732/download/3156f5ec328fc332e2bfb19ef66f89f6
   ```
5. This should download a ZIP file (~10-20 MB)

### Option 2: Manual Download from Website
1. Go to: https://foldxsuite.crg.eu/
2. Click "Download" → "Academic License"
3. Fill in your academic email and accept terms
4. Look for: **"FoldX 5 for Windows"** or **"FoldX5 Windows (64-bit)"**
5. Download the ZIP file

## What the ZIP Should Contain

After downloading and extracting, you should have:
```
foldx5.exe          (or foldx.exe)
rotabase.txt        (required database file)
README.txt          (optional)
```

## Where to Extract

Extract the contents to:
```
C:\Users\thc1006\Downloads\open-source\petase-zeroshot-pipeline\tools\foldx\
```

Final structure should be:
```
tools/foldx/
  ├── foldx5.exe           ← Main executable
  ├── rotabase.txt         ← Required database
  └── DOWNLOAD_GUIDE.md    ← This file
```

## Verify Installation

After extracting, open PowerShell/CMD in this directory and run:
```bash
cd tools/foldx
./foldx5 --version
```

Or:
```bash
./foldx5
```

You should see FoldX version info and help text.

## Common Issues

### Issue 1: "File not found" error
- Make sure you extracted the ZIP completely
- Check that foldx5.exe is directly in tools/foldx/ (not in a subfolder)

### Issue 2: ZIP contains a folder instead of files
If the ZIP has structure like:
```
foldx_windows/
  ├── foldx5.exe
  └── rotabase.txt
```

Then move the contents UP one level:
```bash
cd tools/foldx
mv foldx_windows/* .
rmdir foldx_windows
```

### Issue 3: "Cannot run executable" error
- Right-click foldx5.exe → Properties
- Check "Unblock" if there's a security warning
- Or run: `Unblock-File foldx5.exe` in PowerShell

### Issue 4: Download link redirects to login page
This means you need to accept the license first:
1. Go to: https://foldxsuite.crg.eu/academic-license-info
2. Read and accept the terms
3. Then try your download link again

## Alternative: Command Line Download (After Accepting License)

Once you've accepted the license in your browser, try:
```bash
cd tools/foldx
curl -L -o foldx5.zip "https://foldxsuite.crg.eu/node/732/download/3156f5ec328fc332e2bfb19ef66f89f6" --cookie-jar cookies.txt
unzip foldx5.zip
```

## What's Next (After Download)

Once FoldX is installed:
1. Tell me "FoldX ready"
2. I'll run: `python scripts/test_foldx.py`
3. Then run: `python scripts/run_foldx_ddg.py`
4. Expected result: ρ=0.63+ (Phase 1 complete!)

## Need Help?

If you encounter issues:
1. Screenshot the error message
2. Check what files are in `tools/foldx/` with: `ls tools/foldx`
3. Let me know what you see

## Quick Test

After download, test with:
```bash
cd tools/foldx
./foldx5 --help
```

Should show FoldX help text (not an error).
