# ComfyUI Headless Setup Guide

## Overview

This guide documents the successful setup and configuration of ComfyUI running in headless mode with CUDA acceleration on an NVIDIA GeForce RTX 4090 GPU.

## System Requirements

- **GPU**: NVIDIA GeForce RTX 4090 (25GB VRAM)
- **CUDA**: Version 12.8
- **PyTorch**: Version 2.8.0+cu128
- **Python**: 3.10.12
- **OS**: Linux (Ubuntu/Debian)

## Key Issues Identified and Fixed

### 1. CUDA Allocator Configuration Issue

**Problem**: 
```
RuntimeError: config[i] == get()->name() INTERNAL ASSERT FAILED at "/pytorch/c10/cuda/CUDAAllocatorConfig.cpp":287
```

**Solution**: 
Use the `--disable-cuda-malloc` flag to bypass the CUDA allocator configuration conflict.

### 2. Mutually Exclusive GPU Memory Flags

**Problem**: 
```
main.py: error: argument --gpu-only: not allowed with argument --highvram
```

**Solution**: 
Use only one GPU memory management flag at a time. For RTX 4090 with 25GB VRAM, `--gpu-only` is optimal.

### 3. CPU Mode Override

**Problem**: 
ComfyUI was defaulting to CPU mode despite CUDA being available.

**Solution**: 
Explicitly specify CUDA device and GPU-only mode with proper flags.

## Optimal Configuration

### Command Line Arguments

```bash
python3 main.py \
  --headless \
  --listen 0.0.0.0 \
  --port 8188 \
  --cuda-device 0 \
  --gpu-only \
  --disable-cuda-malloc \
  --verbose INFO
```

### Flag Explanations

- `--headless`: Disables web UI, runs API-only mode
- `--listen 0.0.0.0`: Allows external connections
- `--port 8188`: Standard ComfyUI API port
- `--cuda-device 0`: Uses first CUDA device (RTX 4090)
- `--gpu-only`: Keeps all models in GPU memory (optimal for 25GB VRAM)
- `--disable-cuda-malloc`: Fixes CUDA allocator configuration issues
- `--verbose INFO`: Enables detailed logging

## Performance Metrics

### Successful Test Results

- **Generation Time**: 8.02 seconds for 512x512 image (20 steps)
- **Model Loading**: ~6 seconds for PonyDiffusion V6 XL
- **VRAM Usage**: ~6GB during generation
- **Available VRAM**: ~19GB free out of 25GB total
- **API Response**: All endpoints functional

### System Status

```json
{
  "system": {
    "comfyui_version": "0.3.62",
    "pytorch_version": "2.8.0+cu128",
    "python_version": "3.10.12"
  },
  "devices": [
    {
      "name": "cuda:0 NVIDIA GeForce RTX 4090 : native",
      "type": "cuda",
      "index": 0,
      "vram_total": 25262096384,
      "vram_free": 19908460544
    }
  ]
}
```

## Environment Configuration

### .env File Settings

```bash
# ComfyUI Environment Configuration
COMFYUI_PORT=8188
COMFYUI_HOST=0.0.0.0

# Headless Mode Configuration
DISABLE_PROGRESS_BARS=true
DISABLE_AUTO_LAUNCH=true
DONT_PRINT_SERVER=true
TQDM_DISABLE=1
TQDM_DISABLE_PROGRESS_BAR=1
PYTHONUNBUFFERED=1

# GPU Configuration
CUDA_VISIBLE_DEVICES=0

# Performance Configuration
TQDM_MINITERS=0
TQDM_MAXITERS=0
TQDM_POSITION=0
TQDM_LEAVE=false
TQDM_NCOLS=0
TQDM_DESC=
TQDM_UNIT=
TQDM_UNIT_SCALE=false
TQDM_RATE=0
TQDM_POSTFIX=
TQDM_BAR_FORMAT=
TQDM_SMOOTHING=0
TQDM_DYNAMIC_NCOLS=false
TQDM_ASCII=true
TQDM_DISABLE_TQDM=true

# Logging Configuration
LOG_LEVEL=INFO
DEBUG=false

# Security Configuration
ENABLE_CORS=true
TRUSTED_ORIGINS=*
```

## API Endpoints

### System Information
- `GET /api/system_stats` - System and GPU information
- `GET /api/object_info` - Available nodes (693 nodes loaded)
- `GET /api/queue` - Queue status

### Generation
- `POST /api/prompt` - Submit generation tasks
- `GET /api/history/{prompt_id}` - Get generation results
- `POST /api/interrupt` - Interrupt current generation
- `POST /api/free` - Free memory

## Troubleshooting

### Common Issues

1. **CUDA Not Available**
   - Verify CUDA installation: `nvidia-smi`
   - Check PyTorch CUDA support: `python3 -c "import torch; print(torch.cuda.is_available())"`

2. **Memory Issues**
   - Use `--lowvram` for GPUs with <8GB VRAM
   - Use `--normalvram` for GPUs with 8-16GB VRAM
   - Use `--gpu-only` for GPUs with >16GB VRAM

3. **Port Conflicts**
   - Change port with `--port 8189` if 8188 is in use
   - Check for existing processes: `lsof -i :8188`

4. **Permission Issues**
   - Ensure proper file permissions on ComfyUI directory
   - Run with appropriate user permissions

### Log Analysis

Key log indicators of successful startup:
```
INFO:root:Device: cuda:0 NVIDIA GeForce RTX 4090 : native
INFO:root:Using xformers attention
INFO:root:ComfyUI is running in headless mode at: http://0.0.0.0:8188
INFO:root:API endpoints are available at: http://0.0.0.0:8188/api/
```

## Integration with DreamBeesArt

### Backend Configuration
- **URL**: `http://localhost:8188`
- **Status**: Connected and healthy
- **Models**: PonyDiffusion V6 XL loaded
- **Queue**: Real-time task management

### Generation Workflow
1. Submit generation request to backend
2. Backend forwards to ComfyUI API
3. ComfyUI processes with CUDA acceleration
4. Results returned via API
5. Images saved to frontend directory

## Best Practices

1. **Memory Management**: Use `--gpu-only` for high-VRAM GPUs
2. **Monitoring**: Check VRAM usage with `nvidia-smi`
3. **Logging**: Enable verbose logging for debugging
4. **Security**: Use proper CORS settings for remote access
5. **Performance**: Monitor generation times and optimize accordingly

## Conclusion

This configuration provides optimal performance for ComfyUI headless mode with CUDA acceleration on the RTX 4090, achieving fast generation times and efficient memory usage.
