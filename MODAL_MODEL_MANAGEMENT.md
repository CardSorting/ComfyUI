# Model Storage and Management on Modal.com

Complete guide to storing, organizing, and managing AI models for ComfyUI on Modal.com.

## Table of Contents

1. [Understanding Modal Volumes](#understanding-modal-volumes)
2. [Model Organization Structure](#model-organization-structure)
3. [Uploading Models](#uploading-models)
4. [Downloading Models](#downloading-models)
5. [Managing Model Storage](#managing-model-storage)
6. [Best Practices](#best-practices)
7. [Storage Costs](#storage-costs)
8. [Common Workflows](#common-workflows)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)

---

## Understanding Modal Volumes

### What are Modal Volumes?

Modal Volumes are **persistent network storage** that:
- Persist across function calls and deployments
- Are shared across all containers in your Modal app
- Can be mounted at any path in your containers
- Support concurrent reads and writes
- Are billed separately from compute time

### Key Characteristics

| Feature | Details |
|---------|---------|
| **Persistence** | Data survives container restarts and redeployments |
| **Sharing** | All function invocations access the same volume |
| **Performance** | Network-attached storage (not as fast as local SSD) |
| **Durability** | Automatically replicated for reliability |
| **Capacity** | Practically unlimited (pay for what you use) |
| **Access** | Can be accessed via CLI, API, or within containers |

### Volumes in Our Setup

The ComfyUI deployment uses two volumes:

```python
# In modal_app.py
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)
outputs_volume = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)

# Mounted in containers
volumes={
    "/models": models_volume,      # AI models
    "/outputs": outputs_volume,    # Generated images/videos
}
```

#### comfyui-models Volume
**Purpose:** Store all AI models (checkpoints, LoRAs, VAEs, etc.)
**Mount Point:** `/models`
**Typical Size:** 10-500GB depending on your model collection

#### comfyui-outputs Volume
**Purpose:** Store generated outputs (images, videos)
**Mount Point:** `/outputs`
**Typical Size:** Growing over time based on usage

---

## Model Organization Structure

### Recommended Directory Structure

```
/models/
├── checkpoints/              # Main model checkpoints
│   ├── sd_v1.5.safetensors
│   ├── sdxl_base_1.0.safetensors
│   ├── flux_dev.safetensors
│   └── realistic_v5.safetensors
│
├── vae/                      # VAE models
│   ├── vae-ft-mse-840000.safetensors
│   └── sdxl_vae.safetensors
│
├── loras/                    # LoRA models
│   ├── detail_tweaker.safetensors
│   ├── lighting_lora.safetensors
│   └── style/                # Organize by category
│       ├── anime_style.safetensors
│       └── realistic_style.safetensors
│
├── controlnet/               # ControlNet models
│   ├── control_v11p_sd15_canny.pth
│   ├── control_v11p_sd15_openpose.pth
│   └── sdxl/
│       └── controlnet-openpose-sdxl.safetensors
│
├── clip/                     # CLIP models
│   └── clip_vision_g.safetensors
│
├── clip_vision/              # CLIP Vision models
│   └── vision_model.safetensors
│
├── embeddings/               # Textual Inversion embeddings
│   ├── EasyNegative.pt
│   └── BadDream.pt
│
├── upscale_models/           # Upscaler models
│   ├── RealESRGAN_x4plus.pth
│   ├── ESRGAN_4x.pth
│   └── ultrasharp_4x.pth
│
├── ipadapter/                # IP-Adapter models
│   └── ip-adapter_sd15.bin
│
├── unet/                     # Standalone UNet models
│   └── flux_unet.safetensors
│
└── diffusion_models/         # Other diffusion models
    └── model.safetensors
```

### Why This Structure?

- ✅ **ComfyUI Compatible**: Matches default ComfyUI paths
- ✅ **Easy Navigation**: Clear categories
- ✅ **Scalable**: Can add subcategories as needed
- ✅ **Standard**: Familiar to ComfyUI users

---

## Uploading Models

### Method 1: Upload from Local Machine (Recommended)

#### Single File Upload

```bash
# Basic syntax
modal volume put <volume-name> <local-path> <remote-path>

# Examples
modal volume put comfyui-models ./sd_xl_base_1.0.safetensors /checkpoints/sd_xl_base_1.0.safetensors
modal volume put comfyui-models ./my_lora.safetensors /loras/my_lora.safetensors
modal volume put comfyui-models ./vae.safetensors /vae/sdxl_vae.safetensors
```

#### Directory Upload

```bash
# Upload entire directory
modal volume put comfyui-models ./my_checkpoints /checkpoints

# Upload with structure preserved
modal volume put comfyui-models ./my_models/loras /loras
```

#### Bulk Upload Script

```bash
#!/bin/bash
# upload_models.sh - Upload multiple models at once

# Checkpoints
modal volume put comfyui-models ./models/sd_v1.5.safetensors /checkpoints/sd_v1.5.safetensors
modal volume put comfyui-models ./models/sdxl_base.safetensors /checkpoints/sdxl_base.safetensors

# LoRAs
modal volume put comfyui-models ./loras /loras

# VAEs
modal volume put comfyui-models ./vae /vae

echo "✅ Upload complete!"
```

#### Upload with Progress

```bash
# For large files, you'll see progress
modal volume put comfyui-models large_model.safetensors /checkpoints/large_model.safetensors

# Example output:
# Uploading large_model.safetensors: 100%|████████| 6.46GB/6.46GB [02:15<00:00, 47.8MB/s]
```

### Method 2: Download Directly in Modal Container

Edit the `download_models()` function in `modal_app.py`:

```python
@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=3600,
)
def download_models():
    """
    Download models directly to the Modal volume
    """
    import urllib.request
    import os
    from tqdm import tqdm
    
    def download_file(url, dest_path):
        """Download with progress bar"""
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        if os.path.exists(dest_path):
            print(f"⏭️  Already exists: {dest_path}")
            return
        
        print(f"📥 Downloading: {os.path.basename(dest_path)}")
        urllib.request.urlretrieve(url, dest_path)
        print(f"✅ Downloaded: {dest_path}")
    
    # Define your models
    models = [
        {
            "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
            "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
        },
        {
            "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_vae.safetensors",
            "path": "/models/vae/sdxl_vae.safetensors"
        },
    ]
    
    # Download all models
    for model in models:
        download_file(model["url"], model["path"])
    
    # Commit changes to volume
    models_volume.commit()
    print("✅ All models downloaded and committed!")

# Run it
# modal run modal_app.py::download_models
```

Then run:
```bash
modal run modal_app.py::download_models
```

### Method 3: Download from Hugging Face

Using the Hugging Face Hub library:

```python
@app.function(
    image=image.pip_install("huggingface_hub"),
    volumes={"/models": models_volume},
    timeout=3600,
)
def download_from_huggingface():
    """Download models from Hugging Face Hub"""
    from huggingface_hub import hf_hub_download
    import os
    
    models = [
        {
            "repo": "stabilityai/stable-diffusion-xl-base-1.0",
            "filename": "sd_xl_base_1.0.safetensors",
            "dest": "/models/checkpoints/sd_xl_base_1.0.safetensors"
        },
    ]
    
    for model in models:
        print(f"📥 Downloading {model['filename']} from {model['repo']}")
        
        # Download to cache
        downloaded_path = hf_hub_download(
            repo_id=model["repo"],
            filename=model["filename"]
        )
        
        # Copy to volume
        import shutil
        os.makedirs(os.path.dirname(model["dest"]), exist_ok=True)
        shutil.copy(downloaded_path, model["dest"])
        print(f"✅ Saved to {model['dest']}")
    
    models_volume.commit()
    print("✅ All models downloaded!")
```

### Method 4: Pre-bake Models into Container Image

For frequently used models, bake them into the container image:

```python
def download_models_to_image():
    """Function runs during image build"""
    import urllib.request
    import os
    
    os.makedirs("/models/checkpoints", exist_ok=True)
    
    # Download model during image build
    url = "https://huggingface.co/.../model.safetensors"
    urllib.request.urlretrieve(url, "/models/checkpoints/model.safetensors")

# Add to image definition
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(...)
    .pip_install(...)
    .run_function(download_models_to_image)  # Bake models into image
)
```

**Pros:**
- ✅ Zero cold start time for model loading
- ✅ Models always available

**Cons:**
- ❌ Larger image size
- ❌ Slower image builds
- ❌ Less flexible (requires rebuild to update models)

---

## Downloading Models

### List Volume Contents

```bash
# List root directory
modal volume ls comfyui-models

# List specific directory
modal volume ls comfyui-models /checkpoints
modal volume ls comfyui-models /loras

# List with details (sizes, dates)
modal volume ls comfyui-models /checkpoints -l
```

### Download Single File

```bash
# Basic syntax
modal volume get <volume-name> <remote-path> <local-path>

# Examples
modal volume get comfyui-models /checkpoints/model.safetensors ./model.safetensors
modal volume get comfyui-models /loras/my_lora.safetensors ./my_lora.safetensors
```

### Download Directory

```bash
# Download entire directory
modal volume get comfyui-models /checkpoints ./local_checkpoints
modal volume get comfyui-models /loras ./local_loras

# Download with structure preserved
modal volume get comfyui-models /models ./backup_models
```

### Backup Your Models

```bash
#!/bin/bash
# backup_models.sh - Backup all models from Modal

BACKUP_DIR="./model_backup_$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "📦 Backing up models to $BACKUP_DIR"

# Backup each category
modal volume get comfyui-models /checkpoints "$BACKUP_DIR/checkpoints"
modal volume get comfyui-models /loras "$BACKUP_DIR/loras"
modal volume get comfyui-models /vae "$BACKUP_DIR/vae"
modal volume get comfyui-models /controlnet "$BACKUP_DIR/controlnet"

echo "✅ Backup complete!"
```

---

## Managing Model Storage

### View Storage Usage

```bash
# List all volumes
modal volume list

# View volume details
modal volume ls comfyui-models

# Check specific directory sizes (run in container)
modal shell modal_app.py
# Then in the shell:
du -sh /models/*
du -sh /models/checkpoints/*
```

### Delete Models

```bash
# Delete single file
modal volume rm comfyui-models /checkpoints/old_model.safetensors

# Delete directory
modal volume rm comfyui-models /loras/unused --recursive

# Be careful - deletions are permanent!
```

### Rename/Move Models

Modal doesn't have a direct rename command, so use copy + delete:

```bash
# Download, upload to new location, delete old
modal volume get comfyui-models /checkpoints/old_name.safetensors ./temp.safetensors
modal volume put comfyui-models ./temp.safetensors /checkpoints/new_name.safetensors
modal volume rm comfyui-models /checkpoints/old_name.safetensors
rm ./temp.safetensors
```

Or do it in a Modal function:

```python
@app.function(volumes={"/models": models_volume})
def rename_model(old_path: str, new_path: str):
    """Rename a model file"""
    import shutil
    import os
    
    full_old = f"/models{old_path}"
    full_new = f"/models{new_path}"
    
    os.makedirs(os.path.dirname(full_new), exist_ok=True)
    shutil.move(full_old, full_new)
    models_volume.commit()
    print(f"✅ Renamed {old_path} → {new_path}")
```

### Organize Existing Models

```python
@app.function(volumes={"/models": models_volume})
def organize_models():
    """Organize models into subdirectories"""
    import os
    import shutil
    
    # Example: Move style LoRAs into subdirectory
    lora_dir = "/models/loras"
    style_dir = f"{lora_dir}/style"
    
    os.makedirs(style_dir, exist_ok=True)
    
    # Move files matching pattern
    for file in os.listdir(lora_dir):
        if "style" in file.lower() and file.endswith(".safetensors"):
            src = os.path.join(lora_dir, file)
            dst = os.path.join(style_dir, file)
            if os.path.isfile(src):
                shutil.move(src, dst)
                print(f"Moved {file} → style/")
    
    models_volume.commit()
    print("✅ Organization complete!")
```

### Clean Up Unused Models

```python
@app.function(volumes={"/models": models_volume})
def list_large_models():
    """Find large model files"""
    import os
    
    models_dir = "/models"
    large_files = []
    
    for root, dirs, files in os.walk(models_dir):
        for file in files:
            path = os.path.join(root, file)
            size = os.path.getsize(path)
            size_gb = size / (1024**3)
            
            if size_gb > 5:  # Files larger than 5GB
                large_files.append((path, size_gb))
    
    # Sort by size
    large_files.sort(key=lambda x: x[1], reverse=True)
    
    print("📊 Large Model Files:")
    for path, size in large_files:
        print(f"  {size:.2f} GB - {path}")
```

---

## Best Practices

### 1. Use Descriptive Names

```bash
# ❌ Bad
modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors

# ✅ Good
modal volume put comfyui-models model.safetensors /checkpoints/sdxl_base_1.0_fp16.safetensors
```

### 2. Organize by Type and Version

```
/models/
├── checkpoints/
│   ├── sd15/
│   │   ├── v1-5-pruned-emaonly.safetensors
│   │   └── realistic_v5.safetensors
│   └── sdxl/
│       ├── sd_xl_base_1.0.safetensors
│       └── sd_xl_refiner_1.0.safetensors
```

### 3. Keep Model Metadata

Create a `models_index.json` file:

```json
{
  "checkpoints": {
    "sd_xl_base_1.0.safetensors": {
      "source": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
      "size": "6.46 GB",
      "uploaded": "2024-10-15",
      "hash": "31e35c80fc4829d14f90153f4c74cd59c90b779f",
      "notes": "Base SDXL model, good for general use"
    }
  },
  "loras": {
    "detail_tweaker.safetensors": {
      "source": "civitai.com/models/12345",
      "size": "144 MB",
      "strength_range": "0.5-1.0",
      "notes": "Enhances fine details"
    }
  }
}
```

Upload it:
```bash
modal volume put comfyui-models models_index.json /models_index.json
```

### 4. Use Symlinks for Duplicates

If you need the same model in multiple locations:

```python
@app.function(volumes={"/models": models_volume})
def create_symlink(source: str, link: str):
    """Create symlink instead of duplicating"""
    import os
    
    full_source = f"/models{source}"
    full_link = f"/models{link}"
    
    os.symlink(full_source, full_link)
    models_volume.commit()
```

### 5. Regular Backups

```bash
# Weekly backup script
0 0 * * 0 /path/to/backup_models.sh
```

### 6. Document Your Collection

Keep a README in your volume:

```bash
cat > models_readme.txt << EOF
# ComfyUI Models Collection

Last Updated: 2024-10-16

## Checkpoints
- sd_xl_base_1.0.safetensors: Main SDXL model
- realistic_v5.safetensors: Photorealistic SD 1.5

## LoRAs
- detail_tweaker.safetensors: Detail enhancement (use at 0.7)
- lighting_lora.safetensors: Lighting control (use at 0.5-0.8)

## Notes
- All SDXL models require sdxl_vae.safetensors
- Keep total storage under 500GB to manage costs
EOF

modal volume put comfyui-models models_readme.txt /README.txt
```

### 7. Test Models Before Full Upload

```bash
# Upload to a test directory first
modal volume put comfyui-models model.safetensors /test/model.safetensors

# Test in ComfyUI

# If good, move to production
# (download, re-upload to correct location, delete test)
```

---

## Storage Costs

### Modal Storage Pricing

| Item | Cost |
|------|------|
| Storage | **$0.10 per GB-month** |
| Data Transfer (egress) | Included in compute costs |
| API Calls | Free |

### Cost Examples

| Storage Size | Monthly Cost |
|--------------|--------------|
| 10 GB (small collection) | $1.00 |
| 50 GB (medium collection) | $5.00 |
| 100 GB (large collection) | $10.00 |
| 500 GB (very large) | $50.00 |
| 1 TB (extensive) | $100.00 |

### Example Model Sizes

| Model Type | Typical Size | 100 Models Cost |
|------------|--------------|-----------------|
| SD 1.5 Checkpoint | 2-4 GB | $20-40 |
| SDXL Checkpoint | 6-7 GB | $60-70 |
| LoRA | 50-200 MB | $0.50-2.00 |
| VAE | 300-500 MB | $3.00-5.00 |
| ControlNet | 1-2 GB | $10-20 |

### Cost Optimization Tips

1. **Remove Duplicates**
   ```bash
   # Find duplicate files (run in container)
   find /models -type f -exec md5sum {} + | sort | uniq -w32 -d
   ```

2. **Use FP16 Models When Possible**
   - FP32 model: 6.46 GB
   - FP16 model: 3.23 GB
   - **Savings: 50%**

3. **Compress Unused Models**
   ```bash
   # Archive old models
   tar -czf old_models.tar.gz /models/archive/
   # Upload compressed version
   modal volume put comfyui-models old_models.tar.gz /archives/old_models.tar.gz
   ```

4. **Delete Unnecessary Files**
   - Remove old versions after testing new ones
   - Delete unused LoRAs
   - Remove preview images (ComfyUI generates these)

5. **Monitor Usage**
   ```bash
   # Check volume size regularly
   modal volume ls comfyui-models -l
   ```

### Storage vs Compute Trade-offs

| Scenario | Storage Cost | Compute Cost | Total Cost |
|----------|--------------|--------------|------------|
| **Store all models** | $50/mo | $20/mo | $70/mo |
| **Download on-demand** | $10/mo | $40/mo | $50/mo |
| **Hybrid approach** | $25/mo | $25/mo | $50/mo |

**Recommendation:** Store frequently-used models, download others on-demand.

---

## Common Workflows

### Workflow 1: Initial Setup

```bash
# 1. Create local directory structure
mkdir -p models/{checkpoints,loras,vae,controlnet}

# 2. Download models to local
# (download your models)

# 3. Upload to Modal
modal volume put comfyui-models ./models/checkpoints /checkpoints
modal volume put comfyui-models ./models/loras /loras
modal volume put comfyui-models ./models/vae /vae
modal volume put comfyui-models ./models/controlnet /controlnet

# 4. Verify
modal volume ls comfyui-models /checkpoints
```

### Workflow 2: Adding New Model

```bash
# 1. Download model locally
wget https://example.com/new_model.safetensors

# 2. Upload to Modal
modal volume put comfyui-models new_model.safetensors /checkpoints/new_model.safetensors

# 3. Test in ComfyUI workflow

# 4. Document in your index
echo "new_model.safetensors - Added 2024-10-16" >> model_log.txt
```

### Workflow 3: Updating Model

```bash
# 1. Backup old version
modal volume get comfyui-models /checkpoints/model.safetensors ./backup/model_v1.safetensors

# 2. Upload new version
modal volume put comfyui-models model_v2.safetensors /checkpoints/model.safetensors

# 3. Test new version

# 4. If good, delete backup. If bad, restore:
modal volume put comfyui-models ./backup/model_v1.safetensors /checkpoints/model.safetensors
```

### Workflow 4: Sharing Models Between Projects

```python
# Option 1: Use same volume in multiple apps
app1 = modal.App("comfyui-production")
app2 = modal.App("comfyui-staging")

# Both use same models volume
shared_models = modal.Volume.from_name("comfyui-models")

@app1.function(volumes={"/models": shared_models})
def prod_function():
    pass

@app2.function(volumes={"/models": shared_models})
def staging_function():
    pass
```

### Workflow 5: Model Version Control

```bash
# Use version tags in filenames
/checkpoints/
├── sdxl_base_1.0.safetensors
├── sdxl_base_0.9.safetensors
└── current -> sdxl_base_1.0.safetensors  # symlink

# Or use dated directories
/checkpoints/
├── 2024-10/
│   └── model.safetensors
└── 2024-11/
    └── model.safetensors
```

---

## Troubleshooting

### Issue: Model Not Found

**Symptom:** ComfyUI says "model not found"

**Diagnosis:**
```bash
# Check if file exists
modal volume ls comfyui-models /checkpoints

# Check exact filename
modal volume ls comfyui-models /checkpoints -l
```

**Solution:**
- Verify filename matches exactly (case-sensitive)
- Check path is correct (`/checkpoints/` not `/checkpoint/`)
- Ensure volume is mounted in container

### Issue: Upload Fails

**Symptom:** Upload times out or fails

**Solutions:**
```bash
# 1. Check file size
ls -lh model.safetensors

# 2. For very large files, increase timeout
export MODAL_TIMEOUT=3600
modal volume put comfyui-models large_model.safetensors /checkpoints/large_model.safetensors

# 3. Split large uploads
split -b 1G large_model.safetensors part_
# Upload parts separately and reassemble in container
```

### Issue: Volume Out of Space

**Symptom:** "No space left" error

**Diagnosis:**
```python
@app.function(volumes={"/models": models_volume})
def check_storage():
    import os
    total = 0
    for root, dirs, files in os.walk("/models"):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    print(f"Total: {total / (1024**3):.2f} GB")
```

**Solutions:**
1. Delete unnecessary files
2. Compress old models
3. Move to separate volume

### Issue: Slow Model Loading

**Symptom:** Long wait times loading models

**Causes:**
- Network volume read latency
- Large model files
- Multiple models loaded simultaneously

**Solutions:**
```python
# 1. Pre-warm models in container startup
@app.function(
    volumes={"/models": models_volume},
    # Cache loaded models in container
    container_idle_timeout=600,
)
def optimized_function():
    pass

# 2. Use smaller model formats (FP16, quantized)

# 3. Bake frequently-used models into image (see Method 4 above)
```

### Issue: Model Corruption

**Symptom:** Model fails to load or generates errors

**Diagnosis:**
```bash
# Check file integrity
modal volume get comfyui-models /checkpoints/model.safetensors ./test_model.safetensors

# Compare checksums
# (if you have original checksum)
sha256sum test_model.safetensors
```

**Solutions:**
1. Re-upload model
2. Download from original source
3. Verify source file integrity before upload

### Issue: Permission Errors

**Symptom:** Cannot write to volume

**Solution:**
```python
# Ensure volume.commit() is called after writes
@app.function(volumes={"/models": models_volume})
def write_model():
    # ... write files ...
    models_volume.commit()  # Required!
```

---

## Advanced Topics

### A. Automated Model Syncing

```python
@app.function(
    schedule=modal.Period(days=1),  # Run daily
    volumes={"/models": models_volume},
)
def sync_models_daily():
    """Sync models from external source daily"""
    import requests
    
    # Fetch model list from your API
    response = requests.get("https://api.example.com/models")
    models = response.json()
    
    for model in models:
        local_path = f"/models/checkpoints/{model['filename']}"
        if not os.path.exists(local_path):
            print(f"Downloading new model: {model['filename']}")
            urllib.request.urlretrieve(model['url'], local_path)
    
    models_volume.commit()
```

### B. Model Version Management System

```python
import json
from datetime import datetime

@app.function(volumes={"/models": models_volume})
def register_model(filepath: str, metadata: dict):
    """Register model with version control"""
    
    registry_path = "/models/model_registry.json"
    
    # Load existing registry
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {}
    
    # Add new entry
    registry[filepath] = {
        "uploaded": datetime.now().isoformat(),
        "size": os.path.getsize(f"/models{filepath}"),
        "metadata": metadata
    }
    
    # Save registry
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    models_volume.commit()
```

### C. Lazy Model Loading

```python
class ModelCache:
    """Cache models in memory across function calls"""
    _cache = {}
    
    @classmethod
    def load_model(cls, path: str):
        if path not in cls._cache:
            # Load model from volume
            cls._cache[path] = load_model_function(path)
        return cls._cache[path]

@app.function(volumes={"/models": models_volume})
def use_cached_model(model_path: str):
    model = ModelCache.load_model(model_path)
    # Use model...
```

### D. Model Sharding for Large Models

```python
@app.function(volumes={"/models": models_volume})
def shard_large_model(model_path: str, num_shards: int = 4):
    """Split large model into shards"""
    import os
    
    full_path = f"/models{model_path}"
    file_size = os.path.getsize(full_path)
    shard_size = file_size // num_shards
    
    with open(full_path, 'rb') as f:
        for i in range(num_shards):
            shard_path = f"{full_path}.shard{i}"
            with open(shard_path, 'wb') as shard:
                shard.write(f.read(shard_size))
    
    models_volume.commit()

@app.function(volumes={"/models": models_volume})
def load_sharded_model(model_path: str):
    """Reconstruct model from shards"""
    import glob
    
    # Find all shards
    shards = sorted(glob.glob(f"/models{model_path}.shard*"))
    
    # Reconstruct
    with open(f"/models{model_path}", 'wb') as output:
        for shard in shards:
            with open(shard, 'rb') as f:
                output.write(f.read())
    
    return f"/models{model_path}"
```

### E. Cross-Volume Model Sharing

```python
# Share models between different Modal workspaces
import modal

# In workspace A
models_a = modal.Volume.from_name("workspace-a-models")

# In workspace B - reference workspace A's volume
# Note: This requires appropriate permissions
models_shared = modal.Volume.from_name("workspace-a-models")

@app.function(volumes={"/models": models_shared})
def use_shared_models():
    # Access models from workspace A
    pass
```

---

## Summary

### Quick Reference Commands

```bash
# Upload
modal volume put comfyui-models <local> <remote>

# Download
modal volume get comfyui-models <remote> <local>

# List
modal volume ls comfyui-models <path>

# Delete
modal volume rm comfyui-models <remote-path>

# List all volumes
modal volume list
```

### Storage Best Practices Checklist

- [ ] Use descriptive, consistent file names
- [ ] Organize models by type and version
- [ ] Keep model metadata/documentation
- [ ] Regular backups of important models
- [ ] Monitor storage costs monthly
- [ ] Remove duplicates and unused models
- [ ] Use FP16 models when possible
- [ ] Test models before production use
- [ ] Document model sources and checksums
- [ ] Set up automated syncing for updates

### Cost Management Checklist

- [ ] Current storage: ____ GB
- [ ] Monthly cost: $____
- [ ] Last cleanup: ________
- [ ] Models to remove: ________
- [ ] Using FP16 where possible: Yes/No
- [ ] Automated backups configured: Yes/No

---

## Additional Resources

- **Modal Volumes Documentation**: https://modal.com/docs/guide/volumes
- **ComfyUI Model Documentation**: https://github.com/comfyanonymous/ComfyUI/wiki
- **Model Sources**:
  - Hugging Face: https://huggingface.co/models
  - Civitai: https://civitai.com
  - Model repositories: Check ComfyUI Discord

## Questions or Issues?

- **Modal Support**: https://discord.gg/modal
- **Check Main Guide**: [MODAL_DEPLOYMENT_GUIDE.md](MODAL_DEPLOYMENT_GUIDE.md)
- **Storage Issues**: Run `modal shell modal_app.py` and investigate

---

*Last updated: October 16, 2025*
*Part of the ComfyUI on Modal.com deployment guide*

