# Download Linux FoldX (You Have License!)

Since you have the FoldX license, download the Linux version now:

## Quick Download (With Your License)

### Method 1: Direct Download in WSL
```bash
# Open WSL
wsl

# Navigate to project
cd /mnt/c/Users/thc1006/Desktop/dev/petase-zero-shot/tools/foldx

# Download Linux FoldX (your license allows this)
wget https://foldxsuite.crg.eu/sites/default/files/FoldX/FoldX5Linux64.tar_.gz -O foldx_linux.tar.gz

# Extract
tar -xzf foldx_linux.tar.gz

# Make executable
chmod +x foldx

# Test
./foldx --version
```

### Method 2: Manual Download (If wget doesn't work)
1. In browser, visit: https://foldxsuite.crg.eu/node/731
2. Login with your license credentials
3. Download "FoldX 5 Linux (64-bit)"
4. Move downloaded file to: `C:\Users\thc1006\Desktop\dev\petase-zero-shot\tools\foldx\`
5. Extract in WSL:
```bash
wsl
cd /mnt/c/Users/thc1006/Desktop/dev/petase-zero-shot/tools/foldx
tar -xzf foldx_linux.tar.gz
chmod +x foldx
```

## Expected Result
You should see:
```
********************************************
   ***             FoldX 5 (c)            ***
********************************************
```

Then I'll enable it in the config and run predictions!
