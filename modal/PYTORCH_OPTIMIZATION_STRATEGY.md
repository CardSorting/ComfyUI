# PyTorch Installation Optimization Strategy

## Problem Statement

PyTorch installation during Modal deployments takes **10-15 minutes** and often causes:
- Client-side timeouts
- Stuck deployments
- Slow iteration cycles
- Unreliable builds

## Root Causes

1. **Large Download Size**: PyTorch with CUDA is ~2-3GB
2. **Network Speed**: Dependent on PyTorch CDN performance
3. **No Caching**: PyTorch rebuilt on every deployment
4. **Single Build**: Everything in one image, no layer separation

## Strategy Overview

We'll implement a **multi-layered approach** with multiple strategies you can choose from:

### Strategy 1: Base Image Caching (Recommended) ⭐
**Best for**: Regular deployments, fastest subsequent builds

### Strategy 2: Optimized PyTorch Installation
**Best for**: Single-build deployments, faster PyTorch install

### Strategy 3: Pre-built Image Registry
**Best for**: Team deployments, shared base images

### Strategy 4: Lazy PyTorch Loading
**Best for**: Minimal initial builds, load PyTorch on-demand

---

## Strategy 1: Base Image Caching (Recommended)

### Concept
Separate PyTorch installation into a reusable base image that's built once and cached.

### Benefits
- ✅ **First build**: 15-20 minutes (base image)
- ✅ **Subsequent builds**: 2-5 minutes (uses cached base)
- ✅ **Reliability**: Base image tested separately
- ✅ **Team sharing**: Base image can be shared across team

### Implementation

#### Step 1: Build Base Image (One-Time)
```bash
modal deploy modal/apps/base_image.py
```
**Time**: ~15-20 minutes (one time only)

#### Step 2: Update Main App to Use Base
The main app references the cached base image instead of installing PyTorch fresh.

**Time**: ~2-5 minutes (every deployment)

### Code Changes

**Before** (current - slow):
```python
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(...)
    .pip_install("torch", "torchvision", "torchaudio", ...)  # 10-15 min every time!
    .pip_install(...other deps...)
)
```

**After** (optimized - fast):
```python
# Reference cached base image
base_image = modal.Image.from_name("comfyui-base-image", create_if_missing=False)

image = (
    base_image  # PyTorch already installed, cached!
    .pip_install(...other deps...)  # Only 1-2 min
    .add_local_dir(...)
)
```

### Deployment Workflow

1. **Initial Setup** (one time):
   ```bash
   # Build base image with PyTorch
   modal deploy modal/apps/base_image.py
   # Wait ~15-20 minutes, monitor in dashboard
   ```

2. **Regular Deployments** (fast):
   ```bash
   # Deploy main app (uses cached base)
   modal deploy modal/apps/modal_app_fastapi.py
   # Only ~2-5 minutes!
   ```

3. **Update Base Image** (when PyTorch version changes):
   ```bash
   # Rebuild base image
   modal deploy modal/apps/base_image.py
   ```

---

## Strategy 2: Optimized PyTorch Installation

### Concept
Optimize the PyTorch installation process itself to be faster and more reliable.

### Techniques

#### A. Use Specific PyTorch Version
Instead of latest, pin a specific version for better caching:
```python
.pip_install(
    "torch==2.1.0",
    "torchvision==0.16.0", 
    "torchaudio==2.1.0",
    index_url="https://download.pytorch.org/whl/cu121"
)
```

#### B. Install PyTorch Components Separately
Install in optimal order for better layer caching:
```python
# Install torch first (largest, changes least)
.pip_install("torch", index_url="https://download.pytorch.org/whl/cu121")
# Then torchvision (depends on torch)
.pip_install("torchvision", index_url="https://download.pytorch.org/whl/cu121")
# Finally torchaudio (smallest)
.pip_install("torchaudio", index_url="https://download.pytorch.org/whl/cu121")
```

#### C. Use Alternative Index (if faster)
Try PyPI with CUDA wheels:
```python
.pip_install(
    "torch", "torchvision", "torchaudio",
    extra_index_url="https://download.pytorch.org/whl/cu121"
)
```

