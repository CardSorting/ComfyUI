# ComfyUI Model Download CLI - User Guide

## 🚀 Quick Start

The ComfyUI Model Download CLI is a powerful tool that allows you to download models from Hugging Face, Civitai, and direct URLs with automatic type detection and proper file organization.

## 📋 Prerequisites

- Python 3.7 or higher
- ComfyUI installed
- Internet connection

## ⚡ Installation

### 1. Install Dependencies

```bash
# Navigate to your ComfyUI directory
cd /path/to/ComfyUI

# Install required dependencies
pip install -r requirements-download.txt
```

### 2. Make Scripts Executable

```bash
# Make the shell wrapper executable
chmod +x download_models.sh
```

## 🎯 Basic Usage

### Download Models with Automatic Detection

The easiest way to use the tool is to simply paste any model URL:

```bash
# Download from Hugging Face (auto-detects model type and organizes files)
./download_models.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"

# Download from Civitai (auto-detects model type)
./download_models.sh download --source url --url "https://civitai.com/models/257749/pony-diffusion-v6-xl"

# Download from direct URL (requires model type)
./download_models.sh download --model-type checkpoints --source url --url "https://example.com/model.safetensors"
```

## 🔍 Search and Discovery

### Search Hugging Face Models

```bash
# Search for models
./download_models.sh huggingface search --query "stable diffusion" --limit 5

# Search with API token for private models
./download_models.sh huggingface search --query "anime" --limit 10 --hf-token YOUR_TOKEN
```

### Search Civitai Models

```bash
# Search Civitai models
./download_models.sh civitai search --query "anime" --limit 5

# Search with API key
./download_models.sh civitai search --query "realistic" --limit 10 --api-key YOUR_API_KEY
```

## 📁 Model Types and Organization

The tool automatically detects model types and places them in the correct ComfyUI directories:

| Model Type | Directory | Description |
|------------|-----------|-------------|
| Checkpoints | `models/checkpoints/` | Main Stable Diffusion models |
| LoRA | `models/loras/` | Low-Rank Adaptation models |
| VAE | `models/vae/` | Variational Autoencoder models |
| Text Encoders | `models/text_encoders/` | CLIP text encoders |
| UNet | `models/unet/` | UNet diffusion models |
| ControlNet | `models/controlnet/` | ControlNet models |
| Embeddings | `models/embeddings/` | Textual inversion embeddings |
| Upscalers | `models/upscale_models/` | Image upscaling models |

## 🎨 Platform-Specific Usage

### Hugging Face Hub

```bash
# Download by repository ID
./download_models.sh download --source huggingface --repo "runwayml/stable-diffusion-v1-5"

# Download specific branch
./download_models.sh download --source huggingface --repo "stabilityai/stable-diffusion-xl-base-1.0" --branch "main"

# Download with URL (auto-extracts repo info)
./download_models.sh download --source huggingface --huggingface-url "https://huggingface.co/runwayml/stable-diffusion-v1-5"

# List Hugging Face model type patterns
./download_models.sh huggingface types
```

### Civitai

```bash
# Download by model ID
./download_models.sh download --source civitai --model-id 257749

# Download specific version
./download_models.sh download --source civitai --model-id 257749 --version-id 290640

# Download with URL (auto-extracts IDs)
./download_models.sh download --source civitai --civitai-url "https://civitai.com/models/257749/pony-diffusion-v6-xl"

# List Civitai model type mappings
./download_models.sh civitai types
```

## 🔧 Advanced Features

### Batch Downloads

Create a configuration file for batch downloads:

```json
{
  "models": [
    {
      "name": "Stable Diffusion XL",
      "source": "huggingface",
      "repo": "stabilityai/stable-diffusion-xl-base-1.0"
    },
    {
      "name": "Pony Diffusion",
      "source": "civitai",
      "model_id": 257749
    }
  ]
}
```

Then run:
```bash
./download_models.sh batch models_config.json
```

### Model Information

```bash
# Get information about a downloaded model
./download_models.sh info --model-type checkpoints --filename "model.safetensors"
```

### List Available Models

```bash
# List all models
./download_models.sh list

# List models of specific type
./download_models.sh list --model-type checkpoints
./download_models.sh list --model-type loras
```

## 🔑 Authentication Setup

### Hugging Face API Token

For private models or higher rate limits:

```bash
# Set environment variable
export HUGGINGFACE_HUB_TOKEN=your_token_here

# Or use in commands
./download_models.sh download --source huggingface --repo "private/repo" --hf-token your_token
```

