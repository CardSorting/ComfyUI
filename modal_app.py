"""
ComfyUI on Modal.com - Serverless Deployment
=============================================

This script deploys ComfyUI as a serverless application on Modal.com with GPU support.

Features:
- GPU-accelerated inference (NVIDIA A10G, A100, etc.)
- Persistent model storage
- Web API endpoints
- Auto-scaling based on demand
- Cold start optimization with cached models

Usage:
    # Test locally on Modal
    modal run modal_app.py

    # Deploy to Modal
    modal deploy modal_app.py

    # Check deployment status
    modal app list
"""

import modal
import os
import sys
import uuid
from pathlib import Path

# Modal app configuration
app = modal.App("comfyui")

# Define the container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git",
        "wget",
        "curl",
        "build-essential",
        "libglib2.0-0",
        "libsm6",
        "libxext6",
        "libxrender-dev",
        "libgomp1",
        "libgl1-mesa-glx",
    )
    # Install PyTorch with CUDA support
    .pip_install(
        "torch",
        "torchvision", 
        "torchaudio",
        index_url="https://download.pytorch.org/whl/cu121"
    )
    # Install ComfyUI dependencies (headless mode - no frontend packages)
    .pip_install(
        "torchsde",
        "numpy>=1.25.0",
        "einops",
        "transformers>=4.37.2",
        "tokenizers>=0.13.3",
        "sentencepiece",
        "safetensors>=0.4.2",
        "aiohttp>=3.11.8",
        "yarl>=1.18.0",
        "pyyaml",
        "Pillow",
        "scipy",
        "tqdm",
        "psutil",
        "python-dotenv>=1.0.0",
        "alembic",
        "SQLAlchemy",
        "av>=14.2.0",
        "kornia>=0.7.1",
        "spandrel",
        "soundfile",
        "pydantic~=2.0",
        "pydantic-settings~=2.0",
        # Note: Custom node dependencies removed for clean deployment
        # To enable custom nodes, uncomment these and set args.disable_all_custom_nodes = False
        # "opencv-python-headless",
        # "scikit-image",
        # "piexif",
        # "matplotlib",
        # "dill",
        # "ultralytics>=8.3.162",
        # "segment-anything",
    )
    # Note: SAM2 installation removed (only needed for Impact Pack custom nodes)
    # .run_commands("pip install git+https://github.com/facebookresearch/sam2")
    # Add the entire ComfyUI codebase to the image
    .add_local_dir(".", remote_path="/app")
)

# Create persistent volumes for models and outputs
# These volumes persist across function calls and deployments
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)
outputs_volume = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)

# GPU configuration - choose based on your needs (Modal 1.2.0+ uses string format):
# GPU_CONFIG = "T4"        # Budget option (~$0.60/hour)
# GPU_CONFIG = "A10G"      # Balanced option (~$1.10/hour)
# GPU_CONFIG = "A100"      # High performance (~$4.00/hour)
# GPU_CONFIG = "A100:2"    # Multi-GPU setup (2x A100)
GPU_CONFIG = "A10G"  # Default: A10G - good balance of performance and cost

# Timeout configuration (in seconds)
# For image generation, 10 minutes should be sufficient
TIMEOUT = 600

