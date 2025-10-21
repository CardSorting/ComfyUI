# ComfyUI Headless Mode

This fork of ComfyUI has been modified to support headless operation, making it ideal for serverless deployments and API-only usage.

## Features

- **No Web UI**: Disables the frontend interface and related dependencies
- **API Only**: Provides REST API endpoints for programmatic access
- **Reduced Dependencies**: Excludes frontend packages to minimize image size
- **Serverless Ready**: Optimized for containerized and serverless environments

## Quick Start

### Using the Headless Script

```bash
python main_headless.py --headless --listen 0.0.0.0 --port 8188
```

### Using Docker

```bash
# Build headless image
docker build -f Dockerfile.headless -t comfyui-headless .

# Run container
docker run -p 8188:8188 comfyui-headless
```

### Using Standard Installation

```bash
# Install headless dependencies only
pip install -r requirements-headless.txt

# Run in headless mode
python main.py --headless --listen 0.0.0.0 --port 8188
```

## API Endpoints

When running in headless mode, the following API endpoints are available:

- `GET /` - Returns API information and available endpoints
- `POST /prompt` - Submit a workflow for execution
- `GET /queue` - Get current queue status
- `GET /history` - Get execution history
- `GET /object_info` - Get available node information
- `GET /system_stats` - Get system information
- `POST /interrupt` - Interrupt current execution
- `POST /free` - Free memory and unload models

All endpoints are also available with `/api/` prefix for easier routing.

## Configuration

### Command Line Arguments

- `--headless`: Enable headless mode (disables web UI)
- `--listen`: IP address to listen on (default: 127.0.0.1)
- `--port`: Port to listen on (default: 8188)
- `--disable-all-custom-nodes`: Disable custom nodes for minimal footprint
- `--disable-api-nodes`: Disable API nodes if not needed

### Environment Variables

- `COMFYUI_HEADLESS=1`: Automatically enables headless mode

## Serverless Deployment

### AWS Lambda

For AWS Lambda deployment, use the headless mode with appropriate memory and timeout settings:

```bash
python main.py --headless --listen 0.0.0.0 --port 8080
```

### Google Cloud Run

```bash
docker build -f Dockerfile.headless -t gcr.io/PROJECT_ID/comfyui-headless .
docker push gcr.io/PROJECT_ID/comfyui-headless
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name comfyui-headless \
  --image comfyui-headless \
  --ports 8188 \
  --memory 4 \
  --cpu 2
```

## Performance Optimizations

For serverless environments, consider these optimizations:

1. **Disable Custom Nodes**: Use `--disable-all-custom-nodes` to reduce startup time
2. **Memory Management**: Use `--lowvram` or `--cpu` for memory-constrained environments
3. **Caching**: Use `--cache-none` to minimize memory usage
4. **Model Loading**: Pre-load models or use model caching strategies

## Differences from Standard ComfyUI

- No web frontend or static file serving
- No WebSocket connections for real-time updates
- No browser auto-launch
- Reduced dependency footprint
- API-only interface

## Troubleshooting

### Frontend Dependencies Error

If you see errors about missing frontend packages, ensure you're using `requirements-headless.txt`:

```bash
pip install -r requirements-headless.txt
```

### Memory Issues

For memory-constrained environments:

```bash
python main.py --headless --cpu --cache-none --disable-all-custom-nodes
```

### Port Binding

Ensure the port is accessible in your deployment environment:

```bash
python main.py --headless --listen 0.0.0.0 --port 8080
```

## Contributing

This headless mode maintains compatibility with the original ComfyUI API while removing UI dependencies. All core functionality remains available through the REST API.