### Civitai API Key

For Civitai downloads:

```bash
# Set environment variable
export CIVITAI_API_KEY=your_api_key_here

# Or use in commands
./download_models.sh download --source civitai --model-id 12345 --api-key your_key
```

## 📊 Examples by Use Case

### 🎨 For Artists

```bash
# Download a popular anime model
./download_models.sh download --source url --url "https://civitai.com/models/128713/dreamshaper-v8"

# Download a realistic model
./download_models.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"

# Search for LoRA models
./download_models.sh civitai search --query "lora anime" --limit 5
```

### 🔧 For Developers

```bash
# Download models programmatically
python3 download_models.py download --source huggingface --repo "runwayml/stable-diffusion-v1-5"

# Get model information
python3 download_models.py info --model-type checkpoints --filename "model.safetensors"

# Search with custom parameters
python3 download_models.py huggingface search --query "controlnet" --limit 20
```

### 🏢 For Enterprise

```bash
# Batch download multiple models
./download_models.sh batch enterprise_models.json

# Download with specific organization
./download_models.sh download --source huggingface --repo "organization/model" --hf-token $HF_TOKEN
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Command not found" Error
```bash
# Make sure the script is executable
chmod +x download_models.sh

# Use full path if needed
/path/to/ComfyUI/download_models.sh help
```

#### 2. "Python not found" Error
```bash
# Use python3 explicitly
python3 download_models.py help

# Or create an alias
alias python=python3
```

#### 3. "Permission denied" Error
```bash
# Check file permissions
ls -la download_models.sh

# Fix permissions
chmod +x download_models.sh
```

#### 4. "Module not found" Error
```bash
# Install missing dependencies
pip install huggingface_hub requests tqdm

# Or install all requirements
pip install -r requirements-download.txt
```

### Getting Help

```bash
# Show help
./download_models.sh help

# Show specific command help
./download_models.sh download --help
./download_models.sh huggingface --help
./download_models.sh civitai --help
```

## 📈 Performance Tips

### 1. Use API Keys
- Set up Hugging Face and Civitai API keys for higher rate limits
- Reduces download time for multiple models

### 2. Batch Downloads
- Use batch configuration files for multiple models
- More efficient than individual downloads

### 3. Selective Downloads
- Use specific filenames to download only needed files
- Reduces bandwidth and storage usage

### 4. Local Caching
- The tool uses Hugging Face Hub's built-in caching
- Subsequent downloads of the same model are faster

## 🔄 Integration with ComfyUI

### Automatic Detection
The tool automatically places models in directories that ComfyUI expects:

```
ComfyUI/
├── models/
│   ├── checkpoints/          # Main models
│   ├── loras/               # LoRA models
│   ├── vae/                 # VAE models
│   ├── text_encoders/       # Text encoders
│   ├── unet/                # UNet models
│   ├── controlnet/          # ControlNet models
│   ├── embeddings/          # Text embeddings
│   └── upscale_models/      # Upscaling models
```

### Custom Model Paths
If you use custom model directories, configure them in `extra_model_paths.yaml`:

```yaml
checkpoints:
  - /path/to/custom/checkpoints
loras:
  - /path/to/custom/loras
```

## 🎯 Best Practices

### 1. Organize Your Models
- Use descriptive names for model directories
- Keep track of model sources and versions
- Regularly clean up unused models

### 2. Use Version Control
- Keep track of which models you've downloaded
- Use batch configuration files for reproducible setups

### 3. Monitor Storage
- Large models can consume significant disk space
- Use `./download_models.sh list` to see what you have

### 4. Stay Updated
- Regularly update the tool for new features
- Check for new model releases

## 📚 Additional Resources

- **ComfyUI Documentation**: [docs.comfy.org](https://docs.comfy.org)
- **Hugging Face Hub**: [huggingface.co/docs/hub](https://huggingface.co/docs/hub)
- **Civitai API**: [civitai.com/api-docs](https://civitai.com/api-docs)

## 🤝 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the error messages carefully
3. Ensure all dependencies are installed
4. Verify your internet connection
5. Check API keys and permissions

## 🎉 Conclusion

The ComfyUI Model Download CLI makes it easy to manage models for your ComfyUI setup. With automatic type detection, proper file organization, and support for multiple platforms, you can focus on creating rather than managing files.

Happy creating! 🎨
