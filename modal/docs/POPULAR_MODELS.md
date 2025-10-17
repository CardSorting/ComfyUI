# Popular ComfyUI Models

This file contains direct download URLs for popular ComfyUI models that you can use with the `modal_download_model.py` script.

## Usage

```bash
# Download a model
python modal_download_model.py download "URL" --category "CATEGORY"

# List all models
python modal_download_model.py list

# Delete a model
python modal_download_model.py delete CATEGORY FILENAME
```

---

## Stable Diffusion XL Models

### SDXL Base 1.0
```bash
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
  --category checkpoints
```

### SDXL Turbo
```bash
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
  --category checkpoints
```

---

## Stable Diffusion 1.5 Models

### SD 1.5 Base
```bash
python modal_download_model.py download \
  "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  --category checkpoints
```

### Realistic Vision V5.1
```bash
python modal_download_model.py download \
  "https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/Realistic_Vision_V5.1_fp16-no-ema.safetensors" \
  --category checkpoints
```

---

## VAE Models

### SDXL VAE
```bash
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
  --category vae
```

### SD 1.5 VAE
```bash
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors" \
  --category vae
```

---

## ControlNet Models

### SDXL ControlNet Canny
```bash
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-canny-rank256.safetensors" \
  --category controlnet
```

### SD 1.5 ControlNet Canny
```bash
python modal_download_model.py download \
  "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth" \
  --category controlnet
```

---

## Upscaler Models

### 4x-UltraSharp
```bash
python modal_download_model.py download \
  "https://huggingface.co/Kim2091/UltraSharp/resolve/main/4x-UltraSharp.pth" \
  --category upscale_models
```

### RealESRGAN x4plus
```bash
python modal_download_model.py download \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth" \
  --category upscale_models
```

---

## CLIP Models

### CLIP Vision (for IPAdapter)
```bash
python modal_download_model.py download \
  "https://huggingface.co/openai/clip-vit-large-patch14/resolve/main/pytorch_model.bin" \
  --category clip_vision \
  --filename "clip_vision_large.bin"
```

---

## Quick Start - Minimal Setup

For a basic SDXL setup, download these:

```bash
# 1. SDXL Base Model (~6.9 GB)
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
  --category checkpoints

# 2. SDXL VAE (~335 MB)
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
  --category vae

# 3. Check what you have
python modal_download_model.py list
```

---

## Quick Start - SD 1.5 Setup

For a basic SD 1.5 setup:

```bash
# 1. SD 1.5 Model (~4.3 GB)
python modal_download_model.py download \
  "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  --category checkpoints

# 2. SD 1.5 VAE (~335 MB)
python modal_download_model.py download \
  "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors" \
  --category vae

# 3. Check what you have
python modal_download_model.py list
```

---

## Notes

### Model Categories
- `checkpoints`: Main SD models (SD 1.5, SDXL, etc.)
- `vae`: VAE models for better image quality
- `loras`: LoRA fine-tuning models
- `controlnet`: ControlNet models for guided generation
- `clip_vision`: CLIP models for image understanding
- `upscale_models`: Upscaling models
- `embeddings`: Textual inversion embeddings

### Finding More Models
- **Hugging Face**: https://huggingface.co/models?other=stable-diffusion
- **CivitAI**: https://civitai.com/ (use API download links)
- **Comfy Models**: https://github.com/comfyanonymous/ComfyUI/wiki/Model-Database

### CivitAI Downloads
For CivitAI, use the API download URL format:
```
https://civitai.com/api/download/models/MODEL_ID
```

You can find the model ID in the URL or on the model page.

### Tips
1. Start small - download one checkpoint and its VAE first
2. Use SDXL Turbo for faster generation (fewer steps needed)
3. VAE models improve image quality significantly
4. Large models take time to download (6-7 GB for SDXL)
5. Check available space: Modal volumes have storage limits

