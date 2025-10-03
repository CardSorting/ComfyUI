# ComfyUI Headless Quick Start Guide

## 🚀 Quick Start

### Option 1: Manual Startup (Recommended for Development)

```bash
# Navigate to ComfyUI directory
cd /home/user/Documents/ComfyUI

# Start ComfyUI headless with optimal settings
./start_comfyui_headless.sh start

# Check status
./start_comfyui_headless.sh status

# View logs
./start_comfyui_headless.sh logs

# Stop when done
./start_comfyui_headless.sh stop
```

### Option 2: System Service (Recommended for Production)

```bash
# Install as system service (requires sudo)
sudo ./install_service.sh install

# Start the service
sudo systemctl start comfyui-headless

# Enable auto-start on boot
sudo systemctl enable comfyui-headless

# Check status
sudo systemctl status comfyui-headless

# View logs
sudo journalctl -u comfyui-headless -f
```

## 📋 Prerequisites

- NVIDIA GPU with CUDA support
- Python 3.10+
- PyTorch with CUDA
- ComfyUI installed

## 🔧 Configuration

The startup script automatically detects your GPU and applies optimal settings:

- **RTX 4090 (25GB)**: Uses `--gpu-only` for maximum performance
- **RTX 4080 (16GB)**: Uses `--highvram` for balanced performance
- **RTX 4070 (12GB)**: Uses `--normalvram` for standard performance
- **RTX 4060 (8GB)**: Uses `--lowvram` for memory efficiency

## 🌐 API Access

Once started, ComfyUI API is available at:
- **Local**: `http://localhost:8188/api/`
- **Network**: `http://0.0.0.0:8188/api/`

### Test API Connection

```bash
# Check system status
curl http://localhost:8188/api/system_stats

# List available nodes
curl http://localhost:8188/api/object_info

# Check queue status
curl http://localhost:8188/api/queue
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 8188
   lsof -i :8188
   
   # Kill existing process
   sudo kill -9 <PID>
   ```

2. **CUDA Not Available**
   ```bash
   # Check CUDA installation
   nvidia-smi
   
   # Check PyTorch CUDA support
   python3 -c "import torch; print(torch.cuda.is_available())"
   ```

3. **Permission Issues**
   ```bash
   # Make scripts executable
   chmod +x start_comfyui_headless.sh
   chmod +x install_service.sh
   ```

### Log Files

- **Manual startup**: `/home/user/Documents/ComfyUI/comfyui_headless.log`
- **System service**: `journalctl -u comfyui-headless`

## 📊 Performance Monitoring

### GPU Usage
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Check VRAM usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

### API Health Check
```bash
# Quick health check
curl -s http://localhost:8188/api/system_stats | jq '.devices[0].vram_free'
```

## 🔄 Integration with DreamBeesArt

The ComfyUI headless service integrates seamlessly with the DreamBeesArt backend:

1. **Backend Configuration**: Set `COMFYUI_URL=http://localhost:8188`
2. **Automatic Connection**: Backend automatically connects to ComfyUI
3. **Queue Management**: Real-time task processing
4. **Image Generation**: Fast CUDA-accelerated generation

## 📝 Script Commands

### Manual Startup Script
```bash
./start_comfyui_headless.sh [command]

Commands:
  start    Start ComfyUI in headless mode (default)
  stop     Stop ComfyUI
  restart  Restart ComfyUI
  status   Show ComfyUI status
  logs     Show and follow logs
  help     Show help message
```

### Service Management Script
```bash
sudo ./install_service.sh [command]

Commands:
  install    Install as systemd service (default)
  uninstall  Remove systemd service
  start      Start the service
  stop       Stop the service
  restart    Restart the service
  status     Show service status
  logs       Show and follow service logs
  help       Show help message
```

## 🎯 Success Indicators

When ComfyUI starts successfully, you should see:

```
[SUCCESS] ComfyUI is running and API is accessible
[INFO] API available at: http://0.0.0.0:8188/api/
[INFO] Device: cuda:0 NVIDIA GeForce RTX 4090 : native
[INFO] Using xformers attention
```

## 🆘 Getting Help

1. **Check logs** for detailed error messages
2. **Verify GPU** with `nvidia-smi`
3. **Test API** with curl commands
4. **Review configuration** in the setup guide

For detailed troubleshooting, see `COMFYUI_HEADLESS_SETUP_GUIDE.md`.
