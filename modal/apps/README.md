# ComfyUI Modal Apps with Backblaze B2

This directory contains the Modal.com deployment for ComfyUI with integrated Backblaze B2 storage.

## 🚀 Quick Start

```bash
# 1. Setup B2 credentials (interactive)
./setup_b2.sh

# 2. Or create secret manually
modal secret create backblaze-b2-credentials \
  USE_BACKBLAZE_B2=true \
  B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com \
  B2_REGION=us-east-005 \
  B2_BUCKET=your-bucket \
  B2_KEY_ID=your-key-id \
  B2_APP_KEY=your-app-key \
  B2_PUBLIC_URL=https://f005.backblazeb2.com/file/your-bucket

# 3. Deploy
modal deploy modal_app_fastapi.py

# 4. Test
curl https://YOUR-WORKSPACE--comfyui-api-web.modal.run/b2/status
```

## 📁 Files

### Main Application
- **`modal_app_fastapi.py`** - FastAPI app with ComfyUI and B2 integration
- **`b2_storage.py`** - Backblaze B2 storage module

### Documentation
- **`BACKBLAZE_B2_INTEGRATION.md`** - Complete technical documentation
- **`BACKEND_INTEGRATION_GUIDE.md`** - Backend integration guide
- **`B2_QUICK_REFERENCE.md`** - Quick reference card
- **`README.md`** - This file

### Tools
- **`setup_b2.sh`** - Interactive setup script
- **`example_b2_client.py`** - Example Python client

## 🎯 Features

✅ **Automatic B2 Upload** - Generated images upload directly to Backblaze B2  
✅ **Public URLs** - Get CDN-ready URLs immediately  
✅ **Synchronous Execution** - Wait for completion and get results  
✅ **Date Organization** - Files organized by YYYY/MM/DD  
✅ **Cost-Effective** - ~77% cheaper than AWS S3  
✅ **Fast** - ~40% faster than file transfer to backend  

## 📡 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and B2 status |
| `/prompt` | POST | Execute workflow (async or sync) |
| `/execute_and_upload` | POST | Simplified sync execution with B2 |
| `/queue` | GET | Check queue status |
| `/history` | GET | Get execution history |
| `/history/{id}` | GET | Get specific execution |
| `/history/{id}/upload_to_b2` | POST | Upload existing output to B2 |

### B2 & System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/b2/status` | GET | Check B2 configuration and recent uploads |
| `/system_stats` | GET | System and GPU information |
| `/outputs` | GET | List output files (Modal volume) |
| `/outputs/{filename}` | GET | Download output file |
| `/object_info` | GET | Available ComfyUI nodes |

## 💻 Usage Examples

### Python (Synchronous with B2)

```python
import requests

response = requests.post(
    "https://your-endpoint.modal.run/prompt",
    json={
        "prompt": workflow,
        "wait_for_completion": True,  # Wait for execution
        "upload_to_b2": True           # Upload to B2 (default)
    },
    timeout=600
)

result = response.json()

# Get B2 URLs
b2_uploads = result["execution"]["b2_uploads"]
for node_id, data in b2_uploads.items():
    for upload in data["uploads"]:
        print(f"Image: {upload['url']}")
        print(f"Size: {upload['size']} bytes")
```

### Python (Simplified)

```python
response = requests.post(
    "https://your-endpoint.modal.run/execute_and_upload",
    json={"prompt": workflow}
)
# Always synchronous with B2 upload
```

### cURL

```bash
# Check B2 status
curl https://your-endpoint.modal.run/b2/status

# Execute workflow
curl -X POST https://your-endpoint.modal.run/execute_and_upload \
  -H "Content-Type: application/json" \
  -d '{"prompt": {...}}'
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AIDreamBees Backend                  │
│                        (Django)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ POST /prompt
                     │ {prompt: {...}, wait_for_completion: true}
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ComfyUI on Modal (FastAPI)                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   ComfyUI   │→ │  B2 Storage  │→ │  Backblaze B2 │ │
│  │  Execution  │  │    Module    │  │    Bucket     │ │
│  └─────────────┘  └──────────────┘  └───────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Returns B2 URLs
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Backend saves URL to DB                  │
│            Frontend displays from B2 CDN                │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables (Modal Secret)

```bash
USE_BACKBLAZE_B2=true                                    # Enable B2
B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com      # S3-compatible endpoint
B2_REGION=us-east-005                                    # Bucket region
B2_BUCKET=your-bucket-name                               # Bucket name
B2_KEY_ID=your-key-id                                    # Application key ID
B2_APP_KEY=your-app-key                                  # Application key secret
B2_PUBLIC_URL=https://f005.backblazeb2.com/file/bucket  # Public URL base
```

### Backblaze B2 Setup

1. Create account at [backblaze.com](https://www.backblaze.com/b2)
2. Create a **public** bucket
3. Generate application keys with **Read and Write** permissions
4. Note the endpoint URL and public URL from bucket details

## 📤 File Organization

Files are automatically organized by date:

```
your-bucket/
└── generations/
    └── 2025/
        └── 10/
            └── 20/
                ├── ComfyUI_00001_.png
                ├── ComfyUI_00002_.png
                └── ComfyUI_00003_.png