# Scaledown window - keep warm for 5 minutes to reduce cold starts
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
)
@modal.asgi_app()
def web():
    """
    Main web server that runs ComfyUI.
    This function is called once per container and creates the ComfyUI server.
    Returns a running aiohttp server.
    """
    import sys
    import asyncio
    import logging
    
    # Add app directory to Python path
    sys.path.insert(0, "/app")
    
    # Set environment variables for headless mode
    os.environ['COMFYUI_HEADLESS'] = '1'
    os.environ['DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    
    # Import ComfyUI after setting environment
    import main
    from comfy.cli_args import args
    
    # Configure ComfyUI for Modal deployment
    args.headless = True
    args.listen = "0.0.0.0"
    args.port = 8000
    args.dont_print_server = False
    args.disable_all_custom_nodes = True  # Disable custom nodes for clean deployment
    
    # Set model paths to use persistent volumes
    os.environ['COMFYUI_MODEL_PATH'] = '/models'
    os.environ['COMFYUI_OUTPUT_PATH'] = '/outputs'
    
    logging.info("🚀 Starting ComfyUI on Modal...")
    logging.info(f"📁 Models directory: /models")
    logging.info(f"📁 Outputs directory: /outputs")
    logging.info(f"🎮 GPU: {GPU_CONFIG}")
    
    # Initialize ComfyUI
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    
    loop, prompt_server, start_all = main.start_comfyui(event_loop)
    
    # Setup the server
    event_loop.run_until_complete(prompt_server.setup())
    
    # Return the aiohttp Application object
    # Modal's @asgi_app() decorator will handle starting and running it
    return prompt_server.app


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=3600,
)
def download_models():
    """
    Helper function to download and cache models to the persistent volume.
    Run this once to populate your models volume.
    
    Usage:
        modal run modal_app.py::download_models
    """
    import urllib.request
    import os
    
    print("📥 Downloading models to persistent volume...")
    
    # Create model directories
    model_dirs = [
        "/models/checkpoints",
        "/models/vae",
        "/models/loras",
        "/models/controlnet",
        "/models/clip",
        "/models/clip_vision",
        "/models/embeddings",
        "/models/upscale_models",
    ]
    
    for dir_path in model_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
    
    # Example: Download a model (uncomment and modify as needed)
    # model_url = "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"
    # model_path = "/models/checkpoints/sd_xl_base_1.0.safetensors"
    # 
    # if not os.path.exists(model_path):
    #     print(f"📥 Downloading model to {model_path}...")
    #     urllib.request.urlretrieve(model_url, model_path)
    #     print(f"✅ Downloaded {model_path}")
    # else:
    #     print(f"⏭️  Model already exists: {model_path}")
    
    # Commit changes to the volume
    models_volume.commit()
    
    print("✅ Model download complete!")
    print("\nℹ️  To use your own models, upload them using:")
    print("   modal volume put comfyui-models <local-file> <remote-path>")
    print("\nExample:")
    print("   modal volume put comfyui-models my_model.safetensors /checkpoints/my_model.safetensors")


@app.function(
    image=image,
    gpu=GPU_CONFIG,
    timeout=TIMEOUT,
    volumes={
        "/models": models_volume,
        "/outputs": outputs_volume,
    },
)
def generate_image(workflow: dict):
    """
    Generate an image using a ComfyUI workflow.
    
    This is a direct function call interface for programmatic access.
    
    Args:
        workflow: A ComfyUI workflow dict
        
    Returns:
        dict: Result containing output paths and metadata
        
    Usage:
        import modal
        
        f = modal.Function.lookup("comfyui", "generate_image")
        result = f.remote(workflow=my_workflow)
    """
    import sys
    import asyncio
    import json
    
    sys.path.insert(0, "/app")
    
    # Set environment for headless operation
    os.environ['COMFYUI_HEADLESS'] = '1'
    os.environ['DISABLE_PROGRESS_BARS'] = '1'
    
    import main
    from comfy.cli_args import args
    
    args.headless = True
    
    # Initialize ComfyUI
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    
    loop, prompt_server, start_all = main.start_comfyui(event_loop)
    
    # Queue the workflow
    prompt_id = str(uuid.uuid4())
    
    # Execute workflow using ComfyUI's execution system
    # This is a simplified example - you'll need to adapt based on your workflow structure
    from execution import validate_prompt
    
    valid = validate_prompt(workflow)
    if not valid[0]:
        return {"error": f"Invalid workflow: {valid[1]}"}
    
    # Queue and execute
    prompt_server.prompt_queue.put((0, prompt_id, workflow, {}, []))
    
    # Wait for completion (simplified - in production, use proper async handling)
    import time
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        history = prompt_server.prompt_queue.get_history(prompt_id=prompt_id)
        if prompt_id in history:
            result = history[prompt_id]
            if result.get("status", {}).get("completed", False):
                # Commit outputs to volume
                outputs_volume.commit()
                return {
                    "success": True,
                    "prompt_id": prompt_id,
                    "outputs": result.get("outputs", {}),
                }
        time.sleep(1)
    
    return {"error": "Timeout waiting for generation"}


@app.local_entrypoint()
def main():
    """
    Local entrypoint for testing the deployment.
    
    Usage:
        modal run modal_app.py
    """
    print("🌐 ComfyUI Modal Deployment")
    print("=" * 50)
    print("\nTo deploy ComfyUI to Modal:")
    print("  modal deploy modal_app.py")
    print("\nTo download models:")
    print("  modal run modal_app.py::download_models")
    print("\nTo manage volumes:")
    print("  modal volume list")
    print("  modal volume ls comfyui-models")
    print("  modal volume put comfyui-models <local> <remote>")
    print("  modal volume get comfyui-models <remote> <local>")
    print("\nAfter deployment, your API will be available at:")
    print("  https://<your-workspace>--comfyui-fastapi-app.modal.run")

