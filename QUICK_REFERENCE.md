# ComfyUI Model Download CLI - Quick Reference

## 🚀 Setup

```bash
# Install dependencies
pip install -r requirements-download.txt

# Make executable
chmod +x download_models.sh
```

## 📥 Download Models

### Automatic Detection (Recommended)
```bash
# Just paste any URL - tool handles everything!
./download_models.sh download --source url --url "MODEL_URL"
```

### Platform-Specific
```bash
# Hugging Face
./download_models.sh download --source huggingface --repo "org/model"

# Civitai
./download_models.sh download --source civitai --model-id 12345

# Direct URL
./download_models.sh download --model-type checkpoints --source url --url "URL"
```

## 🔍 Search Models

```bash
# Search Hugging Face
./download_models.sh huggingface search --query "stable diffusion" --limit 5

# Search Civitai
./download_models.sh civitai search --query "anime" --limit 5
```

## 📋 List Models

```bash
# List all models
./download_models.sh list

# List by type
./download_models.sh list --model-type checkpoints
```

## 🎯 Common Examples

```bash
# Download Stable Diffusion XL
./download_models.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"

# Download Pony Diffusion
./download_models.sh download --source url --url "https://civitai.com/models/257749/pony-diffusion-v6-xl"

# Search for LoRA models
./download_models.sh civitai search --query "lora" --limit 10

# Download with API key
./download_models.sh download --source civitai --model-id 12345 --api-key YOUR_KEY
```

## 🔑 Authentication

```bash
# Set environment variables
export HUGGINGFACE_HUB_TOKEN=your_token
export CIVITAI_API_KEY=your_key

# Or use in commands
--hf-token YOUR_TOKEN
--api-key YOUR_KEY
```

## 📁 Model Types

| Type | Directory | Description |
|------|-----------|-------------|
| checkpoints | `models/checkpoints/` | Main models |
| loras | `models/loras/` | LoRA models |
| vae | `models/vae/` | VAE models |
| text_encoders | `models/text_encoders/` | Text encoders |
| unet | `models/unet/` | UNet models |
| controlnet | `models/controlnet/` | ControlNet models |
| embeddings | `models/embeddings/` | Text embeddings |
| upscale_models | `models/upscale_models/` | Upscaling models |

## 🛠️ Help

```bash
# Show help
./download_models.sh help

# Command-specific help
./download_models.sh download --help
./download_models.sh huggingface --help
./download_models.sh civitai --help
```

## ⚡ Pro Tips

1. **Use URLs**: Just paste any Hugging Face or Civitai URL for automatic detection
2. **API Keys**: Set up API keys for faster downloads and access to private models
3. **Batch Downloads**: Use JSON config files for multiple models
4. **Check Organization**: Files are automatically placed in correct ComfyUI directories
5. **Search First**: Use search to find models before downloading
