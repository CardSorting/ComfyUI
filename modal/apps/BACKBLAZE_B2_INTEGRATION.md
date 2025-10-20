# Backblaze B2 Integration for ComfyUI Modal

## Overview

This integration allows ComfyUI running on Modal to automatically upload generated images to Backblaze B2 storage and return public URLs. This solves the timing issue where outputs couldn't be efficiently transferred back to the backend.

## Architecture

```
Backend (Django) → Modal (ComfyUI + FastAPI) → Backblaze B2
                   ↓
                   Returns B2 URLs directly
```

### Benefits

✅ **No file transfer delays** - Images go directly to B2  
✅ **Cost-effective storage** - B2 is ~74% cheaper than S3  
✅ **CDN-ready** - B2 files are immediately accessible via public URL  
✅ **Persistent storage** - Files remain available after Modal container shuts down  
✅ **Automatic organization** - Files are organized by date (YYYY/MM/DD)  

## Setup

### Step 1: Configure Backblaze B2

1. **Create a B2 Account**
   - Visit [backblaze.com](https://www.backblaze.com/b2/cloud-storage.html)
   - Sign up for an account

2. **Create a Bucket**
   - Go to "B2 Cloud Storage" → "Buckets"
   - Click "Create a Bucket"
   - Name: `your-app-generations` (or your choice)
   - Files in Bucket: **Public**
   - Default Encryption: Disabled (optional)
   - Object Lock: Disabled

3. **Create Application Keys**
   - Go to "App Keys"
   - Click "Add a New Application Key"
   - Key Name: `comfyui-modal-app`
   - Allow access to: Select your bucket
   - Permissions: **Read and Write**
   - Click "Create New Key"
   - **IMPORTANT**: Save the `keyID` and `applicationKey` immediately!

4. **Get Your Configuration Values**
   - **Endpoint**: `https://s3.us-east-005.backblazeb2.com` (check your region)
   - **Region**: `us-east-005` (from your bucket details)
   - **Bucket Name**: Your bucket name
   - **Public URL**: `https://f005.backblazeb2.com/file/your-bucket-name` (from bucket details)

### Step 2: Create Modal Secret

Create a Modal secret with your B2 credentials:

```bash
modal secret create backblaze-b2-credentials \
  USE_BACKBLAZE_B2=true \
  B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com \
  B2_REGION=us-east-005 \
  B2_BUCKET=your-bucket-name \
  B2_KEY_ID=your-key-id \
  B2_APP_KEY=your-app-key \
  B2_PUBLIC_URL=https://f005.backblazeb2.com/file/your-bucket-name
```

**Or create via Modal Dashboard:**

1. Go to [modal.com](https://modal.com) → Your workspace
2. Click "Secrets" in the sidebar
3. Click "Create Secret"
4. Name: `backblaze-b2-credentials`
5. Add these environment variables:
   - `USE_BACKBLAZE_B2` = `true`
   - `B2_ENDPOINT` = `https://s3.us-east-005.backblazeb2.com`
   - `B2_REGION` = `us-east-005`
   - `B2_BUCKET` = `your-bucket-name`
   - `B2_KEY_ID` = `your-key-id`
   - `B2_APP_KEY` = `your-app-key`
   - `B2_PUBLIC_URL` = `https://f005.backblazeb2.com/file/your-bucket-name`

### Step 3: Deploy the Modal App

```bash
cd /Users/bozoegg/ComfyUI/modal/apps
modal deploy modal_app_fastapi.py
```

The app will automatically:
- Load B2 credentials from the secret
- Initialize the B2 storage client
- Enable automatic uploads

## API Usage

### Option 1: Synchronous Execution with B2 Upload (Recommended)

This is the easiest way to use the API. It waits for execution to complete and automatically uploads to B2:

```python
import requests

# Your Modal endpoint
COMFYUI_ENDPOINT = "https://cardsorting--comfyui-api-web.modal.run"

# Queue workflow with synchronous execution
response = requests.post(
    f"{COMFYUI_ENDPOINT}/prompt",
    json={
        "prompt": your_workflow_dict,
        "wait_for_completion": True,  # Wait for completion
        "upload_to_b2": True,          # Upload to B2 (default: True)
    }
)

result = response.json()

# Access B2 URLs directly
if "execution" in result and "b2_uploads" in result["execution"]:
    b2_uploads = result["execution"]["b2_uploads"]
    
    # Example: Get the first uploaded image URL
    for node_id, upload_data in b2_uploads.items():
        if upload_data["type"] == "images":
            for image in upload_data["uploads"]:
                print(f"Image URL: {image['url']}")
                print(f"Size: {image['size']} bytes")
```

### Option 2: Simplified Execute and Upload Endpoint

Even simpler - this endpoint always waits and uploads:

```python
response = requests.post(
    f"{COMFYUI_ENDPOINT}/execute_and_upload",
    json={
        "prompt": your_workflow_dict
    }
)

result = response.json()
# Same response structure as above
```

### Option 3: Asynchronous with Manual Upload

For long-running workflows, you can queue asynchronously and upload later:

```python
# 1. Queue the workflow (async)
response = requests.post(
    f"{COMFYUI_ENDPOINT}/prompt",
    json={
        "prompt": your_workflow_dict,
        "wait_for_completion": False  # Async mode
    }
)

prompt_id = response.json()["prompt_id"]

# 2. Later, check if complete
history = requests.get(
    f"{COMFYUI_ENDPOINT}/history/{prompt_id}"
).json()

# 3. Upload to B2 manually
if prompt_id in history and "outputs" in history[prompt_id]:
    upload_response = requests.post(
        f"{COMFYUI_ENDPOINT}/history/{prompt_id}/upload_to_b2"
    )
    b2_uploads = upload_response.json()["b2_uploads"]
```

## Response Format

### Successful Execution with B2 Upload

```json
{
  "prompt_id": "abc-123-def-456",
  "number": 1,
  "valid": true,
  "node_errors": {},
  "execution": {
    "status": "completed",
    "prompt_id": "abc-123-def-456",
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
            "url": "https://f005.backblazeb2.com/file/your-bucket/generations/2025/10/20/ComfyUI_00001_.png",
            "size": 2457600,
            "b2_key": "generations/2025/10/20/ComfyUI_00001_.png"
          }
        ]
      }
    }
  }
}
```

### File Organization in B2

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

## Backend Integration (Django)

### Update Your ComfyUI Client

Update your Django app's ComfyUI client to use the new endpoint:

```python
# apps/comfyui/client.py

class ComfyUIClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip('/')
    
    def generate_image(self, workflow: dict, wait: bool = True) -> dict:
        """
        Execute a ComfyUI workflow
        
        Args:
            workflow: The ComfyUI workflow dictionary
            wait: If True, waits for completion and returns B2 URLs
        
        Returns:
            Dict with execution results and B2 URLs
        """
        response = requests.post(
            f"{self.endpoint}/prompt",
            json={
                "prompt": workflow,
                "wait_for_completion": wait,
                "upload_to_b2": True
            },
            timeout=600  # 10 minute timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_image_urls(self, result: dict) -> list:
        """
        Extract B2 image URLs from execution result
        
        Args:
            result: Result from generate_image()
        
        Returns:
            List of image URLs
        """
        urls = []
        
        if "execution" in result and "b2_uploads" in result["execution"]:
            b2_uploads = result["execution"]["b2_uploads"]
            
            for node_id, upload_data in b2_uploads.items():
                if upload_data.get("type") == "images":
                    for image in upload_data.get("uploads", []):
                        if "url" in image:
                            urls.append(image["url"])
        
        return urls
```

### Update Your Generation View

```python
# apps/generations/views.py

from apps.comfyui.client import ComfyUIClient
from django.conf import settings

def create_generation(request):
    # ... your existing code ...
    
    # Initialize client
    client = ComfyUIClient(settings.COMFYUI_ENDPOINT)
    
    # Execute workflow
    result = client.generate_image(workflow, wait=True)
    
    # Extract B2 URLs
    image_urls = client.get_image_urls(result)
    
    if image_urls:
        # Save the B2 URL to your model
        generation.image_url = image_urls[0]  # Add this field to your model
        generation.save()
        
        return Response({
            "id": generation.id,
            "image_url": image_urls[0],
            "prompt_id": result["prompt_id"]
        })
    else:
        return Response(
            {"error": "No images generated"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### Add Image URL Field to Model

```python
# apps/generations/models.py

class Generation(models.Model):
    # ... existing fields ...
    
    # Option 1: Store B2 URL instead of file
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Option 2: Keep both for backward compatibility
    image = models.ImageField(upload_to='generations/', null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    def get_image_url(self):
        """Return the B2 URL if available, otherwise the local file URL"""
        if self.image_url:
            return self.image_url
        elif self.image:
            return self.image.url
        return None
```

## Monitoring and Management

### Check B2 Status

```bash
curl https://your-modal-endpoint.modal.run/b2/status
```

Returns:
```json
{
  "enabled": true,
  "storage_info": {
    "enabled": true,
    "bucket": "your-bucket-name",
    "region": "us-east-005",
    "endpoint": "https://s3.us-east-005.backblazeb2.com",
    "public_url": "https://f005.backblazeb2.com/file/your-bucket-name"
  },
  "recent_uploads": [
    {
      "key": "generations/2025/10/20/ComfyUI_00001_.png",
      "size": 2457600,
      "last_modified": "2025-10-20T10:30:00Z"
    }
  ]
}
```

### View Logs

```bash
modal app logs comfyui-api
```

Look for:
- `☁️ Backblaze B2 enabled: your-bucket-name` - B2 initialized
- `📤 Uploading to B2: generations/...` - Upload started
- `✅ Uploaded to B2: filename (size KB)` - Upload succeeded

## Troubleshooting

### B2 Not Enabled

**Problem**: API returns `"b2_uploads": {"error": "B2 storage is not enabled"}`

**Solution**:
1. Verify the Modal secret exists: `modal secret list`
2. Check secret name matches: `backblaze-b2-credentials`
3. Ensure `USE_BACKBLAZE_B2=true` in the secret
4. Redeploy: `modal deploy modal_app_fastapi.py`

### Upload Fails

**Problem**: Files don't appear in B2

**Solution**:
1. Check B2 credentials are correct
2. Verify bucket permissions (should be Public)
3. Check Modal logs for error messages
4. Test B2 connection directly:

```python
import boto3

s3_client = boto3.client(
    's3',
    endpoint_url='https://s3.us-east-005.backblazeb2.com',
    aws_access_key_id='your-key-id',
    aws_secret_access_key='your-app-key',
    region_name='us-east-005'
)

# Test list operation
response = s3_client.list_objects_v2(Bucket='your-bucket', MaxKeys=1)
print(response)
```

### Timeout Issues

**Problem**: Requests timeout before completion

**Solution**:
1. Increase timeout in your client: `timeout=600` (10 minutes)
2. For very long workflows, use async mode:
   ```python
   # Queue async
   result = client.generate_image(workflow, wait=False)
   prompt_id = result["prompt_id"]
   
   # Poll for completion
   # Upload to B2 when ready
   ```

## Cost Estimation

### Backblaze B2 Pricing (as of 2025)

- **Storage**: $0.006/GB/month (first 10GB free)
- **Bandwidth**: $0.01/GB (first 1GB/day free)
- **API Calls**: Free for Class C transactions (uploads, lists)

### Example Usage

For an app with:
- 1,000 images/month
- Average 2.5 MB per image
- 10,000 views/month

**Monthly Cost**:
- Storage: 2.5 GB × $0.006 = **$0.015**
- Bandwidth: 25 GB × $0.01 = **$0.25**
- **Total: ~$0.27/month**

Compare to AWS S3: ~$1.20/month (4.5× more expensive)

## Security Best Practices

1. **Use Application Keys**: Never use your master B2 account credentials
2. **Limit Bucket Access**: Create keys with access only to specific buckets
3. **Rotate Keys**: Periodically rotate your application keys
4. **Monitor Usage**: Set up billing alerts in B2 dashboard
5. **Keep Secrets Secret**: Never commit credentials to git

## Migration from Local Storage

If you were previously storing files locally or returning them from Modal:

1. **Deploy the new version** with B2 integration
2. **Update your backend** to use the new response format
3. **Test with a single request** to verify B2 URLs work
4. **Gradually migrate** - old code will continue to work
5. **Remove local file handling** once fully migrated

## Support

- **Backblaze B2 Docs**: https://www.backblaze.com/b2/docs/
- **Modal Docs**: https://modal.com/docs
- **S3 API Reference**: https://www.backblaze.com/b2/docs/s3_compatible_api.html