```

## 🔍 Response Format

### Successful Execution

```json
{
  "prompt_id": "abc-123-def-456",
  "number": 1,
  "valid": true,
  "execution": {
    "status": "completed",
    "execution_time": 15.234,
    "outputs": {
      "9": {
        "images": [
          {
            "filename": "ComfyUI_00001_.png",
            "subfolder": "",
            "type": "output"
          }
        ]
      }
    },
    "b2_uploads": {
      "9": {
        "type": "images",
        "uploads": [
          {
            "filename": "ComfyUI_00001_.png",
            "url": "https://f005.backblazeb2.com/file/bucket/generations/2025/10/20/ComfyUI_00001_.png",
            "size": 2457600,
            "b2_key": "generations/2025/10/20/ComfyUI_00001_.png"
          }
        ]
      }
    }
  }
}
```

## 🐛 Troubleshooting

### B2 Not Enabled

**Symptom**: `"enabled": false` in `/b2/status`

**Solution**:
```bash
# Verify secret exists
modal secret list

# Recreate if needed
./setup_b2.sh
```

### Upload Fails

**Symptom**: No URLs in response

**Solution**:
1. Check bucket is **public**
2. Verify credentials in Modal secret
3. Check logs: `modal app logs comfyui-api`

### Timeout Errors

**Symptom**: Request times out

**Solution**:
```python
# Increase timeout
response = requests.post(..., timeout=900)  # 15 minutes
```

### 404 on Image URL

**Symptom**: B2 URL returns 404

**Solution**:
- Verify `B2_PUBLIC_URL` is correct
- Check bucket permissions (must be public)
- Verify file exists in B2 dashboard

## 📊 Performance

### Before (File Transfer to Backend)
- Generation: 15s
- Transfer to backend: 5-10s
- Backend upload to storage: 3-5s
- **Total: 23-30s**

### After (Direct B2 Upload)
- Generation: 15s
- Upload to B2: 2-3s
- Return URL: <1s
- **Total: 17-19s**

**⚡ ~40% faster!**

## 💰 Cost Comparison

### Example: 1,000 images/month, 2.5 MB each

| Service | Storage | Bandwidth | Total |
|---------|---------|-----------|-------|
| **Backblaze B2** | $0.015 | $0.25 | **$0.27/mo** |
| AWS S3 | $0.06 | $0.90 | $1.20/mo |
| **Savings** | 75% | 72% | **77%** |

## 🔐 Security

- ✅ Use application keys (not master credentials)
- ✅ Limit key permissions to specific bucket
- ✅ Store credentials in Modal secrets
- ✅ Never commit credentials to git
- ✅ Rotate keys periodically
- ✅ Monitor usage in B2 dashboard

## 📚 Documentation

- **[BACKBLAZE_B2_INTEGRATION.md](BACKBLAZE_B2_INTEGRATION.md)** - Complete technical guide
  - Setup instructions
  - API usage
  - Response formats
  - Troubleshooting
  - Cost analysis

- **[BACKEND_INTEGRATION_GUIDE.md](BACKEND_INTEGRATION_GUIDE.md)** - Backend integration
  - Quick start (5 minutes)
  - Code examples
  - Django model updates
  - Migration steps

- **[B2_QUICK_REFERENCE.md](B2_QUICK_REFERENCE.md)** - Quick reference card
  - Common commands
  - API endpoints
  - Troubleshooting

- **[example_b2_client.py](example_b2_client.py)** - Python client example
  - Drop-in Django integration
  - Full example code

## 🔄 Updates

### Deployment

```bash
# Deploy updates
modal deploy modal_app_fastapi.py

# View logs
modal app logs comfyui-api

# Monitor
watch -n 5 'curl -s https://your-endpoint.modal.run/b2/status | jq'
```

### Updating Secrets

```bash
# Delete old secret
modal secret delete backblaze-b2-credentials

# Create new secret
./setup_b2.sh

# Redeploy (secrets are loaded on startup)
modal deploy modal_app_fastapi.py
```

## 🆘 Support

- **Backblaze B2 Docs**: https://www.backblaze.com/b2/docs/
- **Modal Docs**: https://modal.com/docs
- **S3 API Reference**: https://www.backblaze.com/b2/docs/s3_compatible_api.html

## 📝 License

Same as ComfyUI parent project.