#### D. Add Retry Logic
Handle network issues gracefully:
```python
# Modal handles retries automatically, but we can add explicit retries
.pip_install(
    "torch", "torchvision", "torchaudio",
    index_url="https://download.pytorch.org/whl/cu121",
    # Modal will retry on failure automatically
)
```

### Benefits
- ✅ Faster PyTorch install (5-10 min vs 10-15 min)
- ✅ Better caching with pinned versions
- ✅ More reliable with retry logic

---

## Strategy 3: Pre-built Image Registry

### Concept
Build and publish base image to Modal's image registry, then reference it.

### Implementation

#### Step 1: Build and Deploy Base Image
```python
# In base_image.py
base_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(...)
    .pip_install("torch", "torchvision", "torchaudio", ...)
)

# Deploy to registry
base_image = base_image.deploy("comfyui-pytorch-base")
```

#### Step 2: Reference from Registry
```python
# In modal_app_fastapi.py
base_image = modal.Image.from_registry("comfyui-pytorch-base:latest")
```

### Benefits
- ✅ Shared across team/workspace
- ✅ Version control for base images
- ✅ Faster deployments (no build needed)

---

## Strategy 4: Lazy PyTorch Loading (Advanced)

### Concept
Don't install PyTorch in the image. Load it dynamically at runtime.

### Implementation
```python
# Install PyTorch at runtime, not build time
def install_pytorch():
    import subprocess
    subprocess.run([
        "pip", "install", "torch", "torchvision", "torchaudio",
        "--index-url", "https://download.pytorch.org/whl/cu121"
    ])

@app.function(...)
def web():
    # Install PyTorch on first run (cached in container)
    if not os.path.exists("/root/.pytorch_installed"):
        install_pytorch()
        os.makedirs("/root/.pytorch_installed")
    # ... rest of code
```

### Benefits
- ✅ Fast initial build (no PyTorch install)
- ✅ PyTorch cached in container after first run
- ✅ Good for testing/debugging

### Drawbacks
- ⚠️ Slower first cold start
- ⚠️ More complex code
- ⚠️ Not recommended for production

---

## Recommended Implementation Plan

### Phase 1: Immediate Fix (Strategy 1)
1. ✅ Update `modal_app_fastapi.py` to use base image
2. ✅ Deploy base image once
3. ✅ Test main app deployment

### Phase 2: Optimization (Strategy 2)
1. Pin PyTorch versions
2. Optimize installation order
3. Add better error handling

### Phase 3: Advanced (Strategy 3)
1. Set up image registry
2. Share base images across team
3. Version control base images

---

## Comparison Matrix

| Strategy | First Build | Subsequent Builds | Complexity | Reliability |
|----------|-------------|-------------------|------------|-------------|
| **Current** | 15-20 min | 15-20 min | Low | Medium |
| **Strategy 1** (Base Image) | 15-20 min | **2-5 min** | Medium | **High** |
| **Strategy 2** (Optimized) | 10-15 min | 10-15 min | Low | Medium |
| **Strategy 3** (Registry) | 15-20 min | **1-2 min** | High | **High** |
| **Strategy 4** (Lazy) | **2-5 min** | **2-5 min** | High | Low |

**Recommendation**: Start with **Strategy 1** (Base Image), it provides the best balance of speed, reliability, and simplicity.

---

## Migration Guide

### From Current to Strategy 1

1. **Deploy base image** (one time):
   ```bash
   modal deploy modal/apps/base_image.py
   ```

2. **Update main app** to use base image (see code changes above)

3. **Deploy main app**:
   ```bash
   modal deploy modal/apps/modal_app_fastapi.py
   ```

4. **Verify**:
   ```bash
   modal app list
   curl https://YOUR_ENDPOINT/
   ```

---

## Troubleshooting

### Issue: Base image not found
**Solution**: Deploy base image first:
```bash
modal deploy modal/apps/base_image.py
```

### Issue: Base image outdated
**Solution**: Rebuild base image:
```bash
modal deploy modal/apps/base_image.py --force
```

### Issue: Still slow after base image
**Solution**: Check if base image is actually being used (check build logs)

---

## Next Steps

1. ✅ Implement Strategy 1 (Base Image) - **Recommended first step**
2. ✅ Test deployment speed improvement
3. ✅ Document for team
4. ✅ Consider Strategy 3 for team deployments

