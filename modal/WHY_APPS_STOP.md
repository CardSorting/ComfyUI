# Why Apps Keep Stopping - Investigation Guide

## Current Situation

You have many stopped `comfyui-api` apps, suggesting deployments are starting but then stopping/failing.

## Common Reasons Apps Stop

### 1. Build Failures
**Symptoms**: App stops shortly after starting
**Causes**:
- Build errors (missing dependencies, syntax errors)
- Network issues during PyTorch download
- Resource limits (GPU quota exceeded)
- Timeout during build

**How to Check**:
1. Go to Modal dashboard: https://modal.com/apps
2. Click on a stopped app
3. View build logs
4. Look for error messages

### 2. Runtime Initialization Failures
**Symptoms**: App builds successfully but stops when starting
**Causes**:
- ComfyUI initialization errors
- Missing models or dependencies
- Configuration issues
- Import errors

**How to Check**:
1. Check runtime logs (not build logs)
2. Look for Python errors
3. Check for missing imports

### 3. Client Timeout (Not Actually Stopped)
**Symptoms**: App appears stopped but is actually still building
**Causes**:
- CLI timeout (normal for long builds)
- Build continues on Modal servers

**How to Check**:
1. Check dashboard - if it shows "initializing" or "deploying", it's still building
2. Wait longer (15-20 minutes for first deployment)

### 4. Manual Stops
**Symptoms**: Apps stopped at specific times
**Causes**:
- You stopped them manually
- Auto-cleanup after inactivity
- Modal service issues

## Investigation Steps

### Step 1: Check Most Recent App

```bash
# Get the most recent app ID
modal app list | grep "comfyui-api" | head -1
```

Then check it in dashboard:
- https://modal.com/apps
- Click on the app
- View logs

### Step 2: Look for Patterns

Check if apps are stopping:
- **Immediately** → Build failure
- **After a few minutes** → Runtime error
- **After 15+ minutes** → Might be timeout (check dashboard)

### Step 3: Check Build Logs

In dashboard, look for:
- ✅ "Build completed successfully"
- ❌ Error messages
- ⚠️ Warnings about missing dependencies
- 🔄 "Still building..." (means it's not actually stopped)

### Step 4: Check Runtime Logs

If build succeeded, check runtime logs for:
- ComfyUI initialization errors
- Missing imports
- Configuration issues

## Common Issues and Fixes

### Issue: "GPU quota exceeded"
**Fix**: 
- Check Modal quota limits
- Wait for quota to reset
- Use smaller GPU (T4 instead of A10G)

### Issue: "PyTorch download timeout"
**Fix**:
- Retry deployment
- Check network connection
- Wait longer (PyTorch is ~2-3GB)

### Issue: "Import error: No module named X"
**Fix**:
- Check dependencies in `modal_app_fastapi.py`
- Ensure all required packages are in `.pip_install()`

### Issue: "ComfyUI initialization failed"
**Fix**:
- Check ComfyUI logs
- Verify model paths are correct
- Check for missing custom nodes

## Current Code Status

✅ **Fixed Issues**:
- Recursive loop (removed `Image.from_name()`)
- Secret handling (optional, graceful degradation)
- Image building (direct build, uses layer caching)

✅ **Should Work**:
- Builds from scratch (no recursive loops)
- Uses Modal's automatic layer caching
- Handles missing secrets gracefully

## Next Deployment

The current code should work. To deploy:

```bash
./modal/cleanup_and_redeploy.sh
```

Or:
```bash
modal deploy modal/apps/modal_app_fastapi.py
```

**Expected**:
- First deployment: 15-20 minutes
- Build should complete successfully
- App should reach "running" status

## If It Still Stops

1. **Check dashboard logs** - Most important!
2. **Look for specific errors** - Note the exact error message
3. **Check Modal status** - https://status.modal.com
4. **Try again** - Sometimes it's just a transient issue

## Prevention

1. **Monitor dashboard** during deployment
2. **Check logs** if app stops
3. **Wait for completion** - Don't assume it failed if CLI times out
4. **Clean up old apps** periodically (optional)

## Summary

Stopped apps don't block new deployments. The current code is fixed and should deploy successfully. If it stops again, check the dashboard logs to see why.

