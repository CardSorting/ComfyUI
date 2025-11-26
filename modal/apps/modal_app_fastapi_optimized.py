"""
ComfyUI on Modal.com - FastAPI Version (Optimized with Base Image)

This version uses a cached base image with PyTorch pre-installed,
dramatically reducing deployment time from 15-20 minutes to 2-5 minutes.

SETUP (One-time):
    1. Deploy base image: modal deploy modal/apps/base_image.py (~15-20 min)
    2. Then deploy this: modal deploy modal/apps/modal_app_fastapi_optimized.py (~2-5 min)

Usage:
    modal deploy modal/apps/modal_app_fastapi_optimized.py
"""

import modal
import os

# Modal app configuration
app = modal.App("comfyui-api")

# OPTIMIZATION: Use cached base image with PyTorch
# This reduces deployment time from 15-20 min to 2-5 min
try:
    # Try to use cached base image (fast!)
    base_image = modal.Image.from_name("comfyui-base-image", create_if_missing=False)
    print("✅ Using cached base image with PyTorch (fast deployment: ~2-5 min)")
except Exception as e:
    # Fallback: Build from scratch if base image doesn't exist
    print(f"⚠️  Base image not found: {e}")
    print("   Building from scratch (slow: ~15-20 min)")
    print("   Tip: Run 'modal deploy modal/apps/base_image.py' first for faster deployments")
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

# Build final image from base
image = (
    base_image
    # Other dependencies - fast because PyTorch is already installed
    .pip_install(
        "torchsde", "numpy>=1.25.0", "einops",
        "transformers>=4.37.2", "tokenizers>=0.13.3",
        "sentencepiece", "safetensors>=0.4.2",
        "aiohttp>=3.11.8", "yarl>=1.18.0", "pyyaml",
        "Pillow", "scipy", "tqdm", "psutil",
        "python-dotenv>=1.0.0", "alembic", "SQLAlchemy",
        "av>=14.2.0", "kornia>=0.7.1", "spandrel",
        "soundfile", "pydantic~=2.0", "pydantic-settings~=2.0",
        "fastapi[standard]", "requests",
        "boto3", "botocore",  # For Backblaze B2 S3-compatible uploads
    )
    # Add ComfyUI root directory LAST
    .add_local_dir(
        "../..", 
        remote_path="/app",
        copy=False,  # Files at runtime, faster builds
        ignore=[
            # Exclude model directories (use volumes instead)
            "models/**",
            "output/**",
            "input/**",
            "!input/example.png",
            
            # Exclude cache and build artifacts
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            ".pytest_cache/**",
            ".mypy_cache/**",
            
            # Exclude git and version control
            ".git/**",
            ".gitignore",
            ".github/**",
            
            # Exclude large binary files in custom nodes
            "custom_nodes/**/*.safetensors",
            "custom_nodes/**/*.pt",
            "custom_nodes/**/*.pth",
            "custom_nodes/**/*.bin",
            "custom_nodes/**/*.ckpt",
            "custom_nodes/**/.git/**",
            
            # Exclude test files and documentation
            "tests/**",
            "tests-unit/**",
            "docs/**",
            "*.md",
            "!README.md",
            "!modal/**/*.md",
            
            # Exclude development files
            ".vscode/**",
            ".idea/**",
            ".vs/**",
            "*.log",
            ".DS_Store",
            "venv/**",
            ".venv/**",
            
            # Exclude deployment scripts and configs
            "*.sh",
            "!modal/**/*.sh",
            "docker-compose*.yml",
            "Dockerfile*",
            "*.service",
            
            # Exclude generated files
            "*.png",
            "!input/example.png",
            "*.jpg",
            "*.jpeg",
            "openapi.yaml",
            "filtered-openapi.yaml",
            
            # Exclude environment and config files
            ".env",
            ".env.*",
            "env.template",
            "extra_model_paths.yaml",
            "civitai_models_config.json",
            "models_config.json",
            
            # Exclude database files
            "alembic_db/**",
            "alembic.ini",
            
            # Exclude other large directories
            "web/extensions/**",
            "!web/extensions/logging.js.example",
            "!web/extensions/core/**",
            "web_custom_versions/**",
            "user/**",
            "temp/**",
        ]
    )
)

