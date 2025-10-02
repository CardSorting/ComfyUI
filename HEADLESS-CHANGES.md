# ComfyUI Headless Mode Implementation

This document summarizes the changes made to enable headless operation of ComfyUI for serverless compatibility.

## Files Modified

### 1. `comfy/cli_args.py`
- **Added**: `--headless` command line argument
- **Purpose**: Enables headless mode without web UI

### 2. `server.py`
- **Modified**: `PromptServer.__init__()` - Conditionally initialize frontend
- **Modified**: `get_root()` route - Returns JSON API info in headless mode
- **Modified**: `add_routes()` - Skips UI-related routes in headless mode
- **Modified**: `start_multi_address()` - Updated startup messages for headless mode

### 3. `main.py`
- **Modified**: `start_comfyui()` - Disables auto-launch in headless mode

## Files Created

### 1. `requirements-headless.txt`
- **Purpose**: Minimal dependencies for headless operation
- **Excludes**: Frontend packages (comfyui-frontend-package, comfyui-workflow-templates, comfyui-embedded-docs)

### 2. `main_headless.py`
- **Purpose**: Convenient startup script for headless mode
- **Features**: Sets environment variables and provides helpful output

### 3. `Dockerfile.headless`
- **Purpose**: Docker image optimized for headless deployment
- **Features**: Uses headless requirements, minimal system dependencies

### 4. `README-HEADLESS.md`
- **Purpose**: Comprehensive documentation for headless mode
- **Includes**: Usage examples, API documentation, deployment guides

### 5. `example_headless_usage.py`
- **Purpose**: Example client code for using ComfyUI API
- **Features**: Python client class with common API operations

## Key Features

### Headless Mode Behavior
- **No Web UI**: Frontend initialization is skipped
- **API Only**: Only REST API endpoints are available
- **Reduced Dependencies**: Frontend packages are not required
- **Serverless Ready**: Optimized for containerized deployments

### API Endpoints Available
- `GET /` - API information and available endpoints
- `POST /prompt` - Submit workflows for execution
- `GET /queue` - Queue status
- `GET /history` - Execution history
- `GET /object_info` - Available nodes
- `GET /system_stats` - System information
- `POST /interrupt` - Interrupt execution
- `POST /free` - Free memory

### Command Line Usage
```bash
# Basic headless mode
python main.py --headless

# Headless with custom settings
python main.py --headless --listen 0.0.0.0 --port 8080

# Minimal headless mode
python main.py --headless --disable-all-custom-nodes --cpu
```

### Docker Usage
```bash
# Build headless image
docker build -f Dockerfile.headless -t comfyui-headless .

# Run container
docker run -p 8188:8188 comfyui-headless
```

## Compatibility

- **Backward Compatible**: All existing functionality preserved
- **API Compatible**: Same API endpoints as standard ComfyUI
- **Workflow Compatible**: All ComfyUI workflows work unchanged

## Benefits for Serverless

1. **Reduced Image Size**: No frontend dependencies
2. **Faster Startup**: No frontend initialization
3. **Lower Memory**: No web UI components loaded
4. **API Focused**: Optimized for programmatic access
5. **Container Ready**: Dockerfile for easy deployment

## Testing

The implementation has been tested to ensure:
- ✅ Headless argument parsing works correctly
- ✅ Server logic properly handles headless mode
- ✅ Route logic returns appropriate responses
- ✅ No frontend dependencies are loaded in headless mode
- ✅ All API endpoints remain functional

## Deployment Examples

### AWS Lambda
```bash
python main.py --headless --listen 0.0.0.0 --port 8080
```

### Google Cloud Run
```bash
docker build -f Dockerfile.headless -t gcr.io/PROJECT_ID/comfyui-headless .
```

### Azure Container Instances
```bash
az container create --image comfyui-headless --ports 8188
```

This implementation provides a complete headless solution for ComfyUI while maintaining full API compatibility and reducing resource requirements for serverless deployments.
