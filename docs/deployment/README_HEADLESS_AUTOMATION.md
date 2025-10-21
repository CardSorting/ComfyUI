# ComfyUI Headless Automation

## Overview

This document describes the automated startup system for ComfyUI headless mode, including the fixes applied and the automation scripts created.

## 🛠️ Fixes Applied

### 1. CUDA Allocator Configuration Issue

**Problem**: 
```
RuntimeError: config[i] == get()->name() INTERNAL ASSERT FAILED at "/pytorch/c10/cuda/CUDAAllocatorConfig.cpp":287
```

**Root Cause**: PyTorch CUDA allocator configuration conflict between runtime and load time.

**Solution**: Added `--disable-cuda-malloc` flag to bypass the allocator configuration issue.

### 2. Mutually Exclusive GPU Memory Flags

**Problem**: 
```
main.py: error: argument --gpu-only: not allowed with argument --highvram
```

**Root Cause**: ComfyUI CLI parser has mutually exclusive groups for GPU memory management flags.

**Solution**: Implemented intelligent GPU flag selection based on available VRAM:
- `--gpu-only` for GPUs with ≥20GB VRAM (RTX 4090, A100)
- `--highvram` for GPUs with 16-20GB VRAM (RTX 4080)
- `--normalvram` for GPUs with 8-16GB VRAM (RTX 4070, RTX 3080)
- `--lowvram` for GPUs with <8GB VRAM (RTX 4060, RTX 3070)

### 3. CPU Mode Override

**Problem**: ComfyUI was defaulting to CPU mode despite CUDA being available.

**Root Cause**: Missing explicit CUDA device specification and GPU-only mode.

**Solution**: Added explicit `--cuda-device 0` and appropriate GPU memory flags.

## 🤖 Automation Scripts

### 1. Main Startup Script (`start_comfyui_headless.sh`)

**Features**:
- Automatic GPU detection and optimal flag selection
- System requirements validation
- Port availability checking
- Process management with PID files
- Comprehensive logging
- API health checking
- Graceful startup/shutdown

**Usage**:
```bash
./start_comfyui_headless.sh [start|stop|restart|status|logs|help]
```

**Key Functions**:
- `check_requirements()`: Validates CUDA, GPU, Python, PyTorch
- `get_gpu_flags()`: Automatically selects optimal GPU memory flags
- `start_comfyui()`: Starts ComfyUI with optimal configuration
- `check_running()`: Monitors process status
- `show_status()`: Displays system and API status

### 2. System Service Installation (`install_service.sh`)

**Features**:
- Systemd service installation
- Automatic startup on boot
- Service management (start/stop/restart)
- Log integration with journald
- Security hardening
- Resource limits

**Usage**:
```bash
sudo ./install_service.sh [install|uninstall|start|stop|restart|status|logs|help]
```

**Service Configuration**:
- **Type**: Forking with PID file management
- **User**: Runs as non-root user
- **Restart**: Automatic restart on failure
- **Security**: NoNewPrivileges, PrivateTmp, ProtectSystem
- **Resources**: Optimized file descriptor and process limits

### 3. Systemd Service File (`systemd/comfyui-headless.service`)

**Configuration**:
```ini
[Unit]
Description=ComfyUI Headless Service
After=network.target
Wants=network.target

[Service]
Type=forking
User=user
Group=user
WorkingDirectory=/home/user/Documents/ComfyUI
ExecStart=/home/user/Documents/ComfyUI/start_comfyui_headless.sh start
ExecStop=/home/user/Documents/ComfyUI/start_comfyui_headless.sh stop
ExecReload=/home/user/Documents/ComfyUI/start_comfyui_headless.sh restart
PIDFile=/home/user/Documents/ComfyUI/comfyui_headless.pid
Restart=always
RestartSec=10
```

## 🔧 Configuration Management

### Environment Variables

The automation system sets optimal environment variables:

```bash
CUDA_VISIBLE_DEVICES=0
TQDM_DISABLE=1
PYTHONUNBUFFERED=1
DISABLE_PROGRESS_BARS=true
DISABLE_AUTO_LAUNCH=true
DONT_PRINT_SERVER=true
```

### GPU Memory Optimization

