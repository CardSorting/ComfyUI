# Downloading Models from URLs Directly to Modal

## Quick Answer

✅ **YES!** Modal can download models directly from URLs without needing them on your local machine.

You have **3 main options**:

1. **Download directly in Modal** (Recommended)
2. **Hugging Face Hub integration** (Best for HF models)
3. **Automated download scripts** (For CI/CD)

## Option 1: Download Directly in Modal (Recommended)

### Step 1: Edit `modal_app.py`

Find the `download_models()` function and add your model URLs:

```python
@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=3600,  # 1 hour timeout for large downloads
)
def download_models():
    """
    Download models directly to Modal volume from URLs
    """
    import urllib.request
    import os
    
    def download_file(url, dest_path):
        """Download file with progress"""
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        if os.path.exists(dest_path):
            print(f"⏭️  Already exists: {dest_path}")
            return
        
        print(f"📥 Downloading from: {url}")
        print(f"📁 Saving to: {dest_path}")
        
        try:
            urllib.request.urlretrieve(url, dest_path)
            file_size = os.path.getsize(dest_path) / (1024**3)
            print(f"✅ Downloaded: {dest_path} ({file_size:.2f} GB)")
        except Exception as e:
            print(f"❌ Failed to download {dest_path}: {e}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ADD YOUR MODEL URLS HERE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    models_to_download = [
        # Checkpoints
        {
            "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
            "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
        },
        {
            "url": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors",
            "path": "/models/checkpoints/sd_v1.5.safetensors"
        },
        
        # VAE
        {
            "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors",
            "path": "/models/vae/vae-ft-mse-840000.safetensors"
        },
        
        # LoRAs (example from Civitai)
        # Note: Get direct download link from Civitai
        {
            "url": "https://civitai.com/api/download/models/YOUR_MODEL_ID",
            "path": "/models/loras/your_lora.safetensors"
        },
        
        # ControlNet
        {
            "url": "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth",
            "path": "/models/controlnet/control_v11p_sd15_canny.pth"
        },
    ]
    
    # Download all models
    print("=" * 60)
    print("Starting model downloads...")
    print("=" * 60)
    
    for model in models_to_download:
        download_file(model["url"], model["path"])
    
    # Commit changes to volume
    models_volume.commit()
    
    print("=" * 60)
    print("✅ All downloads complete and committed to volume!")
    print("=" * 60)
```

### Step 2: Run the Download Function

```bash
# This runs on Modal's infrastructure (not your computer)
modal run modal_app.py::download_models
```

**What happens:**
1. Modal spins up a container
2. Downloads models from URLs directly to the volume
3. You see progress in your terminal
4. Models are committed to persistent storage
5. Container shuts down

**Advantages:**
- ✅ No local download needed
- ✅ Uses Modal's fast internet connection
- ✅ Downloads directly to volume
- ✅ Can download very large files
- ✅ Your local internet is free

## Option 2: Hugging Face Hub Integration

For Hugging Face models, use the official API:

