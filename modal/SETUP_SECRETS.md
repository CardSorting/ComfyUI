# Setting Up Modal Secrets for ComfyUI

## Overview

Your ComfyUI deployment needs two optional secrets:
1. **Backblaze B2 Credentials** - For automatic image uploads to B2 storage
2. **Civitai API Key** - For downloading models from Civitai

## Secret 1: Backblaze B2 Credentials

### What It's For
- Automatically uploads generated images to Backblaze B2 storage
- Provides public URLs for generated images
- Enables persistent storage outside Modal containers

### Setup Steps

#### 1. Get B2 Credentials

If you don't have a Backblaze B2 account:
1. Sign up at [backblaze.com/b2](https://www.backblaze.com/b2/cloud-storage.html)
2. Create a bucket (make it public)
3. Create an Application Key with read/write access
4. Save your credentials:
   - **Endpoint**: `https://s3.REGION.backblazeb2.com` (e.g., `https://s3.us-east-005.backblazeb2.com`)
   - **Region**: Your bucket region (e.g., `us-east-005`)
   - **Bucket Name**: Your bucket name
   - **Key ID**: Application Key ID
   - **Application Key**: The secret key
   - **Public URL**: Your bucket's public URL

#### 2. Create Modal Secret

**Option A: Via Modal Dashboard (Recommended)**
1. Go to: https://modal.com/secrets
2. Click "Create Secret"
3. Name: `backblaze-b2-credentials`
4. Add these key-value pairs:
   ```
   USE_BACKBLAZE_B2=true
   B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com
   B2_REGION=us-east-005
   B2_BUCKET=your-bucket-name
   B2_KEY_ID=your-key-id
   B2_APP_KEY=your-application-key
   B2_PUBLIC_URL=https://f005.backblazeb2.com/file/your-bucket-name
   ```
5. Click "Create"

**Option B: Via CLI**
```bash
modal secret create backblaze-b2-credentials \
  USE_BACKBLAZE_B2=true \
  B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com \
  B2_REGION=us-east-005 \
  B2_BUCKET=your-bucket-name \
  B2_KEY_ID=your-key-id \
  B2_APP_KEY=your-application-key \
  B2_PUBLIC_URL=https://f005.backblazeb2.com/file/your-bucket-name
```

**Option C: Use Interactive Script**
```bash
./modal/setup_secrets.sh
```

### Verify B2 Secret
```bash
modal secret list
# Should show: backblaze-b2-credentials
```

---

## Secret 2: Civitai API Key

### What It's For
- Downloads models from Civitai (especially private models)
- Removes rate limits for API access
- Enables faster model downloads

### Setup Steps

#### 1. Get Civitai API Key

1. Go to [civitai.com](https://civitai.com)
2. Sign in to your account
3. Go to Settings → API Keys
4. Create a new API key
5. Copy the key (you'll only see it once!)

#### 2. Create Modal Secret

**Option A: Via Modal Dashboard**
1. Go to: https://modal.com/secrets
2. Click "Create Secret"
3. Name: `civitai-api-key`
4. Add this key-value pair:
   ```
   CIVITAI_API_KEY=your-api-key-here
   ```
5. Click "Create"

**Option B: Via CLI**
```bash
modal secret create civitai-api-key \
  CIVITAI_API_KEY=your-api-key-here
```

**Option C: Use Interactive Script**
```bash
./modal/setup_secrets.sh
```

### Verify Civitai Secret
```bash
modal secret list
# Should show: civitai-api-key
```

---

## Quick Setup Script

Use the interactive setup script:

```bash
cd /Users/bozoegg/ComfyUI
./modal/setup_secrets.sh
```

This script will:
- Guide you through setting up both secrets
- Validate your inputs
- Create secrets via Modal CLI
- Verify they were created

---

## Verify Secrets Are Working

After creating secrets, redeploy your app:

```bash
modal deploy modal/apps/modal_app_fastapi.py
```

Then check the logs to see if secrets are loaded:

```bash
modal app logs comfyui-api
```

Look for:
- ✅ "Backblaze B2 enabled: your-bucket-name"
- ✅ "Civitai API key loaded"

---

## Troubleshooting

### Secret Not Found After Creation

1. **Verify secret exists:**
   ```bash
   modal secret list
   ```

2. **Check secret name matches exactly:**
   - B2: `backblaze-b2-credentials` (lowercase, with hyphens)
   - Civitai: `civitai-api-key` (lowercase, with hyphens)

3. **Redeploy app:**
   ```bash
   modal deploy modal/apps/modal_app_fastapi.py
   ```

### B2 Uploads Not Working

1. **Check environment variables are set:**
   - All 7 variables must be present
   - `USE_BACKBLAZE_B2=true` is required

2. **Verify bucket is public:**
   - B2 bucket must be set to "Public" for public URLs

3. **Check B2 credentials:**
   - Key ID and Application Key must be correct
   - Application Key must have read/write permissions

### Civitai Downloads Failing

1. **Verify API key is valid:**
   - Test key at civitai.com
   - Ensure key hasn't expired

2. **Check rate limits:**
   - Free tier has rate limits
   - Paid tier has higher limits

---

## Secret Structure Reference

### Backblaze B2 Secret (`backblaze-b2-credentials`)
```
USE_BACKBLAZE_B2=true
B2_ENDPOINT=https://s3.REGION.backblazeb2.com
B2_REGION=us-east-005
B2_BUCKET=your-bucket-name
B2_KEY_ID=your-key-id
B2_APP_KEY=your-application-key
B2_PUBLIC_URL=https://f005.backblazeb2.com/file/your-bucket-name
```

### Civitai Secret (`civitai-api-key`)
```
CIVITAI_API_KEY=your-api-key-here
```

---

## Next Steps

1. ✅ Create B2 secret (if you need B2 uploads)
2. ✅ Create Civitai secret (if you need Civitai downloads)
3. ✅ Redeploy app: `modal deploy modal/apps/modal_app_fastapi.py`
4. ✅ Verify secrets are loaded in logs

---

## Notes

- **Secrets are optional** - App works without them, just without those features
- **Secrets are secure** - Stored encrypted in Modal
- **Secrets are workspace-specific** - Each Modal workspace has its own secrets
- **Secrets can be updated** - Update via dashboard or CLI, then redeploy

