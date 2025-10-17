"""
ComfyUI on Modal.com - FastAPI Version

This version uses FastAPI to wrap ComfyUI's functionality.
FastAPI is well-supported by Modal and will work reliably.

Usage:
    modal deploy modal_app_fastapi.py
"""

import modal
import os

# Modal app configuration
app = modal.App("comfyui-api")

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
        "fastapi[standard]",
    )
    # Add local files LAST - this must be the final step
    .add_local_dir(".", remote_path="/app")
)

# Persistent volumes
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)
outputs_volume = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)

# GPU and timeout configuration
GPU_CONFIG = "A10G"
TIMEOUT = 600
SCALEDOWN_WINDOW = 300


# ComfyUI Service with integrated FastAPI
@app.function(
    image=image,
    gpu=GPU_CONFIG,
    timeout=TIMEOUT,
    container_idle_timeout=SCALEDOWN_WINDOW,
    volumes={
        "/models": models_volume,
        "/outputs": outputs_volume,
    },
)
@modal.asgi_app()
def web():
    """FastAPI app that runs inside the GPU container with ComfyUI"""
    import sys
    sys.path.insert(0, "/app")
    
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uuid
    
    # Set environment variables
    os.environ['COMFYUI_HEADLESS'] = '1'
    os.environ['DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    os.environ['COMFYUI_MODEL_PATH'] = '/models'
    os.environ['COMFYUI_OUTPUT_PATH'] = '/outputs'
    
    # Import ComfyUI
    import main
    from comfy.cli_args import args
    import execution
    import comfy.model_management
    
    # Configure for headless mode
    args.headless = True
    args.disable_all_custom_nodes = True
    
    print("🚀 Initializing ComfyUI...")
    
    # Initialize ComfyUI
    event_loop, prompt_server, _ = main.start_comfyui()
    event_loop.run_until_complete(prompt_server.setup())
    
    print("✅ ComfyUI initialized successfully!")
    
    # Create FastAPI app
    web_app = FastAPI(
        title="ComfyUI API on Modal",
        description="Serverless ComfyUI API powered by Modal",
        version="1.0.0"
    )
    
    class PromptRequest(BaseModel):
        prompt: dict
        client_id: str | None = None
    
    @web_app.get("/")
    async def root():
        """API information"""
        return {
            "name": "ComfyUI on Modal",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "POST /prompt": "Queue a workflow",
                "GET /queue": "Get queue status",
                "GET /history": "Get execution history",
                "GET /history/{prompt_id}": "Get specific execution",
                "GET /system_stats": "Get system information",
                "POST /interrupt": "Interrupt execution",
            }
        }
    
    @web_app.post("/prompt")
    async def queue_prompt(request: PromptRequest):
        """Queue a ComfyUI workflow for execution"""
        try:
            prompt_id = str(uuid.uuid4())
            
            # Validate workflow
            valid = execution.validate_prompt(request.prompt)
            if not valid[0]:
                return {
                    "error": f"Invalid workflow: {valid[1]}",
                    "valid": False
                }
            
            # Queue the workflow
            number = prompt_server.number
            prompt_server.number += 1
            
            prompt_server.prompt_queue.put((number, prompt_id, request.prompt, {}, []))
            
            return {
                "prompt_id": prompt_id,
                "number": number,
                "valid": True
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/queue")
    async def get_queue():
        """Get current queue status"""
        try:
            # Use the correct method from ComfyUI's PromptQueue
            current_queue = prompt_server.prompt_queue.get_current_queue_volatile()
            return {
                "queue_running": current_queue[0],
                "queue_pending": current_queue[1]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/history")
    async def get_all_history():
        """Get all execution history"""
        try:
            history = prompt_server.prompt_queue.get_history()
            return history
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/history/{prompt_id}")
    async def get_history_by_id(prompt_id: str):
        """Get execution history for specific prompt"""
        try:
            history = prompt_server.prompt_queue.get_history(prompt_id=prompt_id)
            return history
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/system_stats")
    async def get_system_stats():
        """Get system statistics"""
        try:
            device = comfy.model_management.get_torch_device()
            device_name = comfy.model_management.get_torch_device_name(device)
            
            # Get memory info - these functions return single int by default
            vram_free = comfy.model_management.get_free_memory(device)
            vram_total = comfy.model_management.get_total_memory(device)
            
            return {
                "system": {
                    "os": "linux",
                    "comfyui_version": "0.3.62",
                    "python_version": sys.version,
                },
                "devices": [{
                    "name": device_name,
                    "type": str(device),
                    "vram_total": vram_total,
                    "vram_free": vram_free,
                }]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.post("/interrupt")
    async def interrupt_execution():
        """Interrupt current execution"""
        try:
            comfy.model_management.interrupt_current_processing()
            return {"status": "interrupted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/object_info")
    async def get_object_info():
        """Get available node information"""
        # This would need to be implemented
        # For now, return a placeholder
        return {"message": "Node information endpoint - to be implemented"}
    
    return web_app


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
    
    # Add your model download URLs here
    models = [
        # Example:
        # {
        #     "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
        #     "path": "/models/checkpoints/sd_xl_base_1.0.safetensors"
        # },
    ]
    
    for model in models:
        if not os.path.exists(model["path"]):
            print(f"📥 Downloading {os.path.basename(model['path'])}...")
            urllib.request.urlretrieve(model["url"], model["path"])
            print(f"✅ Downloaded!")
    
    models_volume.commit()
    print("✅ Setup complete!")


@app.local_entrypoint()
def main():
    """Local entrypoint"""
    print("🌐 ComfyUI Modal Deployment (FastAPI Version)")
    print("=" * 50)
    print("\nTo deploy:")
    print("  modal deploy modal_app_fastapi.py")
    print("\nYour endpoint will be:")
    print("  https://{workspace}--comfyui-api-web.modal.run")
    print("\nExample endpoints:")
    print("  GET  /                - API information")
    print("  POST /prompt          - Queue a workflow")
    print("  GET  /queue           - Get queue status")
    print("  GET  /system_stats    - Get system information")

