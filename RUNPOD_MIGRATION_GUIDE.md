# RunPod Migration Guide - From Modal to RunPod

## Why RunPod?
- ⚡ **200ms-12s cold starts** vs Modal's 30s-2min
- 💰 **40-60% cost savings** for typical workloads
- 🎯 **Native ComfyUI support** with serverless endpoints
- 📈 **Auto-scaling** from 0 to 100+ concurrent requests

---

## Quick Start (20 Minutes)

### Step 1: Sign Up for RunPod
1. Go to https://www.runpod.io
2. Create an account
3. Add billing information (pay-as-you-go)
4. Get your API key from dashboard

### Step 2: Install RunPod CLI
```bash
pip install runpod
```

### Step 3: Create RunPod Handler

Create a file `runpod_handler.py` in your project root:

```python
import runpod
import json
import torch
import sys
import os

# Add ComfyUI to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import ComfyUI modules
import execution
import server
from nodes import NODE_CLASS_MAPPINGS
import folder_paths


def load_workflow(workflow_json):
    """Load and validate a ComfyUI workflow"""
    if isinstance(workflow_json, str):
        workflow = json.loads(workflow_json)
    else:
        workflow = workflow_json
    return workflow


def execute_workflow(workflow, client_id="runpod"):
    """Execute a ComfyUI workflow and return results"""
    from execution import PromptExecutor, validate_prompt
    
    # Validate the workflow
    valid = validate_prompt(workflow)
    if not valid[0]:
        return {"error": f"Invalid workflow: {valid[1]}"}
    
    # Create prompt executor
    executor = PromptExecutor(server.PromptServer.instance)
    
    # Execute the workflow
    try:
        output_images = []
        
        # Execute the prompt
        executor.execute(workflow, client_id)
        
        # Get the output files from the output directory
        output_dir = folder_paths.get_output_directory()
        
        # Return paths to generated images
        return {
            "status": "success",
            "output_dir": output_dir,
            "message": "Workflow executed successfully"
        }
        
    except Exception as e:
        return {"error": str(e)}


def handler(event):
    """
    RunPod handler function
    
    Expected input format:
    {
        "input": {
            "workflow": {...},  # ComfyUI workflow JSON
            "return_images": true  # Optional: return base64 images
        }
    }
    """
    try:
        input_data = event.get("input", {})
        workflow = input_data.get("workflow")
        
        if not workflow:
            return {"error": "No workflow provided"}
        
        # Execute the workflow
        result = execute_workflow(workflow)
        
        return result
        
    except Exception as e:
        return {"error": f"Handler error: {str(e)}"}


if __name__ == "__main__":
    # Start the RunPod serverless handler
    runpod.serverless.start({"handler": handler})
```

### Step 4: Create Dockerfile for RunPod

Create `Dockerfile.runpod`:

```dockerfile
# Use NVIDIA CUDA base image
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install RunPod SDK
RUN pip3 install runpod

# Copy ComfyUI files
COPY . /app/

# Copy the RunPod handler
COPY runpod_handler.py /app/

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# RunPod will call this handler
CMD ["python3", "runpod_handler.py"]
```

### Step 5: Create RunPod Configuration

Create `runpod_config.json`:

```json
{
  "name": "comfyui-serverless",
  "container": {
    "image": "YOUR_DOCKER_HUB_USERNAME/comfyui-runpod:latest",
    "gpu_count": 1
  },
  "machine_type": "NVIDIA A100",
  "scaler": {
    "min_workers": 0,
    "max_workers": 3,
    "idle_timeout": 60
  },
  "environment": {
    "CUDA_VISIBLE_DEVICES": "0"
  }
}
```

### Step 6: Build and Push Docker Image

```bash
# Build the image
docker build -f Dockerfile.runpod -t YOUR_DOCKER_HUB_USERNAME/comfyui-runpod:latest .

# Login to Docker Hub
docker login

# Push the image
docker push YOUR_DOCKER_HUB_USERNAME/comfyui-runpod:latest
```

### Step 7: Deploy to RunPod

```bash
# Using RunPod CLI
runpod create endpoint \
  --name comfyui-api \
  --image YOUR_DOCKER_HUB_USERNAME/comfyui-runpod:latest \
  --gpu-type "NVIDIA A100" \
  --min-workers 0 \
  --max-workers 3 \
  --idle-timeout 60
```

Or deploy via RunPod Web UI:
1. Go to RunPod dashboard
2. Click "Serverless" → "Create Endpoint"
3. Enter your Docker image
4. Select GPU type (A100, RTX 4090, etc.)
5. Configure scaling settings
6. Deploy

### Step 8: Test Your Endpoint

Create `test_runpod.py`:

```python
import requests
import json

# Your RunPod endpoint URL
ENDPOINT_URL = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run"
API_KEY = "your-runpod-api-key"

# Load a test workflow
with open("test_workflow_sdxl_turbo.json", "r") as f:
    workflow = json.load(f)

# Make request to RunPod
response = requests.post(
    ENDPOINT_URL,
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "input": {
            "workflow": workflow
        }
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Check job status
if response.status_code == 200:
    job_data = response.json()
    job_id = job_data.get("id")
    
    # Poll for results
    status_url = f"https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/{job_id}"
    
    import time
    while True:
        status_response = requests.get(
            status_url,
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        status_data = status_response.json()
        
        if status_data.get("status") == "COMPLETED":
            print("Job completed!")
            print(status_data.get("output"))
            break
        elif status_data.get("status") == "FAILED":
            print("Job failed!")
            print(status_data.get("error"))
            break
        
        print(f"Status: {status_data.get('status')}")
        time.sleep(2)
```

