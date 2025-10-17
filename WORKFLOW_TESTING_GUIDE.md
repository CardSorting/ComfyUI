# ComfyUI Workflow Testing Guide

Complete guide for running workflows on your Modal ComfyUI deployment.

## 🎉 Your First Successful Workflow!

You've already generated your first image using SDXL Turbo! The image was:
- **File**: `ComfyUI_00001_.png` (372 KB, 512x512)
- **Prompt**: "a beautiful sunset over mountains, vibrant colors, professional photography"
- **Model**: SDXL Turbo
- **Time**: ~15 seconds

---

## 🚀 Quick Start

### Option 1: Use the Helper Script (Easiest)

```bash
# Run the included test workflow
./run_workflow.sh test_workflow_sdxl_turbo.json

# This will:
# 1. Submit the workflow
# 2. Monitor execution
# 3. Download the generated image automatically
```

### Option 2: Manual Steps

```bash
# 1. Submit workflow
python test_workflow_simple.py

# 2. List outputs
curl https://cardsorting--comfyui-api-web.modal.run/outputs

# 3. Download image
curl https://cardsorting--comfyui-api-web.modal.run/outputs/ComfyUI_00001_.png -o image.png
```

---

## 📋 Available Workflows

### 1. SDXL Turbo Text-to-Image
**File**: `test_workflow_sdxl_turbo.json`

Simple text-to-image generation using SDXL Turbo:
- Fast (4 steps, ~15 seconds)
- 512x512 resolution
- Good quality for testing

```bash
./run_workflow.sh test_workflow_sdxl_turbo.json
```

### 2. Create Your Own Workflow

1. **In ComfyUI Desktop**: 
   - Create your workflow
   - Click "Save (API Format)"
   - Save as JSON

2. **Test on Modal**:
   ```bash
   ./run_workflow.sh your_workflow.json
   ```

---

## 🔧 API Endpoints

Your Modal ComfyUI has these endpoints:

### Submit Workflow
```bash
curl -X POST https://YOUR-ENDPOINT/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": {...workflow...}}'
```

### Check Queue
```bash
curl https://YOUR-ENDPOINT/queue
```

### Check History
```bash
curl https://YOUR-ENDPOINT/history/{prompt_id}
```

### List Outputs
```bash
curl https://YOUR-ENDPOINT/outputs
```

### Download Image
```bash
curl https://YOUR-ENDPOINT/outputs/filename.png -o image.png
```

---

## 💡 Tips for Workflows

### 1. **Adjust Image Size**

In your workflow JSON, change the EmptyLatentImage node:
```json
"5": {
  "inputs": {
    "width": 1024,    # Change width
    "height": 1024,   # Change height
    "batch_size": 1
  },
  "class_type": "EmptyLatentImage"
}
```

### 2. **Change the Prompt**

Update the CLIPTextEncode nodes:
```json
"6": {
  "inputs": {
    "text": "YOUR POSITIVE PROMPT HERE",
    "clip": ["4", 1]
  },
  "class_type": "CLIPTextEncode"
}
```

### 3. **SDXL Turbo Settings**

For SDXL Turbo, use:
- **Steps**: 1-4 (it's designed for few steps)
- **CFG**: 1.0 (don't change this)
- **Sampler**: euler or euler_ancestral
- **Scheduler**: normal

### 4. **Generate Multiple Images**

Change the seed in the KSampler node:
```json
"3": {
  "inputs": {
    "seed": 12345,  # Change this for different results
    ...
  }
}
```

---

## 🐛 Troubleshooting

### Workflow fails validation
```bash
# Check available nodes
curl https://YOUR-ENDPOINT/object_info | python -m json.tool | grep -i loader

# Check available models
./modal_manage.sh list
```

### Image doesn't appear
```bash
# List all outputs
curl https://YOUR-ENDPOINT/outputs

# Check history for errors
curl https://YOUR-ENDPOINT/history/PROMPT_ID | python -m json.tool
```

### Container is cold/slow
- First request after idle takes 30-60 seconds (loading model)
- Subsequent requests are much faster
- Container stays warm for 5 minutes (SCALEDOWN_WINDOW)

---

## 📊 Performance

**SDXL Turbo** (your current model):
- First run (cold): ~60s (includes model loading)
- Warm container: ~10-20s per image
- Steps: 1-4 (fast!)
- Quality: Good

**Expected Times**:
- SD 1.5: ~5-15 seconds (20-50 steps)
- SDXL Base: ~30-60 seconds (20-40 steps)
- SDXL Turbo: ~10-20 seconds (1-4 steps) ✅

---

## 🎨 Example Prompts

Try different prompts by editing the workflow JSON:

### Realistic Photo
```
"a professional photograph of a mountain landscape at sunset, golden hour lighting, highly detailed, 8k"
```

### Artistic Style
```
"oil painting of a serene lake, impressionist style, vibrant colors, masterpiece"
```

### Character
```
"portrait of a friendly robot, cute, pixar style, colorful, high quality"
```

### Abstract
```
"abstract geometric patterns, colorful, symmetrical, digital art"
```

---

## 📚 Next Steps

### Add More Models
```bash
# Download SD 1.5 (smaller, faster)
./modal_manage.sh download-url \
  "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  checkpoints

# Download a VAE (improves quality)
./modal_manage.sh download-url \
  "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
  vae
```

### Create Complex Workflows
- Add LoRAs for style
- Use ControlNet for guided generation
- Add upscaling nodes
- Chain multiple generations

### Integrate with Your App
```python
import requests

response = requests.post(
    "https://YOUR-ENDPOINT/prompt",
    json={"prompt": workflow_dict}
)

prompt_id = response.json()["prompt_id"]

# Wait for completion...
history = requests.get(f"https://YOUR-ENDPOINT/history/{prompt_id}").json()

# Download image...
image_url = f"https://YOUR-ENDPOINT/outputs/{filename}"
```

---

## ✅ Current Status

- ✅ ComfyUI deployed and working
- ✅ SDXL Turbo model installed (6.46 GB)
- ✅ 495 nodes loaded
- ✅ Workflow execution working  
- ✅ Image generation successful
- ✅ Image download working

**You're ready to build with ComfyUI on Modal!** 🚀

