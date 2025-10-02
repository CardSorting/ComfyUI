# Civitai Integration for ComfyUI Model Download CLI

This document describes the Civitai integration features added to the ComfyUI Model Download CLI tool.

## Overview

The Civitai integration allows you to:
- Search for models on Civitai
- Download models directly from Civitai
- Automatically organize models into the correct ComfyUI directories
- Extract and save model metadata

## Features

### ✅ Model Type Detection and Auto-Assignment
The tool automatically detects Civitai model types and assigns them to the correct ComfyUI directories:

| Civitai Type | ComfyUI Directory |
|--------------|-------------------|
| Checkpoint | `models/checkpoints/` |
| LORA | `models/loras/` |
| LoCon | `models/loras/` |
| TextualInversion | `models/embeddings/` |
| Hypernetwork | `models/hypernetworks/` |
| AestheticGradient | `models/embeddings/` |
| Controlnet | `models/controlnet/` |
| Poses | `models/controlnet/` |
| VAE | `models/vae/` |
| Upscaler | `models/upscale_models/` |
| MotionModule | `models/motion_modules/` |
| Wildcards | `models/wildcards/` |
| Other | `models/checkpoints/` (fallback) |

### ✅ Metadata Extraction
When downloading models from Civitai, the tool automatically saves metadata including:
- Model name and description
- Creator information
- Download statistics
- Model tags and categories
- File information and hashes

## Usage

### Basic Commands

#### List Civitai Model Types
```bash
./download_models.sh civitai types
```

#### Search Civitai Models
```bash
# Search for models
./download_models.sh civitai search --query "anime" --limit 5

# Search with model type filter
./download_models.sh civitai search --query "realistic" --model-type "Checkpoint" --limit 3
```

#### Download from Civitai
```bash
# Download by model ID (uses latest version)
./download_models.sh download --model-type checkpoints --source civitai --model-id 257749

# Download specific version
./download_models.sh download --model-type checkpoints --source civitai --model-id 257749 --version-id 290640

# Download with API key
./download_models.sh download --model-type checkpoints --source civitai --model-id 257749 --api-key YOUR_API_KEY
```

### Advanced Usage

#### Direct Python Usage
```bash
# Search models
python3 download_models.py civitai search --query "dreamshaper" --limit 5

# Download model
python3 download_models.py download --model-type checkpoints --source civitai --model-id 128713

# List model types
python3 download_models.py civitai types
```

#### Batch Downloads with Civitai
Create a configuration file (`civitai_models_config.json`):
```json
{
  "downloads": [
    {
      "name": "DreamShaper v8",
      "model_type": "checkpoints",
      "source": "civitai",
      "model_id": 128713,
      "version_id": 146759
    },
    {
      "name": "Realistic Vision v6.0",
      "model_type": "checkpoints", 
      "source": "civitai",
      "model_id": 4201
    }
  ],
  "settings": {
    "civitai_api_key": "YOUR_API_KEY"
  }
}
```

Then run:
```bash
./download_models.sh batch civitai_models_config.json
```

## API Key Setup

