# ComfyUI Modal Deployment

Deploy ComfyUI as a serverless API on Modal.com with GPU acceleration.

## 🚀 Quick Start

### 1. Deploy the App

```bash
modal deploy modal/apps/modal_app_fastapi.py
```

Your endpoint will be available at:
```
https://YOUR_WORKSPACE--comfyui-api-web.modal.run
```

### 2. Download a Model

```bash
# Download SDXL Turbo (fast, good quality)
modal run modal/apps/modal_app_fastapi.py::download_model \
  --url "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  --category checkpoints

# List your models
modal run modal/apps/modal_app_fastapi.py::list_models
```

### 3. Test the API

```bash
curl https://YOUR_WORKSPACE--comfyui-api-web.modal.run/
curl https://YOUR_WORKSPACE--comfyui-api-web.modal.run/system_stats
```

## 📁 Directory Structure

```
modal/
├── apps/
│   ├── modal_app_fastapi.py   # Main deployment file
│   ├── b2_storage.py          # Backblaze B2 integration
│   └── *.md                   # B2 documentation
├── docs/                      # Detailed documentation
├── scripts/                   # Helper scripts
├── tests/                     # Test files
├── SETUP_SECRETS.md          # Secret configuration guide
└── setup_secrets.sh          # Secret setup script
```

## 🔧 Optional: Configure Secrets

For full functionality, set up these optional secrets:

### Backblaze B2 (for image uploads)
```bash
modal secret create backblaze-b2-credentials \
  B2_APPLICATION_KEY_ID=your_key_id \
  B2_APPLICATION_KEY=your_key \
  B2_BUCKET_NAME=your_bucket
```

### Civitai API (for model downloads)
```bash
modal secret create civitai-api-key \
  CIVITAI_API_KEY=your_api_key
```

Or run `./modal/setup_secrets.sh` for an interactive setup.

## 💡 Common Commands

```bash
# Deploy
modal deploy modal/apps/modal_app_fastapi.py

# Check status
modal app list

# View logs
modal app logs comfyui-api

# Stop app
modal app stop comfyui-api

# Download model
modal run modal/apps/modal_app_fastapi.py::download_model --url "URL" --category checkpoints

# List models
modal run modal/apps/modal_app_fastapi.py::list_models

# Delete model
modal run modal/apps/modal_app_fastapi.py::delete_model --category checkpoints --filename "model.safetensors"
```

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/prompt` | POST | Queue a workflow |
| `/execute_and_upload` | POST | Execute + upload to B2 |
| `/queue` | GET | Queue status |
| `/history` | GET | Execution history |
| `/history/{id}` | GET | Specific execution |
| `/system_stats` | GET | GPU/system info |
| `/outputs` | GET | List output files |
| `/outputs/{file}` | GET | Download output file |
| `/object_info` | GET | Available nodes |

## 📚 Documentation

- **[Quick Start](docs/MODAL_QUICKSTART.md)** - Get started quickly
- **[Deployment Guide](docs/MODAL_DEPLOYMENT_GUIDE.md)** - Full deployment instructions
- **[Model Setup](docs/MODAL_MODEL_SETUP.md)** - Download and manage models
- **[Popular Models](docs/POPULAR_MODELS.md)** - Ready-to-use model URLs
- **[B2 Integration](apps/BACKBLAZE_B2_INTEGRATION.md)** - Backblaze B2 setup

## 🖥️ Hardware

- **GPU**: NVIDIA A10G (24GB VRAM)
- **Timeout**: 10 minutes per request
- **Scale-down**: 5 minutes idle

## 📞 Support

- View logs: `modal app logs comfyui-api`
- Check status: `modal app list`
- Modal docs: https://modal.com/docs
