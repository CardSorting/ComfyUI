# ComfyUI Model Download CLI Tool

This tool provides a command-line interface for downloading models to ComfyUI, designed specifically for headless implementations where you need to manage models programmatically.

## Features

- **Multiple Sources**: Download from Hugging Face Hub, Civitai, or direct URLs
- **All Model Types**: Support for checkpoints, LoRAs, VAEs, ControlNets, and more
- **Automatic Organization**: Models are automatically placed in correct directories
- **Progress Tracking**: Visual progress bars and download status
- **Model Validation**: Optional hash verification for downloaded files
- **Batch Downloads**: Download multiple models from configuration files
- **Model Discovery**: Search and list available models from multiple sources
- **Metadata Extraction**: Extract model information and metadata
- **Civitai Integration**: Full support for Civitai models with automatic type detection
- **Hugging Face Integration**: Full support for Hugging Face models including segmented/multi-part models
- **Smart URL Detection**: Automatically detects Civitai and Hugging Face URLs and extracts relevant IDs
- **Automatic Model Type Detection**: No need to specify model types - the tool automatically detects and places models in correct directories
- **Segmented Model Support**: Handles large models split into multiple files (e.g., "model-00001-of-00050.safetensors")

## Installation

### Basic Installation
The tool uses ComfyUI's existing dependencies. For full functionality, install additional packages:

```bash
# Install optional dependencies for enhanced features
pip install -r requirements-download.txt

# Or install manually
pip install huggingface_hub tqdm requests safetensors
```

### Quick Setup
```bash
# Make the wrapper script executable (already done)
chmod +x download_models.sh

# Install dependencies
./download_models.sh install-deps
```

## Usage

### Basic Commands

#### List Available Models
```bash
# List all models
./download_models.sh list

# List models of a specific type
./download_models.sh list --model-type checkpoints
```

#### Download Models
```bash
# Download from Hugging Face
./download_models.sh download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5

# Download from Civitai (multiple methods - all with automatic type detection!)
./download_models.sh download --source civitai --model-id 257749
./download_models.sh download --source civitai --civitai-url "https://civitai.com/models/257749/pony-diffusion-v6-xl"

# Download specific version from Civitai
./download_models.sh download --source civitai --model-id 257749 --version-id 290640

# Automatic URL detection (works with any Civitai or Hugging Face URL - no model type needed!)
./download_models.sh download --source url --url "https://civitai.com/models/257749/pony-diffusion-v6-xl"
./download_models.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"

# Download from direct URL
./download_models.sh download --model-type loras --source url --url https://example.com/model.safetensors
```

### Advanced Commands

#### Search for Models
```bash
# Search Hugging Face for models
./download_models.sh search "stable diffusion" --limit 5

# Search Civitai for models
./download_models.sh civitai search "anime" --limit 5

# Search Hugging Face for models
./download_models.sh huggingface search "stable diffusion" --limit 5

# Search with model type filter
./download_models.sh search "controlnet" --model-type controlnet --limit 10
```

#### Popular Models
```bash
# List popular models
./download_models.sh popular

# List popular models of specific type
./download_models.sh popular --model-type checkpoints

# List Civitai model type mappings
./download_models.sh civitai types

# List Hugging Face model type patterns
./download_models.sh huggingface types
```

#### Batch Downloads
```bash
# Download multiple models from config file
./download_models.sh batch models_config.json
```

### Direct Python Usage

You can also use the Python scripts directly:

```bash
# Basic tool
python download_models.py list
python download_models.py download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5

# Advanced tool
python download_models_advanced.py search --query "stable diffusion"
python download_models_advanced.py batch-download --config models_config.json
```

## Configuration

### Model Types
The tool supports all ComfyUI model types:
- `checkpoints` - Main diffusion models
- `loras` - LoRA adapters
- `vae` - Variational Autoencoders
- `controlnet` - ControlNet models
- `embeddings` - Text embeddings
- `upscale_models` - Upscaling models
- `clip_vision` - CLIP vision models
- `text_encoders` - Text encoders
- `diffusion_models` - Diffusion model components
- `style_models` - Style transfer models
- `hypernetworks` - Hypernetworks
- `photomaker` - PhotoMaker models
- `classifiers` - Classifier models
- `model_patches` - Model patches
- `audio_encoders` - Audio encoders

### Batch Download Configuration

Create a JSON configuration file for batch downloads:

```json
{
  "downloads": [
    {
      "name": "Stable Diffusion v1.5",
      "model_type": "checkpoints",
      "source": "huggingface",
      "repo_id": "runwayml/stable-diffusion-v1-5",
      "filename": "v1-5-pruned-emaonly.safetensors"
    },
    {
      "name": "Custom LoRA",
      "model_type": "loras",
      "source": "url",
      "url": "https://example.com/model.safetensors",
      "filename": "custom_lora.safetensors",
      "hash": "sha256_hash_here"
    }
  ],
  "settings": {
    "download_timeout": 600,
    "max_retries": 3,
    "verify_hashes": true,
    "create_backups": false
  }
}
```

## Examples

### Download Popular Models
```bash
# Download Stable Diffusion v1.5
./download_models.sh download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5

# Download Pony Diffusion V6 XL from Civitai
./download_models.sh download --model-type checkpoints --source civitai --model-id 257749

# Download VAE
./download_models.sh download --model-type vae --source huggingface --repo stabilityai/sd-vae-ft-mse

# Download ControlNet
./download_models.sh download --model-type controlnet --source huggingface --repo lllyasviel/sd-controlnet-canny
```

