# Plugin Migration Guide

This guide explains how to migrate from standalone scripts to the ComfyUI Serverless plugin, and how to keep the plugin updated for future ComfyUI releases.

## Overview

The ComfyUI Serverless plugin (`custom_nodes/comfyui-serverless/`) provides:
- Headless mode utilities
- Modal.com deployment support
- Model download nodes (Civitai, HuggingFace)
- Easy migration path for future ComfyUI versions

## Current State vs Plugin State

### Before (Standalone Scripts)

```
ComfyUI/
├── main_headless.py              # Headless startup
├── civitai_integration.py        # Civitai downloads
├── huggingface_integration.py    # HuggingFace downloads
└── modal/
    └── apps/
        └── modal_app_fastapi.py  # Modal deployment
```

### After (Plugin + Standalone)

```
ComfyUI/
├── main_headless.py              # Still works (backward compatible)
├── civitai_integration.py        # Still works (imported by plugin)
├── huggingface_integration.py    # Still works (imported by plugin)
├── modal/
│   └── apps/
│       └── modal_app_fastapi.py # Can use plugin utilities
└── custom_nodes/
    └── comfyui-serverless/       # NEW: Plugin
        ├── __init__.py
        ├── extension.py
        ├── nodes/
        ├── integrations/
        └── serverless/
```

## Migration Steps

### Step 1: Verify Plugin Structure

The plugin should already be in place at:
```
custom_nodes/comfyui-serverless/
```

If not, ensure all files from the investigation are present.

### Step 2: Test Plugin Loading

Start ComfyUI and check logs for:
```
Loading ComfyUI Serverless Plugin v0.1.0
ComfyUI Serverless Extension: on_load() called
ComfyUI Serverless Extension: Providing 3 nodes
```

### Step 3: Update Your Code

#### Using Headless Mode

**Before:**
```python
# main_headless.py
os.environ['COMFYUI_HEADLESS'] = '1'
import main
```

**After (still works):**
```python
# main_headless.py - No changes needed!
os.environ['COMFYUI_HEADLESS'] = '1'
import main
```

**New option (programmatic):**
```python
from custom_nodes.comfyui_serverless.serverless.headless_utils import configure_headless_mode

configure_headless_mode(enable=True)
import main
```

#### Using Model Downloads

**Before:**
```python
from civitai_integration import CivitaiModelManager
manager = CivitaiModelManager()
manager.download_from_url(url)
```

**After (still works):**
```python
# Still works - plugin imports from main codebase
from civitai_integration import CivitaiModelManager
manager = CivitaiModelManager()
manager.download_from_url(url)
```

**New option (via plugin):**
```python
from custom_nodes.comfyui_serverless.integrations.civitai import CivitaiModelManager
manager = CivitaiModelManager()
manager.download_from_url(url)
```

**New option (via ComfyUI nodes):**
Use the `CivitaiDownload`, `HuggingFaceDownload`, or `GenericModelDownload` nodes in workflows.

#### Using Modal Deployment

**Before:**
```python
# modal/apps/modal_app_fastapi.py
# Full Modal app code...
```

**After (enhanced):**
```python
# modal/apps/modal_app_fastapi.py
from custom_nodes.comfyui_serverless.serverless.headless_utils import setup_headless_environment

# In your Modal function:
setup_headless_environment()  # Use plugin utility
# ... rest of your code
```

**New option (generate template):**
```python
from custom_nodes.comfyui_serverless.serverless.modal_host import create_modal_comfyui_app

modal_code = create_modal_comfyui_app(
    app_name="my-comfyui",
    comfyui_root="/path/to/ComfyUI"
)
# Save and customize as needed
```

## Updating for New ComfyUI Versions

### Strategy 1: API Compatibility (Recommended)

The plugin uses ComfyUI's stable extension API (V3), which should remain compatible across versions. Most updates won't require changes.

### Strategy 2: Version Detection

If needed, the plugin can detect ComfyUI version and adapt:

