# ComfyUI on Modal.com - Deployment Guide

This guide explains how to deploy ComfyUI as a serverless application on Modal.com with GPU support.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Configuration](#configuration)
5. [Deployment](#deployment)
6. [Managing Models](#managing-models)
7. [Using the API](#using-the-api)
8. [Cost Optimization](#cost-optimization)
9. [Troubleshooting](#troubleshooting)

## Overview

Modal.com is a serverless platform that allows you to run Python code in the cloud with:

- **GPU Support**: Access to NVIDIA GPUs (T4, A10G, A100, etc.)
- **Auto-scaling**: Automatically scales based on demand
- **Persistent Storage**: Volumes that persist across deployments
- **Pay-per-use**: Only pay when your functions are running
- **Fast Cold Starts**: Optimized container loading

### Why Modal for ComfyUI?

- ✅ No server management required
- ✅ Automatic scaling from 0 to multiple GPUs
- ✅ Only pay for actual usage (per-second billing)
- ✅ Persistent model storage
- ✅ Easy deployment and updates
- ✅ Built-in monitoring and logging

## Prerequisites

1. **Modal Account**
   - Sign up at [modal.com](https://modal.com)
   - Get your API token from the dashboard

2. **Python Environment**
   - Python 3.8 or higher
   - pip package manager

3. **Basic Knowledge**
   - Familiarity with ComfyUI workflows
   - Basic command-line operations

## Initial Setup

### 1. Install Modal

```bash
pip install modal
```

### 2. Authenticate with Modal

```bash
modal setup
```

This will:
- Open your browser for authentication
- Link your local environment to your Modal account
- Store credentials securely

### 3. Verify Installation

```bash
modal --help
```

## Configuration

### GPU Selection

Edit `modal_app.py` to choose your GPU configuration:

```python
# Budget option - Good for testing (~$0.60/hour)
GPU_CONFIG = modal.gpu.T4()

# Balanced option - Recommended for most workloads (~$1.10/hour)
GPU_CONFIG = modal.gpu.A10G()

# High performance - For demanding workloads (~$4.00/hour)
GPU_CONFIG = modal.gpu.A100()

# Multi-GPU - For very large models (~$8.00/hour)
GPU_CONFIG = modal.gpu.A100(count=2)
```

**GPU Comparison:**

| GPU | VRAM | Performance | Cost/hour | Best For |
|-----|------|-------------|-----------|----------|
| T4 | 16GB | Basic | ~$0.60 | Testing, SD 1.5 |
| A10G | 24GB | Good | ~$1.10 | SDXL, Most workflows |
| A100 | 40GB/80GB | Excellent | ~$4.00 | Large models, Video |
| A100 (2x) | 80GB/160GB | Maximum | ~$8.00 | Multi-model, Batch |

### Container Idle Timeout

Adjust how long containers stay warm:

```python
# Keep containers warm for 5 minutes (reduces cold starts)
CONTAINER_IDLE_TIMEOUT = 300

# More aggressive cost savings (longer cold starts)
CONTAINER_IDLE_TIMEOUT = 60

# Keep very warm for high-traffic scenarios
CONTAINER_IDLE_TIMEOUT = 600
```

### Function Timeout

Set maximum execution time:

```python
# 10 minutes - Good for most image generation
TIMEOUT = 600

# 30 minutes - For video or complex workflows
TIMEOUT = 1800
```

## Deployment

### Step 1: Test Locally on Modal

Before deploying, test your setup:

```bash
modal run modal_app.py
```

This runs on Modal's infrastructure but doesn't create a persistent deployment.

### Step 2: Deploy to Modal

Create a persistent deployment:

```bash
modal deploy modal_app.py
```

Output will show:
```
✓ Created objects.
├── 🔨 Created function fastapi_app.
├── 🔨 Created function download_models.
└── 🔨 Created function generate_image.
✓ App deployed! 🎉

View your app at https://modal.com/apps/<workspace>/comfyui

Web endpoint available at:
https://<workspace>--comfyui-fastapi-app.modal.run
```

### Step 3: Verify Deployment

```bash
# List all deployments
modal app list

# View deployment details
modal app show comfyui
```

## Managing Models

### Understanding Volumes

Modal uses persistent volumes for storage:
- `comfyui-models`: Stores all your AI models
- `comfyui-outputs`: Stores generated images/videos

Volumes persist across deployments and are shared across all function calls.

### Downloading Models

#### Option 1: Using the Helper Function

Run the built-in download function:

```bash
modal run modal_app.py::download_models
```

Edit `download_models()` in `modal_app.py` to add your model URLs:

```python
# Example: Download SDXL model
model_url = "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"
model_path = "/models/checkpoints/sd_xl_base_1.0.safetensors"

if not os.path.exists(model_path):
    urllib.request.urlretrieve(model_url, model_path)
```

#### Option 2: Upload from Local Machine

```bash
# Upload a single model
modal volume put comfyui-models local_model.safetensors /checkpoints/model.safetensors

# Upload an entire directory
modal volume put comfyui-models ./my_models /checkpoints
```

### Managing Volume Contents

```bash
# List volumes
modal volume list

# List contents of a volume
modal volume ls comfyui-models
modal volume ls comfyui-models /checkpoints

# Download files from volume
modal volume get comfyui-models /checkpoints/model.safetensors ./local_model.safetensors

# Delete files (be careful!)
# modal volume rm comfyui-models /checkpoints/old_model.safetensors
```

### Recommended Model Organization

```
/models/
├── checkpoints/          # Main model checkpoints (.safetensors, .ckpt)
├── vae/                  # VAE models
├── loras/               # LoRA models
├── controlnet/          # ControlNet models
├── clip/                # CLIP models
├── clip_vision/         # CLIP Vision models
├── embeddings/          # Textual Inversion embeddings
└── upscale_models/      # Upscaler models (ESRGAN, etc.)
```

## Using the API

### Web Endpoint

After deployment, you get a public HTTPS endpoint:

```
https://<workspace>--comfyui-fastapi-app.modal.run
```

### API Endpoints

All standard ComfyUI API endpoints are available:

```bash
# Get system info
curl https://<endpoint>/system_stats

# Get available nodes
curl https://<endpoint>/object_info

# Queue a prompt (workflow)
curl -X POST https://<endpoint>/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": {...}}'

# Get queue status
curl https://<endpoint>/queue

# Get history
curl https://<endpoint>/history

# Get specific result
curl https://<endpoint>/history/<prompt_id>

# Download generated image
curl https://<endpoint>/view?filename=<filename>
```

### Python Client Example

```python
import requests
import json

# Your Modal endpoint
ENDPOINT = "https://<workspace>--comfyui-fastapi-app.modal.run"

# Load a workflow
with open("workflow.json", "r") as f:
    workflow = json.load(f)

# Queue the workflow
response = requests.post(
    f"{ENDPOINT}/prompt",
    json={"prompt": workflow}
)

result = response.json()
prompt_id = result["prompt_id"]

print(f"Queued workflow with ID: {prompt_id}")

# Check status
status = requests.get(f"{ENDPOINT}/history/{prompt_id}")
print(status.json())
```

### Using Modal Functions Directly

```python
import modal

# Look up the deployed function
f = modal.Function.lookup("comfyui", "generate_image")

# Call it directly
result = f.remote(workflow=my_workflow_dict)

print(result)
```

## Cost Optimization

### 1. Choose the Right GPU

- **Development/Testing**: Use T4 GPUs
- **Production (SD 1.5)**: Use T4 or A10G
- **Production (SDXL)**: Use A10G
- **Large Models/Video**: Use A100

### 2. Optimize Container Idle Time

```python
# High traffic (keep warm)
CONTAINER_IDLE_TIMEOUT = 600  # 10 minutes

# Medium traffic (balanced)
CONTAINER_IDLE_TIMEOUT = 300  # 5 minutes

# Low traffic (cost optimized)
CONTAINER_IDLE_TIMEOUT = 60   # 1 minute
```

### 3. Use Batch Processing

Queue multiple prompts together to maximize GPU utilization:

```python
# Instead of 10 separate calls
for prompt in prompts:
    generate_image(prompt)  # Cold start each time

# Batch them
batch_generate_images(prompts)  # One warm container
```

### 4. Monitor Usage

```bash
# View usage dashboard
modal app stats comfyui

# Monitor costs in Modal dashboard
# https://modal.com/usage
```

### Estimated Costs

**Example: Image Generation with SDXL on A10G**
- Container startup: 30 seconds
- Generation: 15 seconds per image
- Total per image: 45 seconds
- Cost: ~$0.014 per image (at $1.10/hour)

**With container warming:**
- First image: 45 seconds (~$0.014)
- Subsequent images (within 5 min): 15 seconds (~$0.005)

## Troubleshooting

### Deployment Issues

**Error: "Module not found"**
```bash
# Ensure all files are included in the mount
# Check modal_app.py mount configuration
mounts=[modal.Mount.from_local_dir(".", remote_path="/app")]
```

**Error: "GPU out of memory"**
```bash
# Use a larger GPU or reduce batch size
GPU_CONFIG = modal.gpu.A100()  # More VRAM
```

### Model Loading Issues

**Models not found:**
```bash
# Check volume contents
modal volume ls comfyui-models

# Verify model paths
modal volume ls comfyui-models /checkpoints
```

**Models not persisting:**
```bash
# Ensure volume.commit() is called after downloads
models_volume.commit()
```

### Performance Issues

**Slow cold starts:**
```python
# Increase container idle timeout
CONTAINER_IDLE_TIMEOUT = 600

# Pre-warm with a health check endpoint
```

**Timeouts:**
```python
# Increase function timeout
TIMEOUT = 1800  # 30 minutes
```

### Debugging

**View logs:**
```bash
# Real-time logs
modal app logs comfyui

# Follow logs
modal app logs comfyui --follow
```

**Interactive debugging:**
```bash
# Start an interactive shell in the container
modal shell modal_app.py
```

**Check GPU availability:**
```python
@app.function(gpu=GPU_CONFIG)
def check_gpu():
    import torch
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    
# Run it
modal run modal_app.py::check_gpu
```

## Advanced Topics

### Custom Image with Models Pre-loaded

For fastest cold starts, build a custom image with models included:

```python
def download_models_to_image():
    import urllib.request
    urllib.request.urlretrieve(
        "https://huggingface.co/.../model.safetensors",
        "/models/checkpoints/model.safetensors"
    )

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(...)
    .pip_install(...)
    .run_function(download_models_to_image)  # Bake models into image
)
```

### Multiple Environments

Deploy different configurations:

```python
# Fast/cheap endpoint
@app.function(gpu=modal.gpu.T4())
@modal.asgi_app()
def fast_app():
    ...

# High-quality endpoint  
@app.function(gpu=modal.gpu.A100())
@modal.asgi_app()
def quality_app():
    ...
```

### Scheduled Tasks

Run workflows on a schedule:

```python
@app.function(
    schedule=modal.Period(hours=1),  # Run every hour
    gpu=GPU_CONFIG,
)
def scheduled_generation():
    # Generate images on schedule
    pass
```

## Support and Resources

- **Modal Documentation**: https://modal.com/docs
- **Modal Discord**: https://discord.gg/modal
- **ComfyUI Documentation**: https://github.com/comfyanonymous/ComfyUI
- **Modal Examples**: https://github.com/modal-labs/modal-examples

## Next Steps

1. ✅ Deploy ComfyUI to Modal
2. ✅ Upload your models
3. ✅ Test the API endpoint
4. ✅ Integrate with your application
5. ✅ Monitor usage and costs
6. ✅ Optimize for your use case

Happy generating! 🎨

