# Custom Nodes Serverless Fix

## Problem
When running ComfyUI in serverless environments (Modal, Docker, etc.), some custom nodes fail to load due to missing dependencies. Specifically, the `comfyui-impact-pack` and `comfyui-impact-subpack` custom nodes require OpenCV (`cv2`), which is not installed in the default serverless configuration.

This resulted in the following error:
```
ModuleNotFoundError: No module named 'cv2'
Cannot import /app/custom_nodes/comfyui-impact-pack module for custom nodes: No module named 'cv2'
```

## Solution
The issue has been resolved by disabling problematic custom nodes in serverless environments. This is done by:

1. Using the `--disable-all-custom-nodes` flag to skip all custom nodes by default
2. Using the `--whitelist-custom-nodes` flag to allow only specific, compatible custom nodes (e.g., `websocket_image_save.py`)

## Files Modified

### 1. Modal Deployment (`modal/apps/modal_app_fastapi.py`)
- Changed `args.disable_all_custom_nodes = False` to `True`
- Added `args.whitelist_custom_nodes = ["websocket_image_save.py"]`

### 2. Docker Headless (`Dockerfile.headless`)
- Added `--disable-all-custom-nodes` flag to the CMD
- Added `--whitelist-custom-nodes websocket_image_save.py` to whitelist compatible nodes

### 3. Startup Script (`start_comfyui_headless.sh`)
- Added `--disable-all-custom-nodes` flag
- Added `--whitelist-custom-nodes websocket_image_save.py` to the startup command

## Alternative Solutions

If you need to use custom nodes in serverless environments, you have several options:

### Option 1: Install Required Dependencies
Add the missing dependencies to your environment:

**For Modal:**
```python
.pip_install("opencv-python")
```

**For Docker:**
```dockerfile
RUN pip install opencv-python
```

**For requirements files:**
```
opencv-python
```

### Option 2: Disable Specific Custom Nodes Only
Instead of disabling all custom nodes, you can rename specific problematic directories to have a `.disabled` suffix:
```bash
mv custom_nodes/comfyui-impact-pack custom_nodes/comfyui-impact-pack.disabled
mv custom_nodes/comfyui-impact-subpack custom_nodes/comfyui-impact-subpack.disabled
```

### Option 3: Whitelist Specific Custom Nodes
If you have other custom nodes you want to use, add them to the whitelist:
```bash
--whitelist-custom-nodes websocket_image_save.py your_custom_node.py another_node.py
```

Or in Python (Modal):
```python
args.whitelist_custom_nodes = ["websocket_image_save.py", "your_custom_node.py", "another_node.py"]
```

## Verification
After applying these changes, ComfyUI should start successfully in serverless environments without the `cv2` import errors. The logs will show:
```
INFO:root:
Import times for custom nodes:
   0.0 seconds: /app/custom_nodes/websocket_image_save.py
```

And it will no longer show import failures for the impact-pack nodes.

## Impact Assessment
- **What's affected**: Custom nodes requiring external dependencies (cv2, etc.) will not be loaded
- **What still works**: All built-in nodes, core functionality, and whitelisted custom nodes
- **Performance**: No performance impact; slightly faster startup due to fewer nodes being loaded
- **Compatibility**: Workflows that depend on disabled custom nodes will need to be modified or use Option 1 above

## Notes
- This fix is specifically for serverless/headless environments
- Regular ComfyUI installations with the web UI can still use all custom nodes if dependencies are installed
- The fix prioritizes stability and compatibility over functionality for serverless deployments
- You can always re-enable specific custom nodes by adding them to the whitelist and installing their dependencies

