# Recursive Build Loop - Root Cause & Fix

## The Problem

The Modal deployment was getting stuck in a recursive build loop, where the app would:
1. Start building
2. Fail during initialization
3. Try to rebuild
4. Fail again
5. Repeat...

This resulted in many "stopped" apps in your Modal dashboard.

## Root Causes Identified

### 1. Module-Level Secret Resolution (PRIMARY CAUSE)

**Location**: Lines 169-179 of `modal_app_fastapi.py`

**Issue**: `modal.Secret.from_name()` calls were executed at **module load time** (during import), not at runtime. This happens every time Modal loads your module to:
- Parse function decorators
- Build the image
- Deploy the app

If the Modal API has any transient issues resolving secrets during this phase, it can cause the module import to fail, triggering a rebuild.

```python
# PROBLEMATIC - Runs at module import time
secrets_list = []
try:
    b2_secret = modal.Secret.from_name("backblaze-b2-credentials")
    secrets_list.append(b2_secret)
except Exception:
    pass  # Still runs at import time!
```

### 2. Relative Path Resolution

**Location**: Line 60-61 of `modal_app_fastapi.py`

**Issue**: The relative path `"../.."` in `add_local_dir()` is resolved relative to the current working directory when Modal runs, which may differ between local and remote contexts.

```python
# PROBLEMATIC - Relative path
.add_local_dir(
    "../..",  # Resolved differently in different contexts
    remote_path="/app",
    ...
)
```

### 3. Print Statements During Module Load

**Location**: Lines 182-193 of `modal_app_fastapi.py`

**Issue**: Print statements and conditional logic executed at module load time can cause unexpected behavior during the build phase.

## The Fix

Created `modal_app_fastapi_fixed.py` with these changes:

### Fix 1: Lazy Secret Resolution

Moved secret resolution into a function that's called only when needed:

```python
def _get_secrets_list():
    """Get secrets lazily - only called when actually needed."""
    secrets = []
    try:
        b2_secret = modal.Secret.from_name("backblaze-b2-credentials", create_if_missing=False)
        secrets.append(b2_secret)
    except Exception:
        pass
    # ...
    return secrets

# Used in decorator - resolved at decoration time, not module load
@app.function(
    secrets=_get_secrets_list(),
    ...
)
```

### Fix 2: Absolute Path for Local Directory

Used `pathlib.Path` to get the absolute path:

```python
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
COMFYUI_ROOT = SCRIPT_DIR.parent.parent

image = (
    modal.Image.debian_slim(python_version="3.11")
    # ...
    .add_local_dir(
        str(COMFYUI_ROOT),  # Absolute path
        remote_path="/app",
        ...
    )
)
```

### Fix 3: Removed Module-Level Print Statements

All print statements are now inside functions, not at module scope.

## How to Deploy

```bash
# Deploy the fixed version
modal deploy modal/apps/modal_app_fastapi_fixed.py

# Or use the original version (may still have issues)
modal deploy modal/apps/modal_app_fastapi.py
```

## Expected Behavior After Fix

1. **First deployment**: ~15-20 minutes (PyTorch installation)
2. **Subsequent deployments**: ~5-10 minutes (layer caching)
3. **No more recursive loops**: Module loads cleanly
4. **Secrets are optional**: App works with or without B2/Civitai secrets

## Verification

After deployment, check:

1. **Modal dashboard**: https://modal.com/apps
   - App should show "deployed" status
   - No new stopped apps appearing

2. **API health check**:
   ```bash
   curl https://YOUR_WORKSPACE--comfyui-api-web.modal.run/
   ```

3. **System stats**:
   ```bash
   curl https://YOUR_WORKSPACE--comfyui-api-web.modal.run/system_stats
   ```

## If Issues Persist

1. Check Modal dashboard logs for specific errors
2. Ensure you're deploying the fixed version (`modal_app_fastapi_fixed.py`)
3. Check Modal status: https://status.modal.com
4. Try stopping all apps and deploying fresh:
   ```bash
   modal app stop comfyui-api
   modal deploy modal/apps/modal_app_fastapi_fixed.py
   ```