Run the test:
```bash
python test_runpod.py
```

---

## Advanced Configuration

### Using RunPod Network Volumes for Models

Instead of bundling models in the Docker image, use RunPod Network Volumes:

1. **Create a Network Volume:**
```bash
runpod create volume --name comfyui-models --size 50GB
```

2. **Upload models to the volume:**
```bash
# Mount volume to a pod
runpod create pod \
  --name model-uploader \
  --volume comfyui-models:/models \
  --gpu-type "NVIDIA RTX 3090"

# SSH into pod and upload models
# Or use RunPod's file manager
```

3. **Update Dockerfile to use volume:**
```dockerfile
# In your handler, mount the volume
ENV COMFYUI_MODELS_DIR=/runpod-volume/models
```

4. **Update deployment:**
```bash
runpod create endpoint \
  --name comfyui-api \
  --image YOUR_DOCKER_HUB_USERNAME/comfyui-runpod:latest \
  --volume comfyui-models:/runpod-volume \
  --gpu-type "NVIDIA A100"
```

### Optimizing Cold Start Times

1. **Minimize Docker Image Size:**
```dockerfile
# Use multi-stage build
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 as base
# ... install dependencies

FROM base as final
# Copy only necessary files
COPY --from=base /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
```

2. **Pre-load Models in Handler:**
```python
import runpod

# Global model loading (done once per container)
print("Loading models...")
# Your model loading code here
print("Models loaded!")

def handler(event):
    # Models are already loaded
    # Process request
    pass

runpod.serverless.start({"handler": handler})
```

3. **Use Template Containers:**
RunPod supports template containers that stay warm:
```bash
runpod create endpoint \
  --min-workers 1  # Keep 1 container always warm
```

---

## Cost Optimization

### GPU Selection Guide

| GPU | Best For | Price/hr | Cold Start |
|-----|----------|----------|------------|
| RTX 3090 | Testing, SD 1.5 | ~$0.35 | 200ms |
| RTX 4090 | SDXL, fast inference | ~$0.50 | 200ms |
| A100 40GB | Large models | ~$1.50 | 5-10s |
| A100 80GB | Very large models | ~$2.18 | 5-10s |
| H100 | Highest performance | ~$4.00 | 5-10s |

### Scaling Strategy

```python
# For low traffic (< 100 req/day)
min_workers = 0
max_workers = 1
idle_timeout = 60

# For medium traffic (100-1000 req/day)
min_workers = 1  # Keep one warm
max_workers = 3
idle_timeout = 300

# For high traffic (> 1000 req/day)
min_workers = 2  # Always ready
max_workers = 10
idle_timeout = 600
```

---

## Monitoring and Logging

### View Logs
```bash
# Via CLI
runpod logs YOUR_ENDPOINT_ID

# Via API
curl https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/logs \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Monitoring Dashboard
- Access RunPod dashboard: https://www.runpod.io/console
- View metrics: requests/sec, cold starts, execution time
- Set up alerts for failures

---

## Comparison: Modal vs RunPod

### File Structure Comparison

**Modal (Current):**
```
modal/
├── apps/
│   └── modal_app_fastapi.py
├── scripts/
│   └── modal_model_manager.sh
└── docs/
```

**RunPod (New):**
```
runpod/
├── runpod_handler.py          # Main handler
├── Dockerfile.runpod          # Container definition
├── runpod_config.json         # Configuration
└── tests/
    └── test_runpod.py         # Testing script
```

### Code Migration Map

| Modal Concept | RunPod Equivalent |
|---------------|-------------------|
| `@app.function()` | `def handler(event)` |
| `modal.Image` | `Dockerfile` |
| `modal.Volume` | Network Volume |
| `modal deploy` | `runpod create endpoint` |
| `modal app logs` | `runpod logs` |

---

## Migration Checklist

- [ ] Sign up for RunPod account
- [ ] Install RunPod CLI
- [ ] Create `runpod_handler.py`
- [ ] Create `Dockerfile.runpod`
- [ ] Build Docker image locally
- [ ] Test Docker image locally
- [ ] Push to Docker Hub
- [ ] Create RunPod endpoint
- [ ] Test with sample workflow
- [ ] Measure cold start times
- [ ] Compare costs with Modal
- [ ] Update production endpoints
- [ ] Monitor for 1 week
- [ ] Full migration decision

---

## Troubleshooting

### Issue: Cold starts still slow
**Solution:** 
- Set `min_workers=1` to keep one container warm
- Optimize Docker image size
- Pre-load models in global scope

### Issue: Out of memory
**Solution:**
- Use larger GPU (A100 80GB instead of 40GB)
- Optimize model loading
- Clear CUDA cache between requests

### Issue: Models not loading
**Solution:**
- Check volume mounting
- Verify model paths in workflow
- Check folder_paths configuration

---

## Support Resources

- **RunPod Documentation:** https://docs.runpod.io
- **RunPod Discord:** https://discord.gg/runpod
- **ComfyUI on RunPod Guide:** https://apatero.com/blog/turn-comfyui-into-production-api-runpod-20-minutes-2025/
- **RunPod Blog:** https://www.runpod.io/blog

---

## Next Steps After Migration

1. **Set up monitoring** - Track cold starts and costs
2. **Optimize workflows** - Reduce execution time
3. **Scale as needed** - Adjust min/max workers
4. **Add custom nodes** - Deploy your custom ComfyUI nodes
5. **Implement caching** - Cache frequently used models

---

**Estimated Migration Time:** 2-4 hours for full production deployment
**Expected Cost Savings:** 40-60% compared to Modal
**Expected Cold Start Improvement:** 5-30x faster (200ms vs 30-60s)