### Search and Download
```bash
# Search Hugging Face for models
./download_models.sh search "flux" --limit 3

# Search Civitai for models
./download_models.sh civitai search "realistic" --limit 3

# Download a found model from Hugging Face
./download_models.sh download --model-type checkpoints --source huggingface --repo black-forest-labs/FLUX.1-dev

# Download a found model from Civitai
./download_models.sh download --model-type checkpoints --source civitai --model-id 4201
```

### Batch Setup
```bash
# Create a batch config for common models
cat > my_models.json << EOF
{
  "downloads": [
    {
      "name": "SD 1.5",
      "model_type": "checkpoints",
      "source": "huggingface",
      "repo_id": "runwayml/stable-diffusion-v1-5"
    },
    {
      "name": "SD VAE",
      "model_type": "vae",
      "source": "huggingface",
      "repo_id": "stabilityai/sd-vae-ft-mse"
    }
  ]
}
EOF

# Download all models
./download_models.sh batch my_models.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the ComfyUI directory
   ```bash
   cd /path/to/ComfyUI
   ./download_models.sh list
   ```

2. **Permission Errors**: Ensure you have write permissions to the models directory
   ```bash
   ls -la models/
   ```

3. **Network Issues**: Use direct URLs if Hugging Face is blocked
   ```bash
   ./download_models.sh download --model-type checkpoints --source url --url "https://direct-link-to-model"
   ```

4. **Missing Dependencies**: Install required packages
   ```bash
   ./download_models.sh install-deps
   ```

### Debug Mode
Run with verbose logging:
```bash
python download_models.py --verbose download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5
```

## Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide with setup instructions and examples
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card for common commands
- **[DOCKER_HEADLESS_SETUP.md](DOCKER_HEADLESS_SETUP.md)** - Docker setup guide for headless ComfyUI
- **[CIVITAI_INTEGRATION_README.md](CIVITAI_INTEGRATION_README.md)** - Civitai-specific documentation
- **[HUGGINGFACE_INTEGRATION_SUMMARY.md](HUGGINGFACE_INTEGRATION_SUMMARY.md)** - Hugging Face documentation
- **[HUGGINGFACE_FILE_ORGANIZATION_FIX.md](HUGGINGFACE_FILE_ORGANIZATION_FIX.md)** - File organization details

## File Structure

```
ComfyUI/
├── download_models.py              # Basic download tool
├── download_models_advanced.py     # Advanced features
├── civitai_integration.py          # Civitai integration module
├── huggingface_integration.py      # Hugging Face integration module
├── download_models.sh              # Wrapper script
├── docker_management.sh            # Docker management script
├── requirements-download.txt       # Dependencies
├── models_config.json             # Sample batch config
├── civitai_models_config.json     # Civitai batch config
├── docker-compose.yml.template    # Docker Compose template
├── Dockerfile.template            # Dockerfile template
├── env.template                   # Environment variables template
├── USER_GUIDE.md                  # Complete user guide
├── QUICK_REFERENCE.md             # Quick reference card
├── DOCKER_HEADLESS_SETUP.md       # Docker setup guide
├── MODEL_DOWNLOAD_README.md       # This file
├── CIVITAI_INTEGRATION_README.md  # Civitai-specific documentation
├── HUGGINGFACE_INTEGRATION_SUMMARY.md  # Hugging Face documentation
└── HUGGINGFACE_FILE_ORGANIZATION_FIX.md  # File organization details
```

## Docker Integration

### Quick Docker Setup

```bash
# Setup Docker environment
./docker_management.sh setup

# Start ComfyUI in Docker
./docker_management.sh start

# Download models in Docker
./docker_management.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"

# Check status
./docker_management.sh status
```

For detailed Docker setup instructions, see [DOCKER_HEADLESS_SETUP.md](DOCKER_HEADLESS_SETUP.md).

## Integration with Headless ComfyUI

This tool is designed to work seamlessly with headless ComfyUI setups:

1. **Automated Setup**: Use batch downloads to set up models automatically
2. **CI/CD Integration**: Include model downloads in deployment scripts
3. **Docker Support**: Use in Docker containers for automated model management
4. **API Integration**: Call the Python scripts from your application code

### Example Docker Usage
```dockerfile
# In your Dockerfile
COPY download_models.py /app/
COPY models_config.json /app/
RUN python download_models.py batch-download --config models_config.json
```

## Platform Integrations

### Civitai Integration
For detailed information about Civitai integration, see [CIVITAI_INTEGRATION_README.md](CIVITAI_INTEGRATION_README.md).

### Hugging Face Integration
For detailed information about Hugging Face integration, see [HUGGINGFACE_INTEGRATION_SUMMARY.md](HUGGINGFACE_INTEGRATION_SUMMARY.md).

### Quick Civitai Setup
```bash
# Set your API key
export CIVITAI_API_KEY=your_api_key_here

# Search Civitai models
./download_models.sh civitai search "anime" --limit 5

# Download from Civitai (multiple ways)
./download_models.sh download --model-type checkpoints --source civitai --model-id 257749
./download_models.sh download --model-type checkpoints --source civitai --civitai-url "https://civitai.com/models/257749/pony-diffusion-v6-xl"

# Automatic URL detection (just paste any Civitai URL)
./download_models.sh download --model-type checkpoints --source url --url "https://civitai.com/models/257749/pony-diffusion-v6-xl"
```

## Contributing

To extend the tool:

1. Add new model sources in the downloader classes
2. Implement additional validation methods
3. Add support for new model formats
4. Create new configuration options
5. Extend Civitai integration with new features

## License

This tool follows the same license as ComfyUI.
