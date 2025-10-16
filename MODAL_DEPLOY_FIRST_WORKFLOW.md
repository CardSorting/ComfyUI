# Deploy First, Upload Models Later - Workflow Guide

## Quick Answer

✅ **YES!** You can absolutely deploy ComfyUI to Modal first and upload models later.

The deployment and model storage are **completely separate**:
- **Deployment** = Your ComfyUI application code
- **Models** = Stored in persistent volumes (separate from deployment)

## How It Works

### The Architecture

```
┌─────────────────────────────────────┐
│   ComfyUI Deployment (Code)         │  ← Deploy once
│   - Application logic               │
│   - API endpoints                   │
│   - GPU configuration               │
└──────────────┬──────────────────────┘
               │
               │ Mounts volume
               ▼
┌─────────────────────────────────────┐
│   Modal Volume (Storage)            │  ← Add models anytime
│   - comfyui-models                  │
│   - Persistent across deployments   │
│   - Add/remove files independently  │
└─────────────────────────────────────┘
```

### Key Points

1. **Volumes are Persistent**
   - Models live in a volume separate from your deployment
   - Volumes survive deployments, redeployments, and container restarts

2. **Models Are Immediately Available**
   - Upload a model → It's instantly accessible to your deployed ComfyUI
   - No need to redeploy or restart anything

3. **Independent Operations**
   - Deploy code changes → Models stay intact
   - Upload/delete models → Deployment keeps running
   - Update both → They work independently

## Recommended Workflow

### Phase 1: Deploy Empty (5 minutes)

```bash
# Step 1: Install and authenticate Modal
pip install modal
modal setup

# Step 2: Deploy ComfyUI (with empty volumes)
modal deploy modal_app.py
```

**Result:** You get a running ComfyUI API endpoint immediately!

```
✓ App deployed! 🎉
Web endpoint: https://your-workspace--comfyui-fastapi-app.modal.run
```

### Phase 2: Upload Models (as needed)

Now you can upload models at your leisure:

```bash
# Upload models one at a time
modal volume put comfyui-models ./my_model.safetensors /checkpoints/my_model.safetensors

# Upload entire directories
modal volume put comfyui-models ./my_models/checkpoints /checkpoints

# Upload different model types
modal volume put comfyui-models ./loras /loras
modal volume put comfyui-models ./vae /vae
```

**Result:** Models are immediately available in your deployed ComfyUI!

### Phase 3: Use and Iterate

```bash
# Test with uploaded models
python modal_test.py https://your-endpoint.modal.run

# Add more models anytime
modal volume put comfyui-models new_model.safetensors /checkpoints/new_model.safetensors

# No redeployment needed!
```

## Complete Step-by-Step Example

### 1. Deploy with No Models

```bash
# Deploy the app
cd /Users/bozoegg/ComfyUI
modal deploy modal_app.py
```

**Output:**
```
✓ Created objects.
├── 🔨 Created function fastapi_app.
├── 🔨 Created function download_models.
└── 🔨 Created function generate_image.
✓ App deployed! 🎉

Web endpoint: https://workspace--comfyui-fastapi-app.modal.run
```

Your ComfyUI is now live! But it has no models yet.

### 2. Test the Empty Deployment

```bash
# Check if it's running
curl https://workspace--comfyui-fastapi-app.modal.run/system_stats

# You'll see it's running, just no models available
curl https://workspace--comfyui-fastapi-app.modal.run/object_info
```

### 3. Upload Your First Model

```bash
# Upload SDXL checkpoint (example)
modal volume put comfyui-models \
  ~/Downloads/sd_xl_base_1.0.safetensors \
  /checkpoints/sd_xl_base_1.0.safetensors
```

**Output:**
```
Uploading sd_xl_base_1.0.safetensors: 100%|████| 6.46GB/6.46GB [03:15<00:00, 33.1MB/s]
✓ Upload complete
```