```python
@app.function(
    image=image.pip_install("huggingface_hub"),
    volumes={"/models": models_volume},
    timeout=3600,
    secrets=[modal.Secret.from_name("huggingface-secret")],  # Optional, for private models
)
def download_from_huggingface():
    """Download models from Hugging Face Hub"""
    from huggingface_hub import hf_hub_download, snapshot_download
    import os
    import shutil
    
    # Method 1: Download single file
    def download_single_file(repo_id, filename, dest_path):
        print(f"📥 Downloading {filename} from {repo_id}")
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Download to HF cache
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            # token="your_token_here",  # If private model
        )
        
        # Copy to volume
        shutil.copy(downloaded_path, dest_path)
        print(f"✅ Saved to {dest_path}")
    
    # Method 2: Download entire repository
    def download_repo(repo_id, dest_dir):
        print(f"📥 Downloading entire repo: {repo_id}")
        
        os.makedirs(dest_dir, exist_ok=True)
        
        snapshot_download(
            repo_id=repo_id,
            local_dir=dest_dir,
            # token="your_token_here",  # If private model
        )
        print(f"✅ Downloaded repo to {dest_dir}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DOWNLOAD YOUR MODELS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Example: SDXL
    download_single_file(
        repo_id="stabilityai/stable-diffusion-xl-base-1.0",
        filename="sd_xl_base_1.0.safetensors",
        dest_path="/models/checkpoints/sd_xl_base_1.0.safetensors"
    )
    
    # Example: SD 1.5
    download_single_file(
        repo_id="runwayml/stable-diffusion-v1-5",
        filename="v1-5-pruned-emaonly.safetensors",
        dest_path="/models/checkpoints/sd_v1.5.safetensors"
    )
    
    # Example: VAE
    download_single_file(
        repo_id="stabilityai/sd-vae-ft-mse-original",
        filename="vae-ft-mse-840000-ema-pruned.safetensors",
        dest_path="/models/vae/vae-ft-mse-840000.safetensors"
    )
    
    # Example: Download entire ControlNet repo
    # download_repo(
    #     repo_id="lllyasviel/ControlNet-v1-1",
    #     dest_dir="/models/controlnet"
    # )
    
    # Commit to volume
    models_volume.commit()
    print("✅ All models downloaded and committed!")
```

Run it:
```bash
modal run modal_app.py::download_from_huggingface
```

### Setting up HF Token (for private models)

```bash
# Create secret with your HuggingFace token
modal secret create huggingface-secret HF_TOKEN=hf_your_token_here
```

## Option 3: Automated Download on First Run

Download models automatically when your app starts:

```python
@app.function(
    image=image,
    gpu=GPU_CONFIG,
    volumes={"/models": models_volume},
    container_idle_timeout=CONTAINER_IDLE_TIMEOUT,
)
@modal.asgi_app()
def fastapi_app():
    """
    Main ASGI application that auto-downloads models on first run
    """
    import sys
    import asyncio
    import logging
    import os
    import urllib.request
    
    sys.path.insert(0, "/app")
    
    # Set environment variables
    os.environ['COMFYUI_HEADLESS'] = '1'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AUTO-DOWNLOAD MODELS IF MISSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def ensure_model(url, path):
        """Download model if it doesn't exist"""
        if not os.path.exists(path):
            logging.info(f"📥 Downloading missing model: {path}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            urllib.request.urlretrieve(url, path)
            models_volume.commit()
            logging.info(f"✅ Downloaded: {path}")
        else:
            logging.info(f"✓ Model exists: {path}")
    
    # Define required models
    required_models = [
        {
            "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
            "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
        },
    ]
    
    # Check and download
    logging.info("Checking for required models...")
    for model in required_models:
        ensure_model(model["url"], model["path"])
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Start ComfyUI normally
    import main
    from comfy.cli_args import args
    
    args.headless = True
    args.listen = "0.0.0.0"
    args.port = 8000
    
    logging.info("🚀 Starting ComfyUI on Modal...")
    
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    
    loop, prompt_server, start_all = main.start_comfyui(event_loop)
    event_loop.run_until_complete(prompt_server.setup())
    
    return prompt_server.app
```

## Getting Model URLs

### From Hugging Face

1. Go to model page: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
2. Click "Files and versions"
3. Find your file (e.g., `sd_xl_base_1.0.safetensors`)
4. Right-click "download" → Copy link address

**URL format:**
```
https://huggingface.co/{user}/{repo}/resolve/main/{filename}
```

**Example:**
```
https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
```

### From Civitai

1. Go to model page
2. Click the download button
3. Get the direct download URL from your browser's download manager
4. Or use the API:

```
https://civitai.com/api/download/models/{modelVersionId}
```

You can find the `modelVersionId` in the URL or page source.

### From Other Sources