# Persistent volumes
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)
outputs_volume = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)

# GPU and timeout configuration
GPU_CONFIG = "A10G"
TIMEOUT = 600
SCALEDOWN_WINDOW = 300

# Handle secrets gracefully
secrets_list = []
b2_secret = None
civitai_secret = None

try:
    b2_secret = modal.Secret.from_name("backblaze-b2-credentials", create_if_missing=False)
    secrets_list.append(b2_secret)
    print("✅ Backblaze B2 secret found")
except (Exception, KeyError, ValueError) as e:
    print(f"⚠️  Backblaze B2 secret not found: {type(e).__name__} - B2 uploads will be disabled")

try:
    civitai_secret = modal.Secret.from_name("civitai-api-key", create_if_missing=False)
    secrets_list.append(civitai_secret)
    print("✅ Civitai API key secret found")
except (Exception, KeyError, ValueError) as e:
    print(f"⚠️  Civitai API key secret not found: {type(e).__name__} - Civitai downloads will be limited")

# Import the web function from the original file
# For now, we'll use the same web function implementation
# In production, you might want to extract this to a shared module

# ComfyUI Service with integrated FastAPI
@app.function(
    image=image,
    gpu=GPU_CONFIG,
    timeout=TIMEOUT,
    scaledown_window=SCALEDOWN_WINDOW,
    volumes={
        "/models": models_volume,
        "/outputs": outputs_volume,
    },
    secrets=secrets_list if secrets_list else [],
)
@modal.asgi_app()
def web():
    """FastAPI app that runs inside the GPU container with ComfyUI"""
    # Note: This is a simplified version. For full implementation,
    # copy the web() function from modal_app_fastapi.py
    # or import it from a shared module.
    
    import sys
    sys.path.insert(0, "/app")
    sys.path.insert(0, "/app/modal/apps")
    
    from fastapi import FastAPI
    import folder_paths
    
    # Set environment variables
    os.environ['COMFYUI_HEADLESS'] = '1'
    os.environ['DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    os.environ['COMFYUI_MODEL_PATH'] = '/models'
    os.environ['COMFYUI_OUTPUT_PATH'] = '/outputs'
    
    # Configure folder paths
    folder_paths.set_output_directory('/outputs')
    folder_paths.add_model_folder_path("checkpoints", "/models/checkpoints", is_default=True)
    folder_paths.add_model_folder_path("vae", "/models/vae", is_default=True)
    folder_paths.add_model_folder_path("loras", "/models/loras", is_default=True)
    folder_paths.add_model_folder_path("controlnet", "/models/controlnet", is_default=True)
    
    # Import and initialize ComfyUI
    import main
    import execution
    from comfy.cli_args import args
    
    args.headless = True
    args.disable_all_custom_nodes = True
    args.whitelist_custom_nodes = ["websocket_image_save.py"]
    
    print("🚀 Initializing ComfyUI...")
    event_loop, prompt_server, _ = main.start_comfyui()
    event_loop.run_until_complete(prompt_server.setup())
    print("✅ ComfyUI initialized successfully!")
    
    # Create FastAPI app
    web_app = FastAPI(
        title="ComfyUI API on Modal (Optimized)",
        description="Serverless ComfyUI API with cached PyTorch base image",
        version="1.0.0"
    )
    
    @web_app.get("/")
    async def root():
        return {
            "name": "ComfyUI on Modal (Optimized)",
            "version": "1.0.0",
            "status": "running",
            "optimization": "Using cached base image with PyTorch",
            "note": "For full API, use modal_app_fastapi.py"
        }
    
    return web_app

# Note: For production use, copy all the endpoints from modal_app_fastapi.py
# This optimized version focuses on demonstrating the base image approach

