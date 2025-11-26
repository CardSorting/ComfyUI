# Quick Start: Optimized PyTorch Deployment

## The Problem
PyTorch installation takes 10-15 minutes every deployment, causing timeouts and slow iteration.

## The Solution
Use a **cached base image** with PyTorch pre-installed. This reduces deployment time from **15-20 minutes to 2-5 minutes**.

## Quick Setup (2 Steps)

### Step 1: Deploy Base Image (One-Time, ~15-20 min)

```bash
cd /Users/bozoegg/ComfyUI
modal deploy modal/apps/base_image.py
```

**What this does:**
- Installs system packages
- Installs PyTorch with CUDA (~10-15 min)
- Creates a cached base image named `comfyui-base-image`
- **This only needs to be done once!**

**Monitor progress:**
- Dashboard: https://modal.com/apps
- Even if CLI times out, build continues on Modal servers

### Step 2: Deploy Main App (Fast, ~2-5 min)

```bash
modal deploy modal/apps/modal_app_fastapi.py
```

**What this does:**
- Uses the cached base image (no PyTorch rebuild!)
- Installs remaining dependencies (~1-2 min)
- Adds ComfyUI code files (~1 min)
- **Much faster because PyTorch is already built**

## Automated Script

Or use the automated script:

```bash
./modal/deploy_with_base_image.sh
```

This script:
- ✅ Checks if base image exists
- ✅ Deploys base image if needed
- ✅ Deploys main app using cached base
- ✅ Handles timeouts gracefully

## Speed Comparison

| Deployment | Time | Notes |
|------------|------|-------|
| **Without base image** | 15-20 min | PyTorch installed every time |
| **With base image** | 2-5 min | PyTorch cached, only app code changes |

## When to Rebuild Base Image

Rebuild the base image only when:
- PyTorch version needs updating
- System dependencies change
- Base image becomes corrupted

```bash
# Force rebuild base image
modal deploy modal/apps/base_image.py
```

## Troubleshooting

### "Base image not found"
**Solution**: Deploy base image first:
```bash
modal deploy modal/apps/base_image.py
```

### "Still slow after base image"
**Check**: Verify base image is being used:
- Check build logs in dashboard
- Look for "Using cached base image" message

### "Base image outdated"
**Solution**: Rebuild base image:
```bash
modal deploy modal/apps/base_image.py
```

## Next Steps

1. ✅ Deploy base image (one time)
2. ✅ Deploy main app (fast!)
3. ✅ Enjoy 2-5 minute deployments instead of 15-20 minutes!

## Full Documentation

See `modal/PYTORCH_OPTIMIZATION_STRATEGY.md` for:
- Detailed strategy explanations
- Alternative approaches
- Advanced optimization techniques