Any direct download URL works:
- Google Drive (with direct link)
- Dropbox (with direct link)
- Your own hosting
- Any CDN

## Complete Example Script

Here's a production-ready download script:

```python
@app.function(
    image=image.pip_install("tqdm", "requests"),
    volumes={"/models": models_volume},
    timeout=7200,  # 2 hours for very large downloads
)
def download_all_models():
    """
    Production-ready model downloader with progress bars and error handling
    """
    import urllib.request
    import os
    from tqdm import tqdm
    import requests
    
    class DownloadProgressBar(tqdm):
        """Progress bar for downloads"""
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)
    
    def download_with_progress(url, dest_path):
        """Download with progress bar"""
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        if os.path.exists(dest_path):
            print(f"⏭️  Already exists: {dest_path}")
            return True
        
        print(f"\n📥 Downloading: {os.path.basename(dest_path)}")
        print(f"   From: {url}")
        
        try:
            with DownloadProgressBar(unit='B', unit_scale=True, miniters=1) as t:
                urllib.request.urlretrieve(url, dest_path, reporthook=t.update_to)
            
            file_size = os.path.getsize(dest_path) / (1024**3)
            print(f"✅ Downloaded: {file_size:.2f} GB")
            return True
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MODEL DEFINITIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    models = {
        "checkpoints": [
            {
                "name": "SDXL Base 1.0",
                "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
                "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
            },
            {
                "name": "SD 1.5",
                "url": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors",
                "path": "/models/checkpoints/sd_v1.5.safetensors"
            },
        ],
        "vae": [
            {
                "name": "VAE FT MSE",
                "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors",
                "path": "/models/vae/vae-ft-mse-840000.safetensors"
            },
        ],
        "controlnet": [
            {
                "name": "ControlNet Canny",
                "url": "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth",
                "path": "/models/controlnet/control_v11p_sd15_canny.pth"
            },
        ],
        "loras": [
            # Add your LoRA URLs here
        ],
    }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DOWNLOAD ALL MODELS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("=" * 70)
    print("MODEL DOWNLOADER")
    print("=" * 70)
    
    success_count = 0
    failure_count = 0
    
    for category, model_list in models.items():
        if not model_list:
            continue
            
        print(f"\n📁 Category: {category.upper()}")
        print("-" * 70)
        
        for model in model_list:
            if download_with_progress(model["url"], model["path"]):
                success_count += 1
            else:
                failure_count += 1
    
    # Commit all downloads
    print("\n" + "=" * 70)
    print("💾 Committing to volume...")
    models_volume.commit()
    
    # Summary
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failure_count}")
    print(f"📊 Total: {success_count + failure_count}")
    print("=" * 70)
    
    if failure_count > 0:
        print("\n⚠️  Some downloads failed. Check the logs above.")
    else:
        print("\n🎉 All models downloaded successfully!")
```

## Complete Workflow

### 1. Deploy ComfyUI (no models needed)

```bash
modal deploy modal_app.py
```

Your API is live immediately!

### 2. Add Model URLs to `modal_app.py`

Edit the `download_models()` or `download_all_models()` function with your URLs.

### 3. Download Models from URLs

```bash
modal run modal_app.py::download_all_models
```

Watch the progress in your terminal. Models download directly to Modal's storage.

### 4. Verify Downloads

```bash
modal volume ls comfyui-models /checkpoints
modal volume ls comfyui-models /vae
modal volume ls comfyui-models /loras
```

### 5. Use Immediately

Models are instantly available in your deployed ComfyUI!

## Popular Model URLs

### Stable Diffusion Models

```python
models = [
    # SD 1.5
    {
        "url": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors",
        "path": "/models/checkpoints/sd_v1.5.safetensors"
    },
    
    # SDXL Base
    {
        "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
        "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
    },
    
    # SDXL Refiner
    {
        "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors",
        "path": "/models/checkpoints/sd_xl_refiner_1.0.safetensors"
    },
]
```