### 4. Verify Model is Available

```bash
# List models in volume
modal volume ls comfyui-models /checkpoints

# Or check via API
curl https://workspace--comfyui-fastapi-app.modal.run/object_info
```

The model is now immediately available! **No redeployment needed.**

### 5. Upload More Models Over Time

```bash
# Day 1: Upload checkpoint
modal volume put comfyui-models checkpoint.safetensors /checkpoints/checkpoint.safetensors

# Day 2: Upload VAE
modal volume put comfyui-models vae.safetensors /vae/vae.safetensors

# Week 1: Upload LoRAs
modal volume put comfyui-models ./loras /loras

# Month 1: Add more checkpoints
modal volume put comfyui-models new_model.safetensors /checkpoints/new_model.safetensors
```

Each upload is immediately available. Your deployment keeps running.

## What Happens Behind the Scenes

### When You Deploy

```python
# In modal_app.py
@app.function(
    image=image,
    gpu=GPU_CONFIG,
    volumes={
        "/models": models_volume,  # Mount the volume
        "/outputs": outputs_volume,
    },
)
```

The deployment:
1. ✅ Creates container image with ComfyUI code
2. ✅ Creates/references the `comfyui-models` volume
3. ✅ Mounts volume at `/models` inside containers
4. ✅ Starts serving API requests

### When You Upload Models

```bash
modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors
```

The upload:
1. ✅ Sends file to Modal's volume storage
2. ✅ File appears in the volume immediately
3. ✅ All running containers see the new file
4. ✅ ComfyUI can use it in the next workflow

**No restart or redeployment required!**

## Common Scenarios

### Scenario 1: Start Small, Grow Later

```bash
# Week 1: Deploy with one model
modal deploy modal_app.py
modal volume put comfyui-models sd15.safetensors /checkpoints/sd15.safetensors

# Week 2: Add SDXL
modal volume put comfyui-models sdxl.safetensors /checkpoints/sdxl.safetensors

# Week 3: Add LoRAs
modal volume put comfyui-models ./loras /loras

# Week 4: Add ControlNet
modal volume put comfyui-models ./controlnet /controlnet
```

✅ **Benefit:** Spread out uploads, test incrementally

### Scenario 2: Deploy for Testing, Models Later

```bash
# Morning: Deploy to test API
modal deploy modal_app.py
python modal_test.py https://your-endpoint.modal.run

# Afternoon: Upload models
modal volume put comfyui-models ./models /

# Evening: Test with real workflows
# Submit actual ComfyUI workflows
```

✅ **Benefit:** Verify deployment works before committing to large uploads

### Scenario 3: Different Models for Different Environments

```bash
# Production deployment
modal deploy modal_app.py --env production

# Upload production models
modal volume put comfyui-models prod_model.safetensors /checkpoints/prod.safetensors

# Staging deployment (same volume)
modal deploy modal_app.py --env staging

# Add experimental models
modal volume put comfyui-models experimental.safetensors /checkpoints/experimental.safetensors
```

✅ **Benefit:** Share models across environments, or use separate volumes

### Scenario 4: Update Models Without Downtime

```bash
# Your app is running with model_v1.safetensors

# Upload new version with different name
modal volume put comfyui-models model_v2.safetensors /checkpoints/model_v2.safetensors

# Test new version
# (update your workflow to use model_v2.safetensors)

# If good, you can optionally remove old version
modal volume rm comfyui-models /checkpoints/model_v1.safetensors
```

✅ **Benefit:** Zero downtime model updates

## Practical Advantages

### 1. Faster Initial Deployment
```
Deploy first (5 min) → App is live → Upload models in background (hours)
```

vs.

```
Wait for all models (hours) → Deploy → App is live
```

### 2. No Redeployment for Model Changes

**Traditional hosting:**
```
Add model → Restart server → Downtime → Available
```

**Modal:**
```
Add model → Immediately available
```

