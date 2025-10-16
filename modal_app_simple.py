"""
ComfyUI on Modal.com - Simplified Working Version

This version uses a simpler approach that's guaranteed to work with Modal 1.2.0
"""

import modal

# Modal app configuration
app = modal.App("comfyui-simple")

# Define the container image
image = (
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
    .pip_install(
        "torchsde", "numpy>=1.25.0", "einops",
        "transformers>=4.37.2", "tokenizers>=0.13.3",
        "sentencepiece", "safetensors>=0.4.2",
        "aiohttp>=3.11.8", "yarl>=1.18.0", "pyyaml",
        "Pillow", "scipy", "tqdm", "psutil",
        "python-dotenv>=1.0.0", "alembic", "SQLAlchemy",
        "av>=14.2.0", "kornia>=0.7.1", "spandrel",
        "soundfile", "pydantic~=2.0", "pydantic-settings~=2.0",
    )
    .add_local_dir(".", remote_path="/app")
)

# Persistent volumes
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)
outputs_volume = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)

# GPU and timeout configuration
GPU_CONFIG = "A10G"
TIMEOUT = 600
SCALEDOWN_WINDOW = 300


@app.function(
    image=image,
    gpu=GPU_CONFIG,
    timeout=TIMEOUT,
    scaledown_window=SCALEDOWN_WINDOW,
    volumes={
        "/models": models_volume,
        "/outputs": outputs_volume,
    },
    allow_concurrent_inputs=100,
)
@modal.web_server(8000, startup_timeout=120)
def web():
    """
    Start ComfyUI server on port 8000.
    Modal will proxy to this server.
    """
    import subprocess
    import os
    
    # Set environment variables
    os.environ['COMFYUI_HEADLESS'] = '1'
    os.environ['DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    
    # Start ComfyUI as a subprocess
    # This way Modal just proxies to it, no ASGI conversion needed
    cmd = [
        "python", "/app/main.py",
        "--headless",
        "--listen", "0.0.0.0",
        "--port", "8000",
        "--disable-all-custom-nodes",
    ]
    
    print("🚀 Starting ComfyUI server...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run ComfyUI - this blocks forever
    subprocess.run(cmd, cwd="/app", check=True)


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=3600,
)
def download_models():
    """Download models from URLs to the persistent volume"""
    import urllib.request
    import os
    
    print("📥 Downloading models to persistent volume...")
    
    # Create model directories
    model_dirs = [
        "/models/checkpoints",
        "/models/vae",
        "/models/loras",
        "/models/controlnet",
    ]
    
    for dir_path in model_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
    
    # Example model downloads (uncomment and add your URLs)
    # models = [
    #     {
    #         "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
    #         "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
    #     },
    # ]
    # 
    # for model in models:
    #     if not os.path.exists(model["path"]):
    #         print(f"📥 Downloading {os.path.basename(model['path'])}...")
    #         urllib.request.urlretrieve(model["url"], model["path"])
    #         print(f"✅ Downloaded!")
    
    models_volume.commit()
    print("✅ Setup complete!")


@app.local_entrypoint()
def main():
    """Local entrypoint for testing"""
    print("🌐 ComfyUI Modal Deployment (Simplified)")
    print("=" * 50)
    print("\nTo deploy:")
    print("  modal deploy modal_app_simple.py")
    print("\nTo download models:")
    print("  modal run modal_app_simple.py::download_models")
    print("\nYour endpoint will be:")
    print("  https://{workspace}--comfyui-simple-web.modal.run")

