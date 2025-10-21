# RunPod Serverless Deployment for ComfyUI

This directory contains everything needed to deploy ComfyUI as a RunPod Serverless endpoint.

## Quick Start

### Prerequisites

1. **Docker Hub account**: https://hub.docker.com (free)
2. **RunPod account**: https://www.runpod.io (pay-as-you-go)
3. **Docker installed locally**: https://docs.docker.com/get-docker/

### Step 1: Build and Push Docker Image

```bash
# Set your Docker Hub username
export DOCKER_USERNAME=your_dockerhub_username

# Make the deploy script executable
chmod +x runpod/deploy.sh

# Run the deployment script
./runpod/deploy.sh
```

This will:
- Build the Docker image (~10-15 minutes)
- Push to Docker Hub
- Display next steps

### Step 2: Deploy to RunPod

1. Go to RunPod Console: https://www.runpod.io/console/serverless

2. Click "New Endpoint"

3. Configure:
   - **Name**: `comfyui-api`
   - **Docker Image**: `your_dockerhub_username/comfyui-runpod:latest`
   - **GPU Type**: 
     - RTX 4090 (recommended for SDXL)
     - RTX 3090 (budget option)
     - A100 (for large models)
   - **Min Workers**: 0 (auto-scaling from zero)
   - **Max Workers**: 3 (adjust based on your needs)
   - **Idle Timeout**: 60 seconds
   - **Container Disk**: 20 GB

4. Click "Deploy"

5. Wait for deployment (~2-5 minutes)

6. Copy your **Endpoint ID** and **API Key**

### Step 3: Test Your Deployment

```bash
# Test with the included test script
python runpod/test_runpod.py YOUR_ENDPOINT_ID YOUR_API_KEY

# Or with a custom workflow
python runpod/test_runpod.py YOUR_ENDPOINT_ID YOUR_API_KEY path/to/workflow.json
```

## Files in This Directory

- `runpod_handler.py` - Main handler that processes workflow requests
- `Dockerfile` - Docker image definition
- `requirements-runpod.txt` - Python dependencies (includes RunPod SDK)
- `deploy.sh` - Automated build and deploy script
- `test_runpod.py` - Test script to verify deployment
- `README.md` - This file

## Usage

### Basic API Call

```python
import requests
import json

endpoint_id = "your_endpoint_id"
api_key = "your_api_key"

# Your ComfyUI workflow
workflow = {
    # ... your workflow nodes
}

# Submit job
response = requests.post(
    f"https://api.runpod.ai/v2/{endpoint_id}/run",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "input": {
            "workflow": workflow,
            "return_images": True
        }
    }
)

job_id = response.json()["id"]

# Check status
status_response = requests.get(
    f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}",
    headers={"Authorization": f"Bearer {api_key}"}
)

result = status_response.json()
```

### Input Parameters

The handler accepts the following input:

```json
{
  "input": {
    "workflow": {...},        // Required: ComfyUI workflow JSON
    "return_images": true,    // Optional: Return base64 images (default: true)
    "client_id": "optional"   // Optional: Client ID for tracking
  }
}
```

### Output Format

Successful response:

```json
{
  "status": "success",
  "outputs": [
    {
      "filename": "output_001.png",
      "data": "base64_encoded_image_data",
      "type": "image"
    }
  ],
  "output_files": ["output_001.png"],
  "execution_time": 12.34,
  "client_id": "..."
}
```

Error response:

```json
{
  "status": "error",
  "error": "Error message",
  "trace": "Stack trace..."
}
```

## Adding Models

### Option 1: Bake Models into Docker Image

Edit `Dockerfile` to download models during build:

```dockerfile
# Add before CMD
RUN cd /app/models/checkpoints && \
    wget https://huggingface.co/.../model.safetensors
```

Rebuild and redeploy.

### Option 2: Use RunPod Network Volumes

1. Create a Network Volume in RunPod console
2. Upload models to the volume
3. Attach volume to your endpoint at `/app/models`

This is better for large model collections and allows sharing models across endpoints.

## Pricing Estimate

Based on RTX 4090 @ $0.50/hr:

| Requests/Day | Avg Time | Monthly Cost |
|-------------|----------|--------------|
| 100 | 35s | $14.58 |
| 500 | 35s | $72.92 |
| 1000 | 35s | $145.83 |
| 5000 | 35s | $729.17 |

**Savings vs Modal:** ~52%

## Monitoring

View logs in RunPod console:
1. Go to your endpoint
2. Click "Logs" tab
3. View real-time execution logs

## Troubleshooting

### Build fails

```bash
# Check Docker is running
docker ps

# Try building manually
docker build -f runpod/Dockerfile -t test .
```

### Deployment stuck

- Check Docker image exists on Docker Hub
- Verify image name is correct
- Check RunPod status page

### Job fails immediately

- Check logs in RunPod console
- Verify workflow is valid
- Test locally first with `test_runpod.py`

### Slow cold starts

- Pre-download models in Dockerfile
- Increase container disk size
- Use Network Volumes for models

## Advanced Configuration

### Custom GPU Selection

Edit your endpoint settings to choose specific GPUs:
- RTX 3090: Cheapest, good for SD 1.5
- RTX 4090: Best value for SDXL
- A100: Best for large models

### Scaling Settings

Adjust based on your traffic:
```
Low traffic (< 500 req/day):
  min_workers: 0
  max_workers: 1
  
Medium traffic (500-2000 req/day):
  min_workers: 1
  max_workers: 3
  
High traffic (> 2000 req/day):
  min_workers: 2
  max_workers: 5-10
```

### Environment Variables

Set in RunPod endpoint configuration:
```
COMFYUI_HEADLESS=1
DISABLE_PROGRESS_BARS=1
```

## Next Steps

1. **Test with your workflows**: Use real workflows from your application
2. **Add models**: Include the models you need
3. **Monitor costs**: Track usage in RunPod dashboard
4. **Optimize**: Adjust workers and timeouts based on usage
5. **Integrate**: Connect your application to the endpoint

## Support

- RunPod Docs: https://docs.runpod.io
- RunPod Discord: https://discord.gg/runpod
- This project: See main README.md

## Estimated Setup Time

- First time: 1-2 hours (including Docker build)
- Subsequent deployments: 15-20 minutes

Good luck! 🚀

