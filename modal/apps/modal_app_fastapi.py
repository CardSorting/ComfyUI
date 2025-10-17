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
    scaledown_window=SCALEDOWN_WINDOW,
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
    args.disable_all_custom_nodes = False  # Enable core nodes
    
    print("🚀 Initializing ComfyUI...")
    
    # Initialize ComfyUI (this loads the nodes)
    event_loop, prompt_server, _ = main.start_comfyui()
    event_loop.run_until_complete(prompt_server.setup())
    
    # Check how many nodes were loaded
    import nodes
    print(f"📦 Loaded {len(nodes.NODE_CLASS_MAPPINGS)} node types")
    
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
        try:
            import nodes
            
            out = {}
            for node_class_name in nodes.NODE_CLASS_MAPPINGS:
                try:
                    node_class = nodes.NODE_CLASS_MAPPINGS[node_class_name]
                    obj_class = node_class()
                    
                    info = {}
                    info['input'] = node_class.INPUT_TYPES()
                    info['output'] = node_class.RETURN_TYPES
                    info['output_is_list'] = node_class.OUTPUT_IS_LIST if hasattr(node_class, 'OUTPUT_IS_LIST') else [False] * len(node_class.RETURN_TYPES)
                    info['output_name'] = node_class.RETURN_NAMES if hasattr(node_class, 'RETURN_NAMES') else info['output']
                    info['name'] = node_class_name
                    info['display_name'] = node_class_name
                    info['description'] = node_class.DESCRIPTION if hasattr(node_class, 'DESCRIPTION') else ''
                    info['category'] = node_class.CATEGORY if hasattr(node_class, 'CATEGORY') else 'unknown'
                    info['output_node'] = node_class.OUTPUT_NODE if hasattr(node_class, 'OUTPUT_NODE') else False
                    
                    out[node_class_name] = info
                except Exception as e:
                    print(f"Error getting info for node {node_class_name}: {e}")
                    continue
            
            return out
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return web_app


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=7200,  # 2 hours for large models
)
def download_model(url: str, category: str = "checkpoints", filename: str = None):
    """
    Download a single model from URL to the persistent volume
    
    Args:
        url: Direct download URL for the model
        category: Model category (checkpoints, vae, loras, controlnet, clip_vision, etc.)
        filename: Optional filename (auto-detected from URL if not provided)
    """
    import urllib.request
    import os
    from urllib.parse import urlparse, unquote
    
    print(f"📥 Downloading model to /models/{category}/")
    
    # Create model directory
    model_dir = f"/models/{category}"
    os.makedirs(model_dir, exist_ok=True)
    
    # Determine filename
    if not filename:
        # Try to extract filename from URL
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path))
        if not filename or filename == '':
            filename = "downloaded_model"
    
    file_path = os.path.join(model_dir, filename)
    
    # Check if already exists
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"⚠️  File already exists: {filename} ({file_size / 1024 / 1024:.1f} MB)")
        print(f"   Skipping download. Delete it first if you want to re-download.")
        return {"status": "skipped", "path": file_path, "size": file_size}
    
    # Download with progress
    print(f"🌐 Downloading: {filename}")
    print(f"   From: {url[:80]}...")
    
    def progress_hook(block_num, block_size, total_size):
        if total_size > 0:
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            mb_downloaded = downloaded / 1024 / 1024
            mb_total = total_size / 1024 / 1024
            print(f"   Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='\r')
    
    try:
        urllib.request.urlretrieve(url, file_path, reporthook=progress_hook)
        print()  # New line after progress
        
        file_size = os.path.getsize(file_path)
        print(f"✅ Downloaded: {filename} ({file_size / 1024 / 1024:.1f} MB)")
        
        # Commit volume changes
        models_volume.commit()
        print("💾 Volume committed!")
        
        return {
            "status": "success",
            "path": file_path,
            "filename": filename,
            "size": file_size,
            "category": category
        }
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        # Clean up partial download
        if os.path.exists(file_path):
            os.remove(file_path)
        raise


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=300,
)
def list_models():
    """List all models in the persistent volume"""
    import os
    
    categories = [
        "checkpoints", "vae", "loras", "controlnet", 
        "clip_vision", "unet", "embeddings", "upscale_models"
    ]
    
    print("📦 Models in persistent volume:")
    print("=" * 70)
    
    total_size = 0
    total_files = 0
    
    for category in categories:
        cat_path = f"/models/{category}"
        if os.path.exists(cat_path):
            files = os.listdir(cat_path)
            if files:
                print(f"\n📁 {category}:")
                for file in sorted(files):
                    file_path = os.path.join(cat_path, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        total_size += size
                        total_files += 1
                        print(f"   • {file} ({size / 1024 / 1024:.1f} MB)")
    
    print("\n" + "=" * 70)
    print(f"Total: {total_files} files, {total_size / 1024 / 1024 / 1024:.2f} GB")
    
    return {"total_files": total_files, "total_size_gb": total_size / 1024 / 1024 / 1024}


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=300,
)
def delete_model(category: str, filename: str):
    """Delete a model from the persistent volume"""
    import os
    
    file_path = f"/models/{category}/{filename}"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return {"status": "not_found"}
    
    size = os.path.getsize(file_path)
    os.remove(file_path)
    models_volume.commit()
    
    print(f"🗑️  Deleted: {filename} ({size / 1024 / 1024:.1f} MB)")
    
    return {"status": "deleted", "filename": filename, "size": size}


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

