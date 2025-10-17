# ComfyUI Modal Deployment

This directory contains all files related to deploying and managing ComfyUI on Modal.com.

## 📁 Directory Structure

```
modal/
├── apps/                       # Modal applications
│   └── modal_app_fastapi.py   # Main FastAPI ComfyUI app
├── scripts/                    # Helper scripts
│   ├── modal_model_manager.sh # Model management CLI
│   ├── modal_download_model.py # Python model downloader
│   └── modal_setup_wizard.py  # Setup wizard
├── tests/                      # Test files
│   ├── modal_test_endpoints.py # Endpoint testing suite
│   ├── modal_test_webserver.py # Web server test
│   └── modal_test.py           # Basic tests
├── docs/                       # Documentation
│   ├── MODAL_MODEL_SETUP.md    # Model download guide
│   ├── POPULAR_MODELS.md       # Popular model URLs
│   └── MODAL_*.md              # Other guides
└── modal_requirements.txt      # Modal-specific requirements
```

## 🚀 Quick Start

### Deploy the App
```bash
modal deploy modal/apps/modal_app_fastapi.py
```

### Manage Models
```bash
# List models
modal/scripts/modal_model_manager.sh list

# Download a model
modal/scripts/modal_model_manager.sh download-url "URL" "CATEGORY"

# Delete a model
modal/scripts/modal_model_manager.sh delete "CATEGORY" "FILENAME"
```

### Test the Deployment
```bash
python modal/tests/modal_test_endpoints.py YOUR_ENDPOINT_URL
```

## 📚 Documentation

- **[Model Setup Guide](docs/MODAL_MODEL_SETUP.md)** - Complete guide for downloading models
- **[Popular Models](docs/POPULAR_MODELS.md)** - Ready-to-use model download commands
- **[Deployment Guide](docs/MODAL_DEPLOYMENT_GUIDE.md)** - Full deployment instructions
- **[Quick Start](docs/MODAL_QUICKSTART.md)** - Get started quickly

## 🔗 Your Endpoint

After deployment, your endpoint will be:
```
https://YOUR_WORKSPACE--comfyui-api-web.modal.run
```

## 💡 Common Commands

```bash
# Deploy the app
modal deploy modal/apps/modal_app_fastapi.py

# Check app status
modal app list

# View logs
modal app logs comfyui-api

# Stop the app
modal app stop comfyui-api

# Download SDXL Turbo
modal/scripts/modal_model_manager.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  checkpoints
```

## 🛠️ Development

### Update the App
1. Edit `modal/apps/modal_app_fastapi.py`
2. Run `modal deploy modal/apps/modal_app_fastapi.py`
3. Test with `python modal/tests/modal_test_endpoints.py`

### Add New Models
1. See `docs/POPULAR_MODELS.md` for examples
2. Use `modal/scripts/modal_model_manager.sh download-url`

## 📞 Support

For issues or questions:
- Check `docs/` for detailed guides
- View logs: `modal app logs comfyui-api`
- Review `START_HERE.md` in the root directory

