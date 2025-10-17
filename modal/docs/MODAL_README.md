# Running ComfyUI on Modal.com

Complete guide and implementation for deploying ComfyUI as a serverless GPU application on Modal.com.

## 📋 What is This?

This is a production-ready deployment setup that allows you to run [ComfyUI](https://github.com/comfyanonymous/ComfyUI) on [Modal.com](https://modal.com) - a serverless GPU platform. Instead of managing your own servers, you can deploy ComfyUI to the cloud and pay only for what you use.

## 🎯 Why Modal.com?

| Feature | Benefit |
|---------|---------|
| **Serverless** | No servers to manage, automatic scaling |
| **GPU Access** | NVIDIA T4, A10G, A100 GPUs on-demand |
| **Pay-per-use** | Billed per second, $0 when idle |
| **Fast Deployment** | Deploy in minutes, not hours |
| **Auto-scaling** | Scales from 0 to N instances automatically |
| **Persistent Storage** | Volumes for models and outputs |

## 🚀 Quick Start

### 1. Install Modal
```bash
pip install modal
```

### 2. Authenticate
```bash
modal setup
```

### 3. Deploy
```bash
modal deploy modal_app.py
```

### 4. Use Your API
```bash
# Your endpoint will be shown after deployment
curl https://your-workspace--comfyui-fastapi-app.modal.run/system_stats
```

**That's it!** 🎉 You now have ComfyUI running on serverless GPU infrastructure.

## 📚 Documentation

### Getting Started
- **[MODAL_QUICKSTART.md](MODAL_QUICKSTART.md)** - 5-minute quick start guide
  - Minimal steps to get deployed
  - Common commands
  - Basic examples

### Comprehensive Guide
- **[MODAL_DEPLOYMENT_GUIDE.md](MODAL_DEPLOYMENT_GUIDE.md)** - Complete documentation
  - Prerequisites and setup
  - GPU selection and configuration
  - Model management
  - API usage examples
  - Cost optimization
  - Troubleshooting

### Summary & Overview
- **[MODAL_SUMMARY.md](MODAL_SUMMARY.md)** - Implementation overview
  - Architecture diagram
  - Feature list
  - Cost examples
  - Comparison with traditional hosting

## 🛠️ Files Included

### Core Deployment
- **`modal_app.py`** - Main Modal application
  - ASGI web server configuration
  - GPU settings
  - Volume mounts
  - Helper functions

### Helper Scripts
- **`deploy_to_modal.sh`** - Interactive deployment helper
  - Deploy, test, manage with one script
  - Model upload assistant
  - Log viewer

- **`modal_test.py`** - Testing and verification
  - API endpoint testing
  - Health checks
  - Workflow execution tests

### Configuration
- **`modal_requirements.txt`** - Local development dependencies

## 💰 Pricing Examples

Based on actual usage with A10G GPU ($1.10/hour):

| Use Case | Details | Cost per Image |
|----------|---------|----------------|
| Single image (cold start) | 30s startup + 15s generation | ~$0.014 |
| Single image (warm) | 15s generation only | ~$0.005 |
| Batch of 10 (warm) | 150s total | ~$0.046 total |
| Batch of 100 (warm) | 1500s total | ~$0.46 total |
| Idle time | No usage | $0.00 |

**Compare to dedicated server:**
- Dedicated A10G: ~$800/month (~$1.10/hr × 730hrs)
- Modal (10,000 images/month): ~$50/month
- **Savings: 94%** for typical usage

## 🎮 GPU Options

Choose your GPU in `modal_app.py`:

```python
# Budget (Testing, SD 1.5)
GPU_CONFIG = modal.gpu.T4()  # $0.60/hr, 16GB VRAM

# Recommended (SDXL Production)
GPU_CONFIG = modal.gpu.A10G()  # $1.10/hr, 24GB VRAM

# High Performance (Video, Large Models)
GPU_CONFIG = modal.gpu.A100()  # $4.00/hr, 40-80GB VRAM

# Multi-GPU (Very Large Models)
GPU_CONFIG = modal.gpu.A100(count=2)  # $8.00/hr, 160GB VRAM
```

## 📦 Model Management

### Upload Models to Volume

```bash
# Single model file
modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors

# Entire directory
modal volume put comfyui-models ./my_models /checkpoints

# LoRA models
modal volume put comfyui-models my_lora.safetensors /loras/my_lora.safetensors
```

### Download Models Automatically

1. Edit `modal_app.py` → `download_models()` function
2. Add your model URLs
3. Run:
```bash
modal run modal_app.py::download_models
```

### Browse Your Models

```bash
# List all volumes
modal volume list

# List checkpoints
modal volume ls comfyui-models /checkpoints

# List all model types
modal volume ls comfyui-models
```

## 🔌 API Usage

### REST API Endpoints

Your deployment provides all standard ComfyUI endpoints:

```bash
# System information
GET /system_stats

# Available nodes
GET /object_info

# Queue workflow
POST /prompt
{
  "prompt": { /* your workflow */ }
}

# Check queue
GET /queue

# Get history
GET /history

# Get specific result
GET /history/{prompt_id}

# View output
GET /view?filename={filename}
```

### Python Client Example

```python
import requests
import json

ENDPOINT = "https://your-workspace--comfyui-fastapi-app.modal.run"

# Load workflow (export from ComfyUI as API format)
with open("workflow.json") as f:
    workflow = json.load(f)

# Submit workflow
response = requests.post(
    f"{ENDPOINT}/prompt",
    json={"prompt": workflow}
)

result = response.json()
prompt_id = result["prompt_id"]

print(f"Queued: {prompt_id}")

# Poll for completion
import time
while True:
    status = requests.get(f"{ENDPOINT}/history/{prompt_id}").json()
    if prompt_id in status:
        if status[prompt_id].get("status", {}).get("completed"):
            print("Complete!")
            print(status[prompt_id]["outputs"])
            break
    time.sleep(2)
```

### Direct Function Calls

```python
import modal

# Look up the deployed function
f = modal.Function.lookup("comfyui", "generate_image")

# Call it directly
result = f.remote(workflow=workflow_dict)
```

## 🔧 Common Tasks

### Deploy or Update
```bash
modal deploy modal_app.py
```
*Zero-downtime deployment*

### View Logs
```bash
modal app logs comfyui --follow
```

### Check Status
```bash
modal app list
modal app show comfyui
```

### Interactive Shell
```bash
modal shell modal_app.py
```
*Debug inside the container*

### Stop Deployment
```bash
modal app stop comfyui
```
*⚠️ Irreversible - must redeploy to restart*

## 📊 Monitoring

### Modal Dashboard
- View at: https://modal.com/apps
- Real-time logs
- Usage metrics
- Cost tracking

### Command Line
```bash
# View all apps
modal app list

# View specific app details
modal app show comfyui

# View usage stats
modal app stats comfyui

# Monitor logs in real-time
modal app logs comfyui --follow
```

## 🎯 Use Cases

### Perfect For:
✅ Variable workload (not 24/7)  
✅ Burst processing  
✅ Multiple GPU types needed  
✅ Development and testing  
✅ Automatic scaling requirements  
✅ Pay-per-use cost model  

### Consider Alternatives For:
❌ Constant 24/7 high-volume usage  
❌ Sub-second latency requirements  
❌ Extremely large model files (>100GB)  
❌ Custom hardware requirements  

## 🚨 Troubleshooting

### Common Issues

**❓ "modal: command not found"**
```bash
pip install modal
# Or use: python -m modal setup
```

**❓ GPU out of memory**
```python
# Edit modal_app.py
GPU_CONFIG = modal.gpu.A100()  # Larger GPU
```

**❓ Models not found**
```bash
# Verify uploads
modal volume ls comfyui-models /checkpoints
```

**❓ Timeout errors**
```python
# Edit modal_app.py
TIMEOUT = 1800  # 30 minutes
```

**❓ Slow cold starts**
```python
# Edit modal_app.py
CONTAINER_IDLE_TIMEOUT = 600  # Keep warm longer
```

See [MODAL_DEPLOYMENT_GUIDE.md](MODAL_DEPLOYMENT_GUIDE.md) for comprehensive troubleshooting.

## 🔒 Security Considerations

- ✅ HTTPS by default
- ✅ Isolated containers per execution
- ✅ Volume encryption at rest
- ⚠️ API is public by default - add authentication for production
- ⚠️ Consider API keys for sensitive deployments

### Adding Basic Authentication

```python
# In modal_app.py, add to your function:
@app.function(
    secrets=[modal.Secret.from_name("api-key")]
)
```

Then check for API key in requests.

## 🎓 Learning Resources

- **Modal Documentation**: https://modal.com/docs
- **Modal Examples**: https://github.com/modal-labs/modal-examples
- **Modal Discord**: https://discord.gg/modal
- **ComfyUI Docs**: https://github.com/comfyanonymous/ComfyUI
- **ComfyUI Discord**: https://comfy.org/discord

## 🤝 Contributing

This Modal deployment setup is part of the ComfyUI project. Contributions welcome:

1. Fork the repository
2. Make your changes
3. Test with `modal run modal_app.py`
4. Submit a pull request

## 📝 License

This Modal deployment follows ComfyUI's GPL-3.0 license.

## 🙋 Support

### Modal Support
- **Discord**: https://discord.gg/modal
- **Email**: support@modal.com
- **Docs**: https://modal.com/docs

### ComfyUI Support
- **Discord**: https://comfy.org/discord
- **GitHub Issues**: https://github.com/comfyanonymous/ComfyUI/issues

## 🎬 Getting Started Checklist

- [ ] Install Modal: `pip install modal`
- [ ] Authenticate: `modal setup`
- [ ] Review GPU settings in `modal_app.py`
- [ ] Deploy: `modal deploy modal_app.py`
- [ ] Note your endpoint URL
- [ ] Upload models to volume
- [ ] Test with `modal_test.py`
- [ ] Try a workflow via API
- [ ] Monitor usage on dashboard
- [ ] Optimize settings for your use case

## 📞 Quick Reference

```bash
# Setup
pip install modal && modal setup

# Deploy
modal deploy modal_app.py

# Upload model
modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors

# View logs
modal app logs comfyui --follow

# Test
python modal_test.py https://your-endpoint.modal.run

# Interactive helper
./deploy_to_modal.sh
```

---

## 🌟 Next Steps

1. **Read the Quick Start**: [MODAL_QUICKSTART.md](MODAL_QUICKSTART.md)
2. **Deploy Your First Instance**: `modal deploy modal_app.py`
3. **Upload Your Models**: Use the volume commands above
4. **Test the API**: Use `modal_test.py` or curl
5. **Integrate**: Connect your application
6. **Optimize**: Adjust GPU and timeout settings
7. **Monitor**: Watch usage and costs
8. **Scale**: Let Modal handle the rest!

---

**Ready to get started?**

```bash
# One-command deployment
modal setup && modal deploy modal_app.py
```

🚀 **Welcome to serverless ComfyUI!**

