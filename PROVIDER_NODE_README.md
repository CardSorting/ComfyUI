# Provider Node Integration

The ComfyUI container now includes built-in provider node functionality for the decentralized compute cluster. This allows your ComfyUI instance to automatically pull and execute jobs from a coordinator service.

## Features

- **Automatic Job Processing**: Pulls jobs from coordinator and executes them using ComfyUI
- **Workflow Execution**: Executes ComfyUI workflows received from the coordinator
- **Result Submission**: Automatically submits results back to the coordinator
- **Heartbeat Monitoring**: Sends periodic heartbeats to maintain connection
- **GPU Detection**: Automatically detects GPU capabilities
- **Background Operation**: Runs in a background thread, doesn't interfere with normal ComfyUI operation

## Configuration

The provider node is **disabled by default**. To enable it, set the following environment variables:

### Required Environment Variables

- `ENABLE_PROVIDER_NODE=1` - Enable the provider node (set to "1", "true", or "yes")
- `COORDINATOR_URL` - URL of the coordinator service (e.g., `http://coordinator:3000` or `https://coordinator.example.com`)
- `WALLET_ADDRESS` - Your Solana wallet address for receiving payments

### Optional Environment Variables

- `PROVIDER_ID` - Provider ID (auto-assigned after registration if not set)
- `GPU_TYPE` - GPU model name (auto-detected if not set)
- `GPU_MEMORY_GB` - GPU memory in GB (auto-detected if not set)
- `SUPPORTED_MODELS` - Comma-separated list of supported models (default: `runwayml/stable-diffusion-v1-5,stabilityai/stable-diffusion-xl-base-1.0`)
- `MAX_CONCURRENT_JOBS` - Maximum parallel jobs (default: `1`)
- `COMFYUI_URL` - ComfyUI API URL (default: `http://localhost:8188`)

## Usage

### Docker

```bash
docker run -d \
  --name comfyui-provider \
  --gpus all \
  -e ENABLE_PROVIDER_NODE=1 \
  -e COORDINATOR_URL=https://coordinator.example.com \
  -e WALLET_ADDRESS=your_solana_wallet_address \
  -e SUPPORTED_MODELS=runwayml/stable-diffusion-v1-5 \
  -e MAX_CONCURRENT_JOBS=1 \
  -p 8188:8188 \
  comfyui:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  comfyui:
    image: comfyui:latest
    ports:
      - "8188:8188"
    environment:
      - ENABLE_PROVIDER_NODE=1
      - COORDINATOR_URL=http://coordinator:3000
      - WALLET_ADDRESS=your_solana_wallet_address
      - SUPPORTED_MODELS=runwayml/stable-diffusion-v1-5
      - MAX_CONCURRENT_JOBS=1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Local Development

```bash
export ENABLE_PROVIDER_NODE=1
export COORDINATOR_URL=http://localhost:3000
export WALLET_ADDRESS=your_solana_wallet_address
export SUPPORTED_MODELS=runwayml/stable-diffusion-v1-5

python main.py --headless --listen 0.0.0.0 --port 8188
```

## How It Works

1. **Startup**: When ComfyUI starts, if `ENABLE_PROVIDER_NODE=1` is set, the provider node starts in a background thread
2. **Registration**: The provider node registers with the coordinator, providing GPU capabilities and supported models
3. **Job Polling**: The provider node periodically polls the coordinator for new jobs
4. **Execution**: When a job is received, it executes the workflow using ComfyUI's API
5. **Result Submission**: Results (images, execution time, etc.) are submitted back to the coordinator
6. **Heartbeat**: Periodic heartbeats are sent to maintain the connection

## Job Format

Jobs from the coordinator should include:

```json
{
  "id": "job-123",
  "workflow": {
    "1": {
      "inputs": {
        "text": "a beautiful landscape",
        "clip": ["4", 1]
      },
      "class_type": "CLIPTextEncode"
    },
    "4": {
      "inputs": {
        "ckpt_name": "v1-5-pruned-emaonly.ckpt"
      },
      "class_type": "CheckpointLoaderSimple"
    }
  }
}
```

## Result Format

Results submitted to the coordinator:

```json
{
  "status": "success",
  "images": [
    {
      "filename": "ComfyUI_00001_.png",
      "base64": "iVBORw0KGgoAAAANS...",
      "content_type": "image/png"
    }
  ],
  "execution_time": 12.34,
  "workflow_outputs": {
    "10": {
      "images": [
        {
          "filename": "ComfyUI_00001_.png",
          "subfolder": "",
          "type": "output"
        }
      ]
    }
  }
}
```

## Monitoring

### Logs

The provider node logs all activities:

```
2024-01-28 10:00:00 - Provider initialized: abc123
2024-01-28 10:00:00 - Device: cuda
2024-01-28 10:00:00 - GPU: NVIDIA GeForce RTX 3060 (12GB)
2024-01-28 10:00:05 - ✅ ComfyUI API is ready
2024-01-28 10:00:05 - ✅ Registered successfully: abc123
2024-01-28 10:00:05 - 👂 Listening for jobs...
2024-01-28 10:00:15 - 📦 Job received: job-xyz
2024-01-28 10:00:15 - Submitting workflow to ComfyUI...
2024-01-28 10:00:25 - ✅ Workflow completed in 10.2s
2024-01-28 10:00:25 - ✅ Result submitted for job job-xyz
```

### Status Check

The provider node runs in the background and doesn't expose a separate status endpoint. Check ComfyUI logs to see provider node activity.

## Troubleshooting

### Provider Node Not Starting

- Check that `ENABLE_PROVIDER_NODE=1` is set
- Verify `COORDINATOR_URL` and `WALLET_ADDRESS` are set
- Check ComfyUI logs for error messages

### Registration Fails

- Verify coordinator URL is correct and accessible
- Check network connectivity: `curl $COORDINATOR_URL/health`
- Verify wallet address is valid

### No Jobs Being Received

- Wait a few minutes (network registration takes time)
- Check logs for connection errors
- Verify supported models match jobs in the queue
- Check coordinator logs for job availability

### Workflow Execution Fails

- Verify the workflow is valid ComfyUI workflow JSON
- Check that required models are available in ComfyUI
- Review ComfyUI logs for execution errors
- Ensure GPU has enough memory for the workflow

## Integration with Coordinator

The provider node communicates with the coordinator via REST API:

- `POST /api/v1/provider/register` - Register provider
- `POST /api/v1/provider/heartbeat` - Send heartbeat
- `GET /api/v1/provider/jobs/next` - Pull next job
- `POST /api/v1/provider/jobs/{job_id}/result` - Submit result

## Security Considerations

- **Wallet Address**: Keep your wallet address secure
- **Network**: Use HTTPS for coordinator URL in production
- **Firewall**: Ensure coordinator can reach your ComfyUI instance if needed
- **Resource Limits**: Set `MAX_CONCURRENT_JOBS` appropriately to prevent resource exhaustion

## Disabling Provider Node

To disable the provider node, simply don't set `ENABLE_PROVIDER_NODE` or set it to `0`, `false`, or `no`. ComfyUI will run normally without provider node functionality.

## Support

For issues related to:
- **Provider Node**: Check this README and ComfyUI logs
- **Coordinator**: Contact coordinator service administrator
- **ComfyUI**: See main ComfyUI documentation

