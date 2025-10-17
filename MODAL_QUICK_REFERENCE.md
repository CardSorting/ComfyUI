# Modal Quick Reference

All Modal-related files have been organized in the `modal/` directory for better navigation.

## 📂 File Organization

```
ComfyUI/
├── modal/                              # All Modal files here
│   ├── apps/                           # Modal applications
│   │   └── modal_app_fastapi.py       # 🚀 Main ComfyUI app
│   ├── scripts/                        # Helper scripts
│   │   ├── modal_model_manager.sh     # 🛠️  Model manager CLI
│   │   ├── modal_download_model.py    # Python downloader
│   │   └── modal_setup_wizard.py      # Setup wizard
│   ├── tests/                          # Test scripts
│   │   ├── modal_test_endpoints.py    # Endpoint tester
│   │   └── ...
│   ├── docs/                           # Documentation
│   │   ├── MODAL_MODEL_SETUP.md       # 📘 Model setup guide
│   │   ├── POPULAR_MODELS.md          # Model URLs
│   │   └── MODAL_*.md                 # Other guides
│   └── README.md                       # 📖 Main Modal docs
│
├── modal_deploy.sh                     # ⚡ Quick deploy wrapper
└── modal_manage.sh                     # ⚡ Quick model manager wrapper
```

## ⚡ Quick Commands

### Deploy ComfyUI
```bash
./modal_deploy.sh
# or
modal deploy modal/apps/modal_app_fastapi.py
```

### Manage Models
```bash
# List models
./modal_manage.sh list

# Download a model
./modal_manage.sh download-url "https://..." checkpoints

# Delete a model  
./modal_manage.sh delete checkpoints model.safetensors
```

### Test Deployment
```bash
python modal/tests/modal_test_endpoints.py YOUR_ENDPOINT
```

### Check Status
```bash
modal app list                  # List all apps
modal app logs comfyui-api      # View logs
modal app stop comfyui-api      # Stop the app
```

## 📚 Documentation

For detailed information, see:

- **`modal/README.md`** - Main Modal documentation
- **`modal/docs/MODAL_MODEL_SETUP.md`** - Complete model setup guide
- **`modal/docs/POPULAR_MODELS.md`** - Ready-to-use model commands
- **`START_HERE.md`** - General ComfyUI setup

## 🔗 Your Deployed App

After deployment, find your endpoint:
```
https://YOUR_WORKSPACE--comfyui-api-web.modal.run
```

## 💡 Common Workflows

### First Time Setup
```bash
# 1. Deploy the app
./modal_deploy.sh

# 2. Download SDXL Turbo (fast for testing)
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  checkpoints

# 3. Test it
python modal/tests/modal_test_endpoints.py YOUR_ENDPOINT
```

### Add More Models
```bash
# Check what you have
./modal_manage.sh list

# Download SD 1.5
./modal_manage.sh download-url \
  "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  checkpoints

# Download a VAE
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
  vae
```

### Update Your Deployment
```bash
# 1. Edit the app
nano modal/apps/modal_app_fastapi.py

# 2. Redeploy
./modal_deploy.sh

# 3. Test
python modal/tests/modal_test_endpoints.py YOUR_ENDPOINT
```

## 🎯 Next Steps

1. **Explore the docs**: Check `modal/docs/` for guides
2. **Download models**: See `modal/docs/POPULAR_MODELS.md`
3. **Test your setup**: Run `python modal/tests/modal_test_endpoints.py`
4. **Build workflows**: Create ComfyUI workflows and run via API

Need help? Check `modal/README.md` or `modal/docs/` for detailed guides!