```python
# In extension.py
import comfyui_version

COMFYUI_VERSION = getattr(comfyui_version, 'version', 'unknown')

if COMFYUI_VERSION >= '0.4.0':
    # Use new API features
    pass
else:
    # Use older API
    pass
```

### Strategy 3: Import Compatibility

The plugin imports from the main codebase, so if ComfyUI changes:
1. Update imports in `integrations/civitai.py` and `integrations/huggingface.py`
2. Update node implementations in `nodes/model_download.py` if ComfyUI node API changes
3. Test with new ComfyUI version

### Update Checklist

When updating ComfyUI:

1. **Test Plugin Loading**
   ```bash
   python main.py --headless
   # Check logs for plugin loading
   ```

2. **Test Nodes**
   - Verify model download nodes appear in ComfyUI
   - Test downloading a model via node

3. **Test Headless Mode**
   ```bash
   export COMFYUI_HEADLESS=1
   python main.py
   ```

4. **Test Modal Deployment** (if using)
   - Generate new Modal template
   - Test deployment

5. **Update Documentation**
   - Note any breaking changes
   - Update version compatibility

## Troubleshooting

### Plugin Not Loading

**Symptom**: No plugin messages in logs

**Solutions**:
1. Check `custom_nodes/comfyui-serverless/__init__.py` exists
2. Check `comfy_entrypoint()` function is defined
3. Check for import errors in logs

### Import Errors

**Symptom**: `ImportError` when loading plugin

**Solutions**:
1. Ensure `civitai_integration.py` and `huggingface_integration.py` exist in ComfyUI root
2. Install missing dependencies: `pip install huggingface_hub`
3. Check Python path includes ComfyUI root

### Nodes Not Appearing

**Symptom**: Model download nodes don't appear in ComfyUI

**Solutions**:
1. Check extension is loading (see logs)
2. Check `get_node_list()` returns nodes
3. Verify node schemas are valid
4. Check for errors in node definitions

### Headless Mode Not Working

**Symptom**: Progress bars still appear in headless mode

**Solutions**:
1. Ensure `COMFYUI_HEADLESS=1` is set before importing ComfyUI
2. Call `setup_headless_environment()` early
3. Check environment variables are set

## Best Practices

### 1. Keep Standalone Scripts

Don't remove `main_headless.py`, `civitai_integration.py`, etc. They provide:
- CLI usage
- Backward compatibility
- Direct imports

### 2. Use Plugin for New Code

For new features, use the plugin:
- Better integration with ComfyUI
- Easier updates
- Standard plugin patterns

### 3. Test After ComfyUI Updates

Always test the plugin after updating ComfyUI:
- Plugin loading
- Node functionality
- Headless mode
- Modal deployment (if used)

### 4. Version Pinning (Optional)

If you need to pin to specific versions:

```python
# In extension.py
REQUIRED_COMFYUI_VERSION = "0.3.62"
MINIMUM_COMFYUI_VERSION = "0.3.0"

def check_comfyui_version():
    import comfyui_version
    version = getattr(comfyui_version, 'version', '0.0.0')
    # Check version compatibility
```

## Future Enhancements

Potential improvements:
1. **Configuration File**: Plugin-specific config file
2. **CLI Tools**: Command-line tools for plugin management
3. **More Nodes**: Additional serverless-related nodes
4. **Other Platforms**: Support for other serverless platforms (RunPod, etc.)
5. **Model Management**: Nodes for managing downloaded models

## Support

For issues or questions:
1. Check plugin logs
2. Review this guide
3. Check ComfyUI documentation
4. Open an issue with details

## Conclusion

The plugin approach provides:
- ✅ Easy migration path
- ✅ Backward compatibility
- ✅ Future-proof architecture
- ✅ Standard ComfyUI patterns
- ✅ Easy updates

By following this guide, you can maintain compatibility with future ComfyUI releases while leveraging the plugin's features.

