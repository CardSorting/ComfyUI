# Backblaze B2 Quick Reference

## Setup (One-Time)

```bash
cd /Users/bozoegg/ComfyUI/modal/apps
./setup_b2.sh
```

Or manually:

```bash
# 1. Create Modal secret
modal secret create backblaze-b2-credentials \
  USE_BACKBLAZE_B2=true \
  B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com \
  B2_REGION=us-east-005 \
  B2_BUCKET=your-bucket-name \
  B2_KEY_ID=your-key-id \
  B2_APP_KEY=your-app-key \
  B2_PUBLIC_URL=https://f005.backblazeb2.com/file/your-bucket-name

# 2. Deploy
modal deploy modal_app_fastapi.py
```

## Usage

### Python Client

```python
import requests

# Execute and get B2 URLs
response = requests.post(
    "https://cardsorting--comfyui-api-web.modal.run/prompt",
    json={
        "prompt": workflow,
        "wait_for_completion": True,
        "upload_to_b2": True
    },
    timeout=600
)

result = response.json()
b2_uploads = result["execution"]["b2_uploads"]

# Get first image URL
for node_id, data in b2_uploads.items():
    url = data["uploads"][0]["url"]
    print(url)
```

### Simplified Endpoint

```python
response = requests.post(
    "https://cardsorting--comfyui-api-web.modal.run/execute_and_upload",
    json={"prompt": workflow}
)
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and B2 status |
| `/prompt` | POST | Execute workflow (set `wait_for_completion=true`) |
| `/execute_and_upload` | POST | Simplified sync execution |
| `/b2/status` | GET | Check B2 configuration |
| `/history/{id}/upload_to_b2` | POST | Upload existing outputs |
| `/system_stats` | GET | System information |

## Response Format

```json
{
  "prompt_id": "abc-123",
  "execution": {
    "status": "completed",
    "b2_uploads": {
      "9": {
        "type": "images",
        "uploads": [
          {
            "url": "https://f005.backblazeb2.com/file/.../image.png",
            "size": 2457600,
            "filename": "image.png"
          }
        ]
      }
    }
  }
}
```

## Commands

```bash
# Deploy
modal deploy modal_app_fastapi.py

# Check status
curl https://YOUR-ENDPOINT.modal.run/b2/status

# View logs
modal app logs comfyui-api

# List secrets
modal secret list

# Update secret
modal secret delete backblaze-b2-credentials
modal secret create backblaze-b2-credentials ...
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| B2 not enabled | Check secret exists: `modal secret list` |
| Upload fails | Verify bucket is public, check credentials |
| Timeout | Increase `timeout=900` in request |
| 404 on URL | Verify `B2_PUBLIC_URL` is correct |

## Files

- `modal_app_fastapi.py` - Main FastAPI app
- `b2_storage.py` - B2 storage module
- `BACKBLAZE_B2_INTEGRATION.md` - Full documentation
- `BACKEND_INTEGRATION_GUIDE.md` - Backend guide
- `example_b2_client.py` - Example client
- `setup_b2.sh` - Setup script

## Backend Integration

1. Add `image_url` field to Generation model
2. Update ComfyUI client (see `example_b2_client.py`)
3. Modify views to save B2 URLs
4. Run migrations

See `BACKEND_INTEGRATION_GUIDE.md` for details.

## Costs (Example: 1,000 images/month)

- Storage: $0.015/month
- Bandwidth: $0.25/month
- **Total: ~$0.27/month** 💰

## Support

- **Backblaze B2**: https://www.backblaze.com/b2/docs/
- **Modal**: https://modal.com/docs
- **Full Guide**: `BACKBLAZE_B2_INTEGRATION.md`

