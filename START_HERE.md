# 🚀 START HERE - Super Simple Guide

**New to Modal? Confused by the docs? Start here!**

This is the simplest possible way to get ComfyUI running on Modal.com.

---

## Option 1: Use the Wizard (EASIEST) ⭐

Just run this one command and answer the questions:

```bash
python modal_setup_wizard.py
```

**That's it!** The wizard will:
- Install Modal CLI
- Log you into Modal
- Let you choose a GPU
- Deploy ComfyUI
- Optionally download models for you

**Time: 10-15 minutes** (mostly waiting for downloads)

---

## Option 2: Manual Steps (5 Commands)

If you prefer doing it yourself:

### 1. Install Modal
```bash
pip install modal
```

### 2. Login to Modal
```bash
modal setup
```
(This opens your browser - create a free account)

### 3. Deploy ComfyUI
```bash
modal deploy modal_app.py
```
(Wait 5 minutes - you'll get an HTTPS endpoint URL)

### 4. Check What You Have
```bash
modal volume ls comfyui-models
```
(Empty at first - that's okay!)

### 5. Add Models (Optional)
```bash
# Edit modal_app.py and add model URLs in the download_models() function
# Then run:
modal run modal_app.py::download_models
```

**Done!** Your ComfyUI is live.

---

## What You Get

- ✅ ComfyUI running in the cloud
- ✅ HTTPS API endpoint (e.g., `https://your-workspace--comfyui-fastapi-app.modal.run`)
- ✅ GPU access (T4/A10G/A100)
- ✅ Auto-scaling (handles 1 request or 1000 requests automatically)
- ✅ Pay only for what you use ($0 when idle!)

---

## How to Use It

### Method 1: Via API

Send ComfyUI workflows to your endpoint:

```bash
curl -X POST https://your-endpoint.modal.run/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": your_workflow_json}'
```

### Method 2: Via Python

```python
import requests

response = requests.post(
    "https://your-endpoint.modal.run/prompt",
    json={"prompt": your_workflow}
)

print(response.json())
```

---

## Common Questions

### "Where do I get my endpoint URL?"

After running `modal deploy modal_app.py`, it shows:
```
Web endpoint: https://workspace--comfyui-fastapi-app.modal.run
```
That's your URL!

### "How do I add models?"

**Easy way:** Run the wizard: `python modal_setup_wizard.py` (choose option to download models)

**Manual way:**
1. Edit `modal_app.py`
2. Find `download_models()` function
3. Add model URLs
4. Run: `modal run modal_app.py::download_models`

See `MODAL_DOWNLOAD_MODELS_FROM_URL.md` for details.

### "Do I need models on my computer?"

**No!** Modal downloads them directly from the internet (Hugging Face, Civitai, etc.)

### "How much does it cost?"

- **A10G GPU**: ~$1.10/hour (recommended)
- **T4 GPU**: ~$0.60/hour (testing)
- **A100 GPU**: ~$4/hour (large models)

**But you only pay when it's running!**
- Idle = $0
- Generating one image = ~$0.005
- 1000 images/month = ~$5

### "Can I see my models?"

```bash
modal volume ls comfyui-models /checkpoints
modal volume ls comfyui-models /loras
modal volume ls comfyui-models /vae
```

### "How do I stop it?"

```bash
modal app stop comfyui
```

(But it's free when idle, so you might not need to!)

### "How do I update it?"

```bash
modal deploy modal_app.py
```

Zero-downtime update!

### "Where are the logs?"

```bash
modal app logs comfyui --follow
```

---

## Quick Reference Card

```bash
# Deploy
modal deploy modal_app.py

# Download models
modal run modal_app.py::download_models

# Check models
modal volume ls comfyui-models /checkpoints

# View logs
modal app logs comfyui --follow

# Test endpoint
curl https://your-endpoint.modal.run/system_stats

# Stop (optional)
modal app stop comfyui
```

---

## Getting Help

### Run the Wizard
```bash
python modal_setup_wizard.py
```

### Check the Docs
- **Quick Start**: `MODAL_QUICKSTART.md` - 5-minute guide
- **Full Guide**: `MODAL_DEPLOYMENT_GUIDE.md` - Everything
- **Models**: `MODAL_DOWNLOAD_MODELS_FROM_URL.md` - Model management

### Ask for Help
- **Modal Discord**: https://discord.gg/modal
- **Modal Docs**: https://modal.com/docs

---

## Troubleshooting

### "modal: command not found"
```bash
pip install modal
```

### "Not authenticated"
```bash
modal setup
```

### "GPU out of memory"
Edit `modal_app.py` and change:
```python
GPU_CONFIG = modal.gpu.A100()  # Use bigger GPU
```

### "Models not found"
```bash
# Check if they're uploaded:
modal volume ls comfyui-models /checkpoints

# If empty, download them:
modal run modal_app.py::download_models
```

### "Deployment failed"
```bash
# Check logs:
modal app logs comfyui

# Try redeploying:
modal deploy modal_app.py
```

---

## That's It!

Seriously, that's all you need to know to get started.

**Recommended first step:** Run the wizard!

```bash
python modal_setup_wizard.py
```

It will walk you through everything step by step.

Good luck! 🚀

---

## What's Next?

Once you have it running:

1. **Test it**: Send a ComfyUI workflow to your endpoint
2. **Add more models**: Download more checkpoints, LoRAs, etc.
3. **Customize**: Edit `modal_app.py` to change GPU, timeout, etc.
4. **Integrate**: Connect your app/website to the API
5. **Scale**: Modal handles everything automatically!

---

**Still confused?** Run: `python modal_setup_wizard.py`

**Have questions?** Check: `MODAL_QUICKSTART.md`

**Want details?** Read: `MODAL_DEPLOYMENT_GUIDE.md`

