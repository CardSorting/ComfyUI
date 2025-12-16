# ComfyUI Serverless Plugin

A production-ready ComfyUI extension plugin that provides serverless deployment capabilities, headless mode utilities, and model download integrations for Civitai and HuggingFace.

**Built with industry best practices:** Configuration management, structured logging, error handling, retry mechanisms, caching, validation, and health checks.

## Features

- **Headless Mode Support**: Utilities for configuring ComfyUI in headless/serverless environments
- **Modal.com Deployment**: Helper functions and templates for deploying ComfyUI to Modal.com
- **Model Download Nodes**: ComfyUI nodes for downloading models from Civitai and HuggingFace
- **Easy Migration**: Plugin-based architecture allows easy updates and migration to new ComfyUI versions

### Enterprise-Grade Features

- ✅ **Configuration Management**: Pydantic-based config with environment variable support
- ✅ **Structured Logging**: JSON/text logging with context propagation
- ✅ **Error Handling**: Custom exception hierarchy with error codes
- ✅ **Retry Mechanisms**: Exponential backoff with circuit breaker pattern
- ✅ **Caching**: TTL-based and file-based caching
- ✅ **Input Validation**: Comprehensive URL, path, and type validation
- ✅ **Health Checks**: System health monitoring and dependency checks
- ✅ **Type Safety**: Comprehensive type hints and type definitions
- ✅ **Performance Monitoring**: Decorator-based performance tracking

## Installation

This plugin is part of the ComfyUI codebase. It will be automatically loaded when ComfyUI starts.

### Dependencies

The plugin uses existing ComfyUI integrations:
- `civitai_integration.py` (in ComfyUI root)
- `huggingface_integration.py` (in ComfyUI root)

Optional dependencies:
- `huggingface_hub` - For HuggingFace integration
- `modal` - For Modal.com deployment

## Usage

### Headless Mode

The plugin automatically detects and configures headless mode when the `COMFYUI_HEADLESS` environment variable is set:

```bash
export COMFYUI_HEADLESS=1
python main.py
```

Or programmatically:

```python
from custom_nodes.comfyui_serverless.serverless.headless_utils import configure_headless_mode

configure_headless_mode(enable=True)
```

### Model Download Nodes

The plugin provides three nodes for downloading models:

1. **CivitaiDownload**: Download models from Civitai.com
2. **HuggingFaceDownload**: Download models from HuggingFace Hub
3. **GenericModelDownload**: Auto-detect source and download

These nodes can be used in ComfyUI workflows or called programmatically.

### Modal.com Deployment

Generate a Modal deployment template:

```python
from custom_nodes.comfyui_serverless.serverless.modal_host import create_modal_comfyui_app

modal_code = create_modal_comfyui_app(
    app_name="my-comfyui",
    comfyui_root="/path/to/ComfyUI"
)

# Save to file
with open("modal_app.py", "w") as f:
    f.write(modal_code)
```

## Plugin Structure

```
comfyui-serverless/
├── __init__.py              # Plugin entrypoint
├── extension.py             # ComfyExtension implementation
├── core/                    # Core utilities (NEW)
│   ├── config.py           # Configuration management
│   ├── exceptions.py       # Exception hierarchy
│   ├── logging.py          # Structured logging
│   ├── types.py            # Type definitions
│   ├── retry.py            # Retry mechanisms
│   ├── cache.py            # Caching utilities
│   ├── validation.py       # Input validation
│   └── health.py           # Health checks
├── nodes/                   # ComfyUI nodes
│   └── model_download.py
├── integrations/            # Model download integrations
│   ├── civitai.py
│   └── huggingface.py
├── serverless/              # Serverless utilities
│   ├── headless_utils.py
│   └── modal_host.py
├── ARCHITECTURE.md          # Architecture documentation
├── ENHANCEMENTS.md          # Enhancement details
└── README.md
```

## Migration from Standalone Scripts

The plugin is designed to work alongside existing standalone scripts:
- `main_headless.py` - Still works, but plugin provides additional utilities
- `civitai_integration.py` - Plugin imports from this (no duplication)
- `huggingface_integration.py` - Plugin imports from this (no duplication)
- `modal/apps/modal_app_fastapi.py` - Can use plugin utilities

## Future ComfyUI Version Compatibility

The plugin is designed to be easily updated for new ComfyUI versions:

1. **API Compatibility**: Uses ComfyUI's extension API (V3), which is stable
2. **Import Strategy**: Imports from main codebase, reducing duplication
3. **Version Detection**: Can detect ComfyUI version and adapt if needed

## Development

### Testing

Test the plugin loading:

```python
import asyncio
from custom_nodes.comfyui_serverless import comfy_entrypoint

async def test():
    extension = await comfy_entrypoint()
    nodes = await extension.get_node_list()
    print(f"Loaded {len(nodes)} nodes")

asyncio.run(test())
```

### Adding New Features

1. Add nodes in `nodes/` directory
2. Add integrations in `integrations/` directory
3. Add utilities in `serverless/` directory
4. Update `extension.py` to include new nodes

## License

Same license as ComfyUI.

## Contributing

Contributions welcome! Please ensure:
- Code follows ComfyUI plugin patterns
- Tests are included for new features
- Documentation is updated

