# Modal Deployment Optimization

## Problem
The initial deployment was timing out during the build process. This was caused by:

1. **Large file uploads**: The entire ComfyUI directory (113MB+) was being uploaded, including:
   - `models/` directory (should use volumes)
   - `output/` directory (should use volumes)
   - `__pycache__/` directories
   - Test files and documentation
   - Large binary files in custom nodes

2. **Slow PyTorch installation**: Installing PyTorch with CUDA support takes 5-10 minutes

3. **No file exclusions**: All files were being processed during the build

## Solution

### File Exclusions
Added an `ignore` parameter to `add_local_dir()` to exclude:

- **Model directories**: `models/`, `output/`, `input/` (use volumes instead)
- **Cache files**: `__pycache__/`, `*.pyc`, `.pytest_cache/`, etc.
- **Version control**: `.git/`, `.github/`
- **Test files**: `tests/`, `tests-unit/`
- **Documentation**: `docs/`, `*.md` (except README and modal docs)
- **Development files**: `.vscode/`, `.idea/`, `venv/`, etc.
- **Large binaries**: Model files in `custom_nodes/`
- **Generated files**: `*.png`, `*.jpg`, logs, etc.

### Expected Improvements

- **Reduced upload size**: From ~113MB to ~20-30MB (excluding models, outputs, tests, docs)
- **Faster build**: Less files to process and upload
- **Cleaner image**: Only essential runtime files included

## Deployment

The optimized deployment should now complete successfully:

```bash
modal deploy modal/apps/modal_app_fastapi.py
```

## Monitoring Build Progress

If deployment still times out, you can:

1. **Check Modal dashboard**: View build logs at https://modal.com/apps
2. **Use verbose mode**: The build process will show progress
3. **Check network**: Ensure stable internet connection for uploads

## Additional Optimizations (Future)

If needed, further optimizations could include:

1. **Pre-built PyTorch image**: Use a base image with PyTorch pre-installed
2. **Layer caching**: Structure dependencies to maximize Docker layer caching
3. **Incremental builds**: Only rebuild changed layers
4. **Split dependencies**: Install core dependencies first, optional ones later

## Notes

- Models should be uploaded to volumes, not included in the image
- Outputs are stored in volumes, not in the image
- The image only contains the ComfyUI code and dependencies needed to run

