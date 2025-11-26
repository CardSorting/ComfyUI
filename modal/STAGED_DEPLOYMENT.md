# Staged Deployment Guide - Fix for Build Stalls

## Problem
The build stalls during PyTorch installation, causing deployments to fail or timeout.

## Solution: Staged Build

Split the build into two stages:
1. **Base Image** (build once): Contains PyTorch and system dependencies
2. **Main App** (build often): Contains ComfyUI code and other dependencies

This approach:
- ✅ Caches PyTorch installation (only build once)
- ✅ Faster subsequent deployments
- ✅ More reliable (base image can be tested separately)
- ✅ Avoids stalling on PyTorch installation

## Deployment Steps

### Step 1: Build Base Image (One-Time, ~15 minutes)

```bash
cd /Users/bozoegg/ComfyUI
modal deploy modal/apps/base_image.py
```

**What this does:**
- Installs system packages
- Installs PyTorch with CUDA (~10-15 min)
- Creates a reusable base image named `comfyui-base-image`
- This image is cached and reused

**Expected output:**
```
✓ Created objects.
├── 🔨 Created function test_pytorch.
✓ App deployed! 🎉

View your app at https://modal.com/apps/YOUR_WORKSPACE/comfyui-base-image
```

**Verify it worked:**
```bash
modal run modal/apps/base_image.py::test_pytorch
```

### Step 2: Deploy Main App (Fast, ~2-5 minutes)

```bash
cd /Users/bozoegg/ComfyUI
modal deploy modal/apps/modal_app_fastapi.py
```

**What this does:**
- Uses the cached base image (no PyTorch rebuild!)
- Installs remaining dependencies (~1-2 min)
- Adds ComfyUI code files (~1 min)
- Much faster because PyTorch is already built

**Expected output:**
```
✅ Using cached base image with PyTorch
✓ Created objects.
├── 🔨 Created function web.
├── 🔨 Created function download_model.
├── 🔨 Created function list_models.
└── 🔨 Created function delete_model.
✓ App deployed! 🎉

Web endpoint: https://YOUR_WORKSPACE--comfyui-api-web.modal.run
```

## Benefits

### Before (Single Build)
- **Time**: 15-20 minutes
- **Reliability**: Often stalls on PyTorch
- **Re-deploy**: 15-20 minutes every time

### After (Staged Build)
- **Base Image**: 15 minutes (one-time)
- **Main App**: 2-5 minutes (every deploy)
- **Reliability**: Base image tested separately
- **Re-deploy**: 2-5 minutes (much faster!)

## Troubleshooting

### Base Image Build Fails

If `base_image.py` deployment fails:

1. **Check logs**:
   ```bash
   modal app logs comfyui-base-image
   ```

2. **Common issues**:
   - Network timeout during PyTorch download
   - Solution: Try again, PyTorch download can be slow
   - Use Modal dashboard to monitor progress

3. **Retry**:
   ```bash
   modal deploy modal/apps/base_image.py
   ```

### Main App Can't Find Base Image

If you see "Base image not found":

1. **Check base image exists**:
   ```bash
   modal app list | grep base-image
   ```

2. **Rebuild base image**:
   ```bash
   modal deploy modal/apps/base_image.py
   ```

3. **Wait for completion** before deploying main app

### Still Stalling?

If builds still stall:

1. **Use Modal Dashboard**:
   - Go to https://modal.com/apps
   - Monitor build progress in real-time
   - Dashboard doesn't timeout like CLI

2. **Check network**:
   - Ensure stable internet connection
   - PyTorch download is ~2-3GB

3. **Try smaller GPU first**:
   - Change `GPU_CONFIG = "T4"` in `modal_app_fastapi.py`
   - T4 is cheaper and faster to provision
   - Upgrade to A10G later if needed

## Updating Base Image

If you need to update PyTorch version:

```bash
# Edit modal/apps/base_image.py
# Change PyTorch version or CUDA version
# Then redeploy:
modal deploy modal/apps/base_image.py
```

The main app will automatically use the new base image.

## Files

- **`modal/apps/base_image.py`**: Base image with PyTorch
- **`modal/apps/modal_app_fastapi.py`**: Main app (updated to use base image)

## Next Steps

1. ✅ Build base image: `modal deploy modal/apps/base_image.py`
2. ✅ Wait for completion (~15 min)
3. ✅ Deploy main app: `modal deploy modal/apps/modal_app_fastapi.py`
4. ✅ Test endpoint: `curl https://YOUR_ENDPOINT/`

## Summary

**Staged deployment solves the stalling issue by:**
- Building PyTorch separately (one-time, can monitor closely)
- Caching the result (reused for all future deployments)
- Making main app deployments fast (2-5 min vs 15-20 min)
- Improving reliability (base image tested independently)

This is the recommended approach for production deployments!