### 3. Cost Efficiency

**Option A: Deploy first**
- Deploy: 5 minutes → $0.01
- Upload models later: Takes time but doesn't consume compute

**Option B: Include models in image**
- Build time: 2 hours → $2.20 (charged for GPU time during build)
- Every deployment rebuild → Expensive

### 4. Flexibility

- ✅ Add models without code changes
- ✅ Remove models without code changes
- ✅ Update models without downtime
- ✅ Test with different model sets

## Important Notes

### The Volume is Created Automatically

```python
# In modal_app.py
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)
```

When you deploy, Modal creates the volume if it doesn't exist:
- Empty volume is created
- Mounted at `/models` in your containers
- Ready to receive files

### ComfyUI Handles Missing Models Gracefully

If you try to use a model that doesn't exist:
- ComfyUI returns an error message
- The API stays running
- You can upload the model and try again

### Volumes Persist Across Everything

Your models stay safe through:
- ✅ Deployments and redeployments
- ✅ Container restarts
- ✅ App stops and starts
- ✅ Code updates
- ✅ GPU type changes

**Only way to lose data:** Explicitly delete the volume or files

## Quick Reference Commands

### Check What's in Your Volume (Before/After Upload)

```bash
# List all volumes
modal volume list

# Check if comfyui-models exists
modal volume ls comfyui-models

# List contents
modal volume ls comfyui-models /checkpoints
modal volume ls comfyui-models /loras
```

### Upload Models to Deployed App

```bash
# Single file
modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors

# Directory
modal volume put comfyui-models ./my_models/checkpoints /checkpoints

# With wildcard (upload all .safetensors files)
for file in *.safetensors; do
  modal volume put comfyui-models "$file" "/checkpoints/$file"
done
```

### Check if Model is Available in ComfyUI

```bash
# Via Modal CLI
modal volume ls comfyui-models /checkpoints

# Via ComfyUI API (if you know the model name)
curl https://your-endpoint.modal.run/object_info
```

### Test After Uploading Models

```bash
# Run test script
python modal_test.py https://your-endpoint.modal.run

# Or test with a workflow
curl -X POST https://your-endpoint.modal.run/prompt \
  -H "Content-Type: application/json" \
  -d @workflow.json
```

## Step-by-Step First Time Setup

### Complete Walkthrough

```bash
# ===== PHASE 1: DEPLOY (5 minutes) =====

# 1. Install Modal
pip install modal

# 2. Authenticate
modal setup

# 3. Deploy ComfyUI
cd /Users/bozoegg/ComfyUI
modal deploy modal_app.py

# 4. Save your endpoint URL
# Output shows: https://workspace--comfyui-fastapi-app.modal.run
# Save this URL!

# 5. Verify it's running
curl https://your-endpoint.modal.run/system_stats

# ===== PHASE 2: UPLOAD MODELS (as needed) =====

# 6. Create directories (optional, for organization)
modal run modal_app.py::download_models

# 7. Upload your first model
modal volume put comfyui-models \
  ~/path/to/sd_xl_base_1.0.safetensors \
  /checkpoints/sd_xl_base_1.0.safetensors

# 8. Verify upload
modal volume ls comfyui-models /checkpoints

# 9. Test with the model
python modal_test.py https://your-endpoint.modal.run

# ===== PHASE 3: ADD MORE MODELS =====

# 10. Upload VAE
modal volume put comfyui-models vae.safetensors /vae/vae.safetensors

# 11. Upload LoRAs
modal volume put comfyui-models ./loras /loras

# 12. Upload ControlNet
modal volume put comfyui-models controlnet.pth /controlnet/controlnet.pth

# Done! All models are immediately available.
```

## Troubleshooting

### Q: I deployed but ComfyUI says "no models found"

**A:** That's expected! Upload models:

```bash
modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors
```

### Q: I uploaded a model but ComfyUI doesn't see it