### VAE Models

```python
vae_models = [
    {
        "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors",
        "path": "/models/vae/vae-ft-mse-840000.safetensors"
    },
    {
        "url": "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors",
        "path": "/models/vae/sdxl_vae.safetensors"
    },
]
```

### ControlNet Models

```python
controlnet_models = [
    {
        "url": "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth",
        "path": "/models/controlnet/control_v11p_sd15_canny.pth"
    },
    {
        "url": "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.pth",
        "path": "/models/controlnet/control_v11p_sd15_openpose.pth"
    },
]
```

## Advantages of This Approach

### vs. Local Download + Upload

| Method | Your Internet | Modal Internet | Time |
|--------|---------------|----------------|------|
| **Download → Upload** | Download + Upload | - | 2× time |
| **Direct on Modal** | - | Download only | 1× time |

### Benefits

- ✅ **No local storage needed** (some models are 10GB+)
- ✅ **Faster** (Modal's datacenter internet is very fast)
- ✅ **Your internet is free** (doesn't use your bandwidth)
- ✅ **Can download multiple models in parallel**
- ✅ **Automatic retries** (add error handling)
- ✅ **Works with any URL**

## Cost Implications

### Download Costs

- **Compute time**: ~$1.10/hour (A10G) or ~$0.60/hour (T4)
- **No GPU needed**: Use CPU-only function (much cheaper)

```python
@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=3600,
    # No GPU specified = CPU only = ~$0.10/hour
)
def download_models():
    # ... download code ...
```

### Example Cost

Downloading 50GB of models:
- Time: ~30 minutes (depends on source speed)
- Cost: ~$0.05 (CPU-only function)

**vs. Local:**
- Your bandwidth: 50GB
- Your time: 30-60 minutes
- Your cost: Data overage charges (if applicable)

## Troubleshooting

### Download Fails

**Problem:** `URLError` or timeout

**Solutions:**
```python
# 1. Increase timeout
@app.function(timeout=7200)  # 2 hours

# 2. Add retries
import time
from urllib.error import URLError

def download_with_retry(url, dest_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            urllib.request.urlretrieve(url, dest_path)
            return True
        except URLError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    return False
```

### Hugging Face Rate Limits

**Problem:** 429 Too Many Requests

**Solution:** Use authentication token:

```python
from huggingface_hub import hf_hub_download

hf_hub_download(
    repo_id="...",
    filename="...",
    token="hf_your_token"  # Get from https://huggingface.co/settings/tokens
)
```

### Large Files Timeout

**Problem:** Download doesn't complete in time

**Solutions:**
```python
# 1. Use longer timeout
@app.function(timeout=7200)  # 2 hours

# 2. Download in chunks
import requests

def download_large_file(url, dest_path, chunk_size=8192):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
```

## Summary

### Quick Commands

```bash
# 1. Edit modal_app.py with your model URLs

# 2. Download models directly to Modal
modal run modal_app.py::download_models

# 3. Verify
modal volume ls comfyui-models /checkpoints

# 4. Use immediately (no redeployment needed)
```

### Key Points

- ✅ No local download required
- ✅ Works with any URL (Hugging Face, Civitai, etc.)
- ✅ Faster than local download + upload
- ✅ Doesn't use your bandwidth
- ✅ Models immediately available
- ✅ Can automate with scripts

### Recommended Workflow

1. Deploy ComfyUI first (5 minutes)
2. Add model URLs to `modal_app.py`
3. Run download function
4. Models are immediately available
5. No redeployment needed!

---

**Next Steps:**

1. Choose your download method (Option 1 is easiest)
2. Add your model URLs to `modal_app.py`
3. Run: `modal run modal_app.py::download_models`
4. Watch models download directly to Modal
5. Use them immediately!

No need to download 100GB of models to your local machine! 🚀