### Getting a Civitai API Key
1. Go to [Civitai.com](https://civitai.com)
2. Sign in to your account
3. Go to Account Settings → API Keys
4. Generate a new API key

### Using the API Key
You can provide the API key in several ways:

1. **Command line argument:**
   ```bash
   ./download_models.sh download --source civitai --model-id 12345 --api-key YOUR_KEY
   ```

2. **Environment variable:**
   ```bash
   export CIVITAI_API_KEY=YOUR_KEY
   ./download_models.sh download --source civitai --model-id 12345
   ```

3. **Configuration file:**
   ```json
   {
     "settings": {
       "civitai_api_key": "YOUR_KEY"
     }
   }
   ```

## Model Discovery

### Finding Model IDs
1. **Via Civitai Website:**
   - Go to any model page on Civitai
   - The model ID is in the URL: `https://civitai.com/models/12345/model-name`
   - The version ID is in the version URL: `https://civitai.com/models/12345/model-name?modelVersionId=67890`

2. **Via Search:**
   ```bash
   ./download_models.sh civitai search --query "model name" --limit 10
   ```

### Popular Models
Some popular models you can download:

| Model | ID | Type | Description |
|-------|----|----- |-------------|
| Pony Diffusion V6 XL | 257749 | Checkpoint | Versatile SDXL model |
| DreamShaper v8 | 128713 | Checkpoint | Realistic art model |
| Realistic Vision v6.0 | 4201 | Checkpoint | Photorealistic model |
| ChilloutMix | 6424 | Checkpoint | Realistic portrait model |

## File Organization

### Automatic Directory Assignment
The tool automatically places downloaded models in the correct directories based on their type:

```
ComfyUI/
├── models/
│   ├── checkpoints/          # Main diffusion models
│   ├── loras/               # LoRA adapters
│   ├── vae/                 # VAE models
│   ├── controlnet/          # ControlNet models
│   ├── embeddings/          # Textual inversions
│   ├── hypernetworks/       # Hypernetworks
│   ├── upscale_models/      # Upscaling models
│   └── ...
```

### Metadata Files
Each downloaded model gets a corresponding `.civitai.json` metadata file:
```
models/checkpoints/
├── dreamshaper_v8.safetensors
├── dreamshaper_v8.safetensors.civitai.json
├── realistic_vision_v6.safetensors
└── realistic_vision_v6.safetensors.civitai.json
```

## Error Handling

### Common Issues

1. **API Key Required:**
   ```
   Error: Authentication required for this model
   ```
   Solution: Provide an API key using `--api-key` or set `CIVITAI_API_KEY` environment variable.

2. **Model Not Found:**
   ```
   Error: Model ID 12345 not found
   ```
   Solution: Verify the model ID exists on Civitai.

3. **Network Issues:**
   ```
   Error: Failed to download from Civitai
   ```
   Solution: Check your internet connection and try again.

4. **Permission Denied:**
   ```
   Error: No write permission to models directory
   ```
   Solution: Ensure you have write permissions to the ComfyUI models directory.

## Integration with Existing Tools

### ComfyUI Compatibility
The Civitai integration works seamlessly with ComfyUI's existing model management:
- Uses ComfyUI's `folder_paths` system
- Respects custom model directory configurations
- Compatible with `extra_model_paths.yaml`

### Headless ComfyUI
Perfect for headless ComfyUI deployments:
- No web interface required
- Automated model setup
- CI/CD pipeline integration
- Docker container support

## Examples

### Complete Setup Example
```bash
# 1. Install dependencies
./download_models.sh install-deps

# 2. Set API key
export CIVITAI_API_KEY=your_api_key_here

# 3. Search for models
./download_models.sh civitai search --query "realistic" --limit 5

# 4. Download a model
./download_models.sh download --model-type checkpoints --source civitai --model-id 4201

# 5. Verify download
./download_models.sh list --model-type checkpoints
```

### Docker Integration
```dockerfile
# In your Dockerfile
COPY download_models.py /app/
COPY civitai_models_config.json /app/
ENV CIVITAI_API_KEY=your_key_here
RUN python3 download_models.py batch-download --config civitai_models_config.json
```

## Troubleshooting

### Debug Mode
Run with verbose logging:
```bash
python3 download_models.py --verbose civitai search --query "test"
```

### Test API Connection
```bash
# Test basic API access
curl -s "https://civitai.com/api/v1/models?limit=1" | jq '.items[0].name'
```

### Check Dependencies
```bash
# Verify required packages
pip list | grep requests
```

## Future Enhancements

Potential improvements:
- Model update checking
- Automatic model optimization
- Integration with other model sources
- Model dependency resolution
- Cloud storage integration

## Support

For issues or questions:
1. Check the main [MODEL_DOWNLOAD_README.md](MODEL_DOWNLOAD_README.md)
2. Review error messages and logs
3. Verify API key and permissions
4. Test with simple model downloads first
