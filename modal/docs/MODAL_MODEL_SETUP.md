# Modal Model Setup Guide

Complete guide to downloading and managing models for your ComfyUI Modal deployment.

## 🎯 Quick Start

The **simplest way** to download models to Modal:

```bash
# 1. List current models
./modal_manage.sh list

# 2. Download SDXL Turbo (fast, good for testing)
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  checkpoints

# 3. Verify it downloaded
./modal_manage.sh list
```

---

## 📦 Available Tools

You have **three** model download tools:

### 1. **`modal_manage.sh`** ⭐ RECOMMENDED
Simple wrapper for Modal - use this for most cases.

```bash
./modal_manage.sh list                    # List models
./modal_manage.sh download-url URL CATEGORY
./modal_manage.sh delete CATEGORY FILENAME
```

### 2. **`modal run` commands** (Direct)
Call Modal functions directly from command line:

```bash
modal run modal/apps/modal_app_fastapi.py::list_models
modal run modal/apps/modal_app_fastapi.py::download_model --url "..." --category checkpoints
modal run modal/apps/modal_app_fastapi.py::delete_model --category checkpoints --filename "model.safetensors"
```

### 3. **Local tools** (For local ComfyUI, NOT Modal)
These work on your local machine:
- `download_models.py` - Basic downloader
- `download_models_advanced.py` - Advanced with search
- `civitai_models_config.json` - Configuration file

**⚠️ These download to local folders, NOT to Modal's volume.**

---

## 🚀 Common Download Scenarios

### Scenario 1: Download SDXL Turbo (Fastest for Testing)

```bash
# SDXL Turbo - ~7GB, only needs 1-4 steps to generate
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  checkpoints
```

### Scenario 2: Download SD 1.5 (Smaller, Classic)

```bash
# SD 1.5 Base - ~4GB
./modal_manage.sh download-url \
  "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  checkpoints

# SD 1.5 VAE (improves quality)
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors" \
  vae
```

### Scenario 3: Download SDXL Base (Full Quality)

```bash
# SDXL Base - ~7GB
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
  checkpoints

# SDXL VAE (improves quality)
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
  vae
```

### Scenario 4: Download LoRAs

```bash
# Download a LoRA from any direct URL
./modal_manage.sh download-url \
  "https://example.com/my_lora.safetensors" \
  loras \
  "my_custom_name.safetensors"
```

### Scenario 5: Download from CivitAI

```bash
# Use CivitAI API download URLs
# Find model ID on CivitAI page
./modal_manage.sh download-url \
  "https://civitai.com/api/download/models/MODEL_ID" \
  checkpoints \
  "model_name.safetensors"
```

---

## 📁 Model Categories

When downloading, use these categories:

| Category | Description | Examples |
|----------|-------------|----------|
| `checkpoints` | Main SD models | SD 1.5, SDXL, custom models |
| `vae` | VAE models | sdxl_vae, sd-vae-ft-mse |
| `loras` | LoRA models | Style LoRAs, character LoRAs |
| `controlnet` | ControlNet | Canny, depth, pose |
| `clip_vision` | CLIP models | For IPAdapter |
| `upscale_models` | Upscalers | RealESRGAN, UltraSharp |
| `embeddings` | Textual inversions | Negative embeddings |
| `unet` | UNet models | For advanced setups |

---

## 🔍 Managing Models

### List all models
```bash
./modal_manage.sh list
```

This shows:
- All models by category
- File sizes
- Total storage used

### Delete a model
```bash
./modal_manage.sh delete checkpoints "model_name.safetensors"
```

### Check Modal volume storage
```bash
modal volume list comfyui-models
```

---

## 💡 Tips & Best Practices

### 1. **Start Small**
- Download SDXL Turbo first (fast generation for testing)
- Test your workflow
- Add more models as needed

### 2. **Download Times**
- Large models (6-7 GB) take 5-15 minutes
- Modal has good download speeds
- You'll see progress in the terminal

### 3. **Storage Limits**
- Modal volumes have storage limits
- Delete unused models: `./modal_manage.sh delete`
- Check usage: `./modal_manage.sh list`

### 4. **File Naming**
- Use descriptive names for easier management
- Add version numbers: `sdxl_turbo_1.0.safetensors`
- Avoid spaces in filenames

### 5. **Getting Direct URLs**

**From Hugging Face:**
1. Go to model page
2. Click "Files and versions"
3. Right-click on file → "Copy link address"

**From CivitAI:**
1. Go to model page
2. Use format: `https://civitai.com/api/download/models/MODEL_ID`
3. Find MODEL_ID in the URL or page

---

## 🛠️ Advanced Usage

### Using `modal run` directly

```bash
# Download with all options
modal run modal_app_fastapi.py::download_model \
  --url "https://..." \
  --category "checkpoints" \
  --filename "custom_name.safetensors"

# List models
modal run modal_app_fastapi.py::list_models

# Delete model
modal run modal_app_fastapi.py::delete_model \
  --category "checkpoints" \
  --filename "model.safetensors"
```

### Batch downloads

Create a simple bash script:

```bash
#!/bin/bash
# download_my_models.sh

echo "Downloading essential models..."

./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  checkpoints

./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
  vae

echo "Done!"
```

Then run: `chmod +x download_my_models.sh && ./download_my_models.sh`

---

## 🐛 Troubleshooting

### "Function has not been hydrated" error
Your app needs to be deployed first:
```bash
modal deploy modal_app_fastapi.py
```

### Download timeout
For very large files, the function has a 2-hour timeout. If it times out:
1. Check your internet connection
2. Try a different model source
3. The file might be too large

### File already exists
If you want to re-download:
```bash
./modal_manage.sh delete checkpoints "model.safetensors"
./modal_manage.sh download-url "..." checkpoints
```

### Can't find model in ComfyUI
1. Check the category is correct
2. List models: `./modal_manage.sh list`
3. Restart your ComfyUI API (modal app stop, then access endpoint)

---

## 📚 Resources

### Finding Models
- **Hugging Face**: https://huggingface.co/models?other=stable-diffusion
- **CivitAI**: https://civitai.com/
- **ComfyUI Wiki**: https://github.com/comfyanonymous/ComfyUI/wiki/Model-Database

### Model Recommendations
- **Best for speed**: SDXL Turbo
- **Best quality**: SDXL Base 1.0
- **Smallest size**: SD 1.5
- **Most popular**: Realistic Vision, DreamShaper

---

## ⚡ Quick Reference

```bash
# List models
./modal_manage.sh list

# Download model
./modal_manage.sh download-url "URL" "CATEGORY" "FILENAME"

# Delete model
./modal_manage.sh delete "CATEGORY" "FILENAME"

# Check deployment
modal app list

# View logs
modal app logs comfyui-api
```

---

## 🎬 Complete Example Workflow

```bash
# 1. Deploy your app
modal deploy modal_app_fastapi.py

# 2. Check current models
./modal_manage.sh list

# 3. Download SDXL Turbo for testing
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  checkpoints

# 4. Verify download
./modal_manage.sh list

# 5. Test your ComfyUI endpoint
python modal_test_endpoints.py https://YOUR-ENDPOINT.modal.run

# 6. Success! 🎉
```

Need help? Check `POPULAR_MODELS.md` for more model URLs!