**A:** Check a few things:

```bash
# 1. Verify file is in volume
modal volume ls comfyui-models /checkpoints

# 2. Check filename matches exactly (case-sensitive)
modal volume ls comfyui-models /checkpoints -l

# 3. Verify volume is mounted
# Check modal_app.py has:
# volumes={"/models": models_volume}
```

### Q: Do I need to redeploy after uploading models?

**A:** No! Models are immediately available. Just use them in your workflows.

### Q: Can I upload models while ComfyUI is processing a job?

**A:** Yes! Uploads don't affect running jobs. New models will be available for the next job.

### Q: What happens if I delete a model that's being used?

**A:** The current job will fail, but the API stays running. Upload the model again and retry.

### Q: Can I upload models from within ComfyUI?

**A:** Not directly. Use the Modal CLI or the `download_models()` function to add models. ComfyUI's UI is not deployed in headless mode.

## Best Practices

### ✅ DO:

1. **Deploy first, test the API works**
2. **Upload models incrementally** (test as you go)
3. **Keep frequently-used models in the volume**
4. **Use descriptive filenames** (e.g., `sdxl_base_1.0_fp16.safetensors`)
5. **Document what you upload** (keep a list)
6. **Test each model after uploading**

### ❌ DON'T:

1. **Don't wait to upload everything before deploying**
2. **Don't redeploy just to add models** (not necessary)
3. **Don't upload to random paths** (follow the structure in MODAL_MODEL_MANAGEMENT.md)
4. **Don't delete models without verifying** (they're immediately gone)
5. **Don't upload huge batches without testing first** (test one, then upload more)

## Cost Implications

### Deploy First Strategy

```
Day 1: Deploy (5 min compute) → $0.01
Day 1: Upload 50GB models (no compute cost) → $0
Day 1: Storage (50GB × 1 day) → $0.16

Total: $0.17
```

### Wait and Upload First Strategy

```
Day 1: Local testing → $0
Day 1: Upload 50GB models → $0
Day 1: Deploy → $0.01
Day 1: Storage (50GB × 1 day) → $0.16

Total: $0.17
```

**Same cost**, but deploy-first means your API is live sooner!

## Summary

### The Key Insight

```
Deployment ≠ Models

Your ComfyUI deployment (code) is separate from your models (data).

Deploy code once → Add/remove models anytime → No redeployment needed
```

### Recommended Workflow

1. ✅ **Deploy ComfyUI** (5 minutes)
   - Get your API endpoint
   - Verify it works

2. ✅ **Upload models incrementally**
   - Start with one model
   - Test it works
   - Add more as needed

3. ✅ **Iterate freely**
   - Add models: No downtime
   - Remove models: No downtime
   - Update models: No downtime
   - Update code: Redeploy (but models stay)

### Benefits

- ⚡ **Faster time to live**
- 💰 **No extra cost**
- 🔄 **More flexibility**
- 🛡️ **No downtime for model changes**
- 🧪 **Easier testing**

## Next Steps

1. **Deploy now**: `modal deploy modal_app.py`
2. **Get your endpoint URL**: Save it!
3. **Test the API**: `python modal_test.py <endpoint>`
4. **Upload first model**: `modal volume put ...`
5. **Test with model**: Submit a workflow
6. **Repeat**: Add more models over time

---

**Ready to deploy?**

```bash
modal deploy modal_app.py
```

Your ComfyUI will be live in 5 minutes. Upload models whenever you're ready! 🚀

For more details on model management, see:
- [MODAL_MODEL_MANAGEMENT.md](MODAL_MODEL_MANAGEMENT.md) - Complete model storage guide
- [MODAL_QUICKSTART.md](MODAL_QUICKSTART.md) - Quick start guide
- [MODAL_DEPLOYMENT_GUIDE.md](MODAL_DEPLOYMENT_GUIDE.md) - Full deployment documentation

