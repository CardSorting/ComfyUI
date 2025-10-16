# ComfyUI on Modal - Quick Start

Get ComfyUI running on Modal.com in 5 minutes.

## Prerequisites

- Modal account (sign up at [modal.com](https://modal.com))
- Python 3.8+
- Basic familiarity with command line

## Step-by-Step Setup

### 1. Install Modal

```bash
pip install modal
```

### 2. Authenticate

```bash
modal setup
```

This opens your browser to authenticate with Modal.

### 3. Deploy ComfyUI

From your ComfyUI directory:

```bash
modal deploy modal_app.py
```

Expected output:
```
✓ Created objects.
├── 🔨 Created function fastapi_app.
├── 🔨 Created function download_models.
└── 🔨 Created function generate_image.
✓ App deployed! 🎉

Web endpoint: https://your-workspace--comfyui-fastapi-app.modal.run
```

### 4. Upload Models

Upload your first model:

```bash
# Example: Upload a local model file
modal volume put comfyui-models /path/to/model.safetensors /checkpoints/model.safetensors
```

Or use the helper to download models:

```bash
# Edit modal_app.py to add model URLs, then run:
modal run modal_app.py::download_models
```

### 5. Test the Deployment

```bash
# Test the API
python modal_test.py https://your-workspace--comfyui-fastapi-app.modal.run
```

Or use curl:

```bash
# Check system stats
curl https://your-workspace--comfyui-fastapi-app.modal.run/system_stats

# Get available nodes
curl https://your-workspace--comfyui-fastapi-app.modal.run/object_info
```

## Using the API

### Get Your Endpoint URL

After deployment, Modal shows your endpoint:
```
https://your-workspace--comfyui-fastapi-app.modal.run
```

### Submit a Workflow

1. Create a workflow in ComfyUI
2. Export it (Dev Save API Format)
3. Submit via API:

```bash
curl -X POST https://your-endpoint.modal.run/prompt \
  -H "Content-Type: application/json" \
  -d @workflow.json
```

### Python Example

```python
import requests
import json

ENDPOINT = "https://your-endpoint.modal.run"

# Load workflow
with open("workflow.json") as f:
    workflow = json.load(f)

# Submit
response = requests.post(
    f"{ENDPOINT}/prompt",
    json={"prompt": workflow}
)

print(f"Queued: {response.json()['prompt_id']}")
```

## Managing Your Deployment

### View Logs

```bash
modal app logs comfyui --follow
```

### Check Status

```bash
modal app list
modal app show comfyui
```

### Update Deployment

Make changes to `modal_app.py`, then:

```bash
modal deploy modal_app.py
```

Zero-downtime deployment!

### Stop Deployment

```bash
modal app stop comfyui
```

**Note:** This is irreversible. Redeploy with `modal deploy` to restart.

## Volume Management

### List Volumes

```bash
modal volume list
```

### Browse Volume Contents

```bash
# List root
modal volume ls comfyui-models

# List checkpoints
modal volume ls comfyui-models /checkpoints
```

### Upload Files

```bash
# Single file
modal volume put comfyui-models local_model.safetensors /checkpoints/model.safetensors

# Directory
modal volume put comfyui-models ./my_loras /loras
```

### Download Files

```bash
# Download a file
modal volume get comfyui-models /checkpoints/model.safetensors ./local_model.safetensors

# Download directory
modal volume get comfyui-models /outputs ./local_outputs
```

## GPU Configuration

Edit `modal_app.py` to change GPU:

```python
# Current default (balanced)
GPU_CONFIG = modal.gpu.A10G()  # ~$1.10/hour, 24GB VRAM

# Budget option
GPU_CONFIG = modal.gpu.T4()  # ~$0.60/hour, 16GB VRAM

# High performance
GPU_CONFIG = modal.gpu.A100()  # ~$4.00/hour, 40GB/80GB VRAM
```

Then redeploy:

```bash
modal deploy modal_app.py
```

## Cost Optimization Tips

1. **Start with T4** for testing
2. **Use A10G** for production SDXL workflows
3. **Adjust idle timeout** to balance cost vs. cold starts:
   ```python
   CONTAINER_IDLE_TIMEOUT = 300  # 5 minutes (default)
   ```
4. **Monitor usage** at https://modal.com/usage

## Troubleshooting

### "Command not found: modal"

```bash
# Ensure modal is installed
pip install modal

# Try with python -m
python -m modal setup
```

### "GPU out of memory"

Use a larger GPU in `modal_app.py`:

```python
GPU_CONFIG = modal.gpu.A100()
```

### Models not found

Verify uploads:

```bash
modal volume ls comfyui-models /checkpoints
```

### Deployment failed

Check logs:

```bash
modal app logs comfyui
```

## Next Steps

- ✅ Read the full [MODAL_DEPLOYMENT_GUIDE.md](MODAL_DEPLOYMENT_GUIDE.md)
- ✅ Configure your GPU preferences
- ✅ Upload your models
- ✅ Test with your workflows
- ✅ Integrate with your application

## Support

- **Modal Docs**: https://modal.com/docs
- **Modal Discord**: https://discord.gg/modal
- **ComfyUI GitHub**: https://github.com/comfyanonymous/ComfyUI

## Estimated Costs

**Example usage (A10G GPU):**

| Scenario | Time | Cost |
|----------|------|------|
| Single SDXL image | 15s | ~$0.005 |
| 10 images (cold start) | 45s + 10×15s | ~$0.064 |
| 10 images (warm) | 10×15s | ~$0.046 |
| Per hour continuous | 3600s | $1.10 |

**Tips:**
- First request includes ~30s cold start
- Subsequent requests (within idle timeout) are faster
- Only billed for actual usage
- No cost when idle

---

**Ready to deploy?** Run `modal deploy modal_app.py` and you're live! 🚀

