"""
Base image with PyTorch pre-installed.
Build this separately to cache PyTorch installation.

Usage:
    modal deploy modal/apps/base_image.py
    
This creates a reusable base image that can be referenced in the main app.
This avoids rebuilding PyTorch every time.
"""

import modal

app = modal.App("comfyui-base-image")

# Base image with PyTorch - build this once, reuse many times
base_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git", "wget", "curl", "build-essential",
        "libglib2.0-0", "libsm6", "libxext6", "libxrender-dev",
        "libgomp1", "libgl1-mesa-glx",
    )
    .pip_install(
        "torch", "torchvision", "torchaudio",
        index_url="https://download.pytorch.org/whl/cu121"
    )
)

# Export the image so it can be referenced
image = base_image

@app.function(image=base_image)
def test_pytorch():
    """Test function to verify PyTorch installation"""
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    return {"status": "ok", "pytorch": torch.__version__}