Automatic GPU flag selection based on VRAM:

```bash
# RTX 4090 (25GB) - Maximum Performance
--gpu-only

# RTX 4080 (16GB) - High Performance
--highvram

# RTX 4070 (12GB) - Balanced Performance
--normalvram

# RTX 4060 (8GB) - Memory Efficient
--lowvram
```

## 📊 Monitoring and Logging

### Log Management

1. **Manual Startup**: Logs to `comfyui_headless.log`
2. **System Service**: Logs to systemd journal
3. **Real-time Monitoring**: `tail -f` for manual, `journalctl -f` for service

### Health Monitoring

- **Process Monitoring**: PID file tracking
- **API Health Checks**: Automatic endpoint testing
- **GPU Status**: VRAM usage monitoring
- **Performance Metrics**: Generation time tracking

## 🚀 Performance Results

### Test Results (RTX 4090)

- **Startup Time**: ~15 seconds
- **Generation Time**: 8.02 seconds (512x512, 20 steps)
- **VRAM Usage**: ~6GB during generation
- **Available VRAM**: ~19GB free
- **API Response**: <100ms average

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

## 🔄 Integration Points

### DreamBeesArt Backend

The automation system integrates seamlessly with the DreamBeesArt backend:

1. **Automatic Connection**: Backend connects to `http://localhost:8188`
2. **Health Monitoring**: Backend monitors ComfyUI status
3. **Queue Management**: Real-time task processing
4. **Error Handling**: Graceful fallback and retry mechanisms

### API Endpoints

All standard ComfyUI API endpoints are available:

- `GET /api/system_stats` - System and GPU information
- `GET /api/object_info` - Available nodes (693 nodes)
- `POST /api/prompt` - Submit generation tasks
- `GET /api/queue` - Queue status
- `POST /api/interrupt` - Interrupt generation
- `POST /api/free` - Free memory

## 🛡️ Security and Reliability

### Security Features

- **Non-root Execution**: Service runs as regular user
- **Process Isolation**: PrivateTmp, ProtectSystem
- **Resource Limits**: File descriptor and process limits
- **Network Security**: CORS configuration

### Reliability Features

- **Automatic Restart**: Service restarts on failure
- **Health Monitoring**: Continuous API health checks
- **Graceful Shutdown**: Proper cleanup on stop
- **Error Recovery**: Comprehensive error handling

## 📝 Usage Examples

### Development Workflow

```bash
# Start ComfyUI for development
./start_comfyui_headless.sh start

# Check status
./start_comfyui_headless.sh status

# View logs in real-time
./start_comfyui_headless.sh logs

# Stop when done
./start_comfyui_headless.sh stop
```

### Production Deployment

```bash
# Install as system service
sudo ./install_service.sh install

# Start service
sudo systemctl start comfyui-headless

# Enable auto-start on boot
sudo systemctl enable comfyui-headless

# Monitor service
sudo systemctl status comfyui-headless
```

### Troubleshooting

```bash
# Check service logs
sudo journalctl -u comfyui-headless -f

# Restart service
sudo systemctl restart comfyui-headless

# Check GPU status
nvidia-smi

# Test API
curl http://localhost:8188/api/system_stats
```

## 🎯 Success Criteria

The automation system is considered successful when:

1. ✅ ComfyUI starts automatically with CUDA acceleration
2. ✅ API endpoints respond within 100ms
3. ✅ Generation completes in <10 seconds (512x512, 20 steps)
4. ✅ VRAM usage is optimized for the GPU
5. ✅ Service restarts automatically on failure
6. ✅ Logs provide clear diagnostic information
7. ✅ Integration with DreamBeesArt backend works seamlessly

## 🔮 Future Enhancements

Potential improvements for the automation system:

1. **Multi-GPU Support**: Automatic GPU selection and load balancing
2. **Dynamic Scaling**: Automatic resource adjustment based on load
3. **Health Dashboards**: Web-based monitoring interface
4. **Backup and Recovery**: Automatic model and configuration backup
5. **Performance Tuning**: Automatic optimization based on workload
6. **Container Support**: Docker and Kubernetes integration

This automation system provides a robust, production-ready solution for running ComfyUI in headless mode with optimal performance and reliability.
