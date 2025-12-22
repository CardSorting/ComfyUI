"""
ComfyUI on Modal.com - FastAPI Version

Serverless ComfyUI API deployment using Modal and FastAPI.

Features:
- GPU-accelerated image generation (NVIDIA A10G)
- Persistent model storage via Modal Volumes
- Optional Backblaze B2 integration for image uploads
- Optional Civitai API integration for model downloads

Usage:
    modal deploy modal/apps/modal_app_fastapi.py
"""

import modal
import os
from pathlib import Path
from typing import Tuple, Optional

# Modal app configuration
app = modal.App("comfyui-api-debug-fix-v4")

# Get the absolute path to ComfyUI root (parent of modal/apps/)
SCRIPT_DIR = Path(__file__).parent.resolve()
COMFYUI_ROOT = SCRIPT_DIR.parent.parent


# Build the container image
# IMPORTANT: All image building happens at deploy time, so we use absolute paths
base_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git", "wget", "curl", "build-essential",
        "libglib2.0-0", "libsm6", "libxext6", "libxrender-dev",
        "libgomp1", "libgl1-mesa-glx",
    )
    # PyTorch installation - this is the slowest step (~10-15 minutes)
    .pip_install(
        "torch", "torchvision", "torchaudio",
        index_url="https://download.pytorch.org/whl/cu121"
    )
)

# Build final image with other dependencies
image = (
    base_image
    # Other dependencies - much faster (~2-3 minutes)
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
    # Add ComfyUI root directory using absolute path
    # Use copy=False to add files at runtime (not baked into image) - faster builds
    # Add ComfyUI root directory using absolute path
    # Use copy=False to add files at runtime (not baked into image) - faster builds
    .add_local_dir(
        str(COMFYUI_ROOT), 
        remote_path="/root/comfy_app",
        copy=False,
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

# Persistent volumes - these are resolved at deploy time, which is fine
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=True)
outputs_volume = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)

# GPU and timeout configuration
GPU_CONFIG = "A10G"
TIMEOUT = 600  # Function execution timeout (10 minutes)
SCALEDOWN_WINDOW = 300  # Container idle time before scaling down (5 minutes)


def _get_secrets_list():
    """
    Get secrets lazily - only called when actually needed.
    This prevents issues with secret resolution during module import.
    """
    secrets = []
    
    try:
        # b2_secret = modal.Secret.from_name("backblaze-b2-credentials")
        # secrets.append(b2_secret)
        pass
    except Exception:
        pass  # Secret doesn't exist
    
    try:
        civitai_secret = modal.Secret.from_name("civitai-api-key")
        secrets.append(civitai_secret)
    except Exception:
        pass  # Secret doesn't exist
    
    return secrets


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
    secrets=_get_secrets_list(),
)
@modal.asgi_app()
def web_v3():
    """FastAPI app that runs inside the GPU container with ComfyUI"""
    import sys
    import os
    import asyncio
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, FileResponse
    from pydantic import BaseModel
    import uuid
    import json
    import time
    from contextlib import asynccontextmanager

    sys.path.insert(0, "/root/comfy_app")  # ComfyUI root
    sys.path.insert(0, "/root/comfy_app/modal/apps")  # For b2_storage module
    os.chdir("/root/comfy_app") # Ensure we are in the root directory

    # Global variables to hold ComfyUI state
    comfyui_state = {
        "prompt_server": None,
        "event_loop": None,
        "b2_storage": None
    }

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Lifespan events for FastAPI.
        Initializes ComfyUI on startup using the correct asyncio loop.
        """
        print("🚀 Starting ComfyUI lifespan...")
        
        # Reload volumes to ensure we see the latest data
        print("🔄 Reloading volumes to get latest data...")
        try:
            models_volume.reload()
            outputs_volume.reload()
            print("✅ Volumes reloaded")
        except Exception as e:
            print(f"⚠️ Error reloading volumes: {e}")

        # Set environment variables for headless mode
        os.environ['COMFYUI_HEADLESS'] = '1'
        os.environ['DISABLE_PROGRESS_BARS'] = '1'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['DO_NOT_TRACK'] = '1'
        os.environ['COMFYUI_MODEL_PATH'] = '/models'
        os.environ['COMFYUI_OUTPUT_PATH'] = '/outputs'
        
        # Import folder_paths FIRST to configure paths before anything else loads
        import folder_paths
        from comfy.cli_args import args
        
        # Configure folder paths to use the Modal volumes BEFORE importing main
        folder_paths.set_output_directory('/outputs')
        
        # Ensure model directories exist before adding paths
        model_dirs = {
            "checkpoints": "/models/checkpoints",
            "vae": "/models/vae",
            "loras": "/models/loras",
            "controlnet": "/models/controlnet",
            "clip_vision": "/models/clip_vision",
            "upscale_models": "/models/upscale_models",
            "embeddings": "/models/embeddings",
            "unet": "/models/unet",
            "text_encoders": "/models/text_encoders",
            "clip": "/models/clip"
        }
        
        for category, path in model_dirs.items():
            os.makedirs(path, exist_ok=True)
            folder_paths.add_model_folder_path(category, path, is_default=True)
        
        # Also register text_encoders as clip source
        folder_paths.add_model_folder_path("clip", "/models/text_encoders")

        checkpoint_paths = folder_paths.get_folder_paths('checkpoints')
        print(f"📁 Configured model paths: {checkpoint_paths}")

        # Clear the filename cache BEFORE importing ComfyUI modules
        if hasattr(folder_paths, 'filename_list_cache'):
            folder_paths.filename_list_cache.clear()
            print("🔄 Cleared filename cache before ComfyUI init")
        
        if hasattr(folder_paths, 'cache_helper'):
            folder_paths.cache_helper.clear()
            print("🔄 Cleared cache helper before ComfyUI init")
        
        # Touch the checkpoint directory to update its modification time
        for path in checkpoint_paths:
            if os.path.exists(path):
                try:
                    os.utime(path, None)  # Update access/modification time
                    print(f"🔄 Updated modification time for {path}")
                except Exception as e:
                    print(f"⚠️  Could not update mtime for {path}: {e}")

        # NOW import ComfyUI modules
        import main
        import execution
        import comfy.model_management
        
        # Configure for headless mode
        args.headless = True
        args.disable_all_custom_nodes = True
        args.whitelist_custom_nodes = ["websocket_image_save.py"]
        
        print("🚀 Initializing ComfyUI...")
        
        # Helper to initialize ComfyUI manually to avoid run_until_complete error
        print("🚀 Initializing ComfyUI manually...")
        
        # Import dependencies
        import server
        import nodes
        import main
        import threading
        
        loop = asyncio.get_running_loop()
        print(f"ℹ️  Using running event loop: {loop}")
        
        # Initialize PromptServer with running loop
        prompt_server = server.PromptServer(loop)
        
        # Initialize nodes (Async) - Replaces loop.run_until_complete(nodes.init_extra_nodes(...))
        print("⏳ Initializing extra nodes...")
        await nodes.init_extra_nodes(
            init_custom_nodes=(not args.disable_all_custom_nodes) or len(args.whitelist_custom_nodes) > 0,
            init_api_nodes=not args.disable_api_nodes
        )
        print("✅ Nodes initialized")
        
        # Start the prompt worker thread (from main.py start_comfyui)
        threading.Thread(target=main.prompt_worker, daemon=True, args=(prompt_server.prompt_queue, prompt_server,)).start()
        print("✅ Worker thread started")
        
        # Update state
        comfyui_state["prompt_server"] = prompt_server
        comfyui_state["event_loop"] = loop
        
        # Explicitly setup the server
        await prompt_server.setup()
        
        # Check how many nodes were loaded
        import nodes
        print(f"📦 Loaded {len(nodes.NODE_CLASS_MAPPINGS)} node types")
        
        # Force rescan of checkpoints by clearing ALL caches again
        if hasattr(folder_paths, 'filename_list_cache'):
            if 'checkpoints' in folder_paths.filename_list_cache:
                del folder_paths.filename_list_cache['checkpoints']
            print("🔄 Removed checkpoints from filename cache")
        
        if hasattr(folder_paths, 'cache_helper'):
            folder_paths.cache_helper.clear()
            print("🔄 Cleared cache helper")
        
        # Monkey-patch CheckpointLoaderSimple to always return fresh list
        try:
             # Force scan
            checkpoint_list = folder_paths.get_filename_list("checkpoints")
            print(f"📋 Rescanned checkpoints: found {len(checkpoint_list)} models")
            
            from nodes import CheckpointLoaderSimple

            @classmethod
            def dynamic_input_types(cls):
                # Always get fresh list, bypassing cache
                folder_paths.filename_list_cache.pop('checkpoints', None)
                fresh_list = folder_paths.get_filename_list("checkpoints")
                return {
                    "required": {
                        "ckpt_name": (fresh_list, {"tooltip": "The name of the checkpoint (model) to load."}),
                    }
                }
            
            CheckpointLoaderSimple.INPUT_TYPES = dynamic_input_types
            print(f"✅ Patched CheckpointLoaderSimple.INPUT_TYPES")
        except Exception as e:
            print(f"⚠️  Error patching/scanning: {e}")

        # Verify the prompt worker thread is running
        import threading
        active_threads = [t.name for t in threading.enumerate()]
        print(f"🔄 Active threads: {active_threads}")
        
        print("✅ ComfyUI initialized successfully!")
        
        # Initialize Backblaze B2 storage
        try:
            from b2_storage import BackblazeB2Storage
            b2_storage = BackblazeB2Storage()
            
            if b2_storage.is_enabled():
                storage_info = b2_storage.get_storage_info()
                print(f"☁️  Backblaze B2 enabled: {storage_info['bucket']}")
            else:
                print("⚠️  Backblaze B2 storage is disabled - files will be served from Modal")
        except Exception as e:
            print(f"⚠️  Backblaze B2 storage initialization failed: {e}")
            # Create a dummy b2_storage object
            class DummyB2Storage:
                def is_enabled(self): return False
                def get_storage_info(self): return {"enabled": False}
                def upload_file(self, *args, **kwargs): return None
                def list_files(self, *args, **kwargs): return []
            b2_storage = DummyB2Storage()
        
        comfyui_state["b2_storage"] = b2_storage

        yield
        
        print("🛑 Shutting down ComfyUI...")
        # Cleanup code if needed

    # Create FastAPI app with lifespan
    web_app = FastAPI(
        title="ComfyUI API on Modal",
        description="Serverless ComfyUI API powered by Modal",
        version="1.1.0",
        lifespan=lifespan
    )
    
    # Helper to get state safely
    def get_prompt_server():
        if comfyui_state["prompt_server"] is None:
            raise HTTPException(status_code=503, detail="ComfyUI not initialized")
        return comfyui_state["prompt_server"]

    def get_b2_storage():
        if comfyui_state["b2_storage"] is None:
            # Fallback
            from b2_storage import BackblazeB2Storage
            return BackblazeB2Storage() 
        return comfyui_state["b2_storage"]

    class PromptRequest(BaseModel):
        prompt: dict
        client_id: str | None = None
        upload_to_b2: bool = True
        wait_for_completion: bool = False
    
    def wait_for_execution(prompt_id: str, timeout: int = 600) -> dict:
        """Wait for a workflow execution to complete and return results"""
        prompt_server = get_prompt_server()
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            history = prompt_server.prompt_queue.get_history(prompt_id=prompt_id)
            
            if prompt_id in history:
                execution_data = history[prompt_id]
                
                if 'outputs' in execution_data:
                    return {
                        "status": "completed",
                        "prompt_id": prompt_id,
                        "outputs": execution_data['outputs'],
                        "execution_time": time.time() - start_time
                    }
                elif 'status' in execution_data and execution_data['status'].get('status_str') == 'error':
                    return {
                        "status": "error",
                        "prompt_id": prompt_id,
                        "error": execution_data['status'].get('messages', []),
                        "execution_time": time.time() - start_time
                    }
            
            current_queue = prompt_server.prompt_queue.get_current_queue_volatile()
            queue_running = current_queue[0]
            queue_pending = current_queue[1]
            
            still_queued = any(
                item[1] == prompt_id 
                for item in queue_running + queue_pending
            )
            
            if not still_queued:
                time.sleep(0.5)
                continue
            
            time.sleep(1)
        
        return {
            "status": "timeout",
            "prompt_id": prompt_id,
            "message": f"Execution did not complete within {timeout} seconds"
        }
    
    def upload_outputs_to_b2(prompt_id: str, outputs: dict) -> dict:
        """Upload output files to Backblaze B2"""
        b2_storage = get_b2_storage()
        if not b2_storage.is_enabled():
            return {"error": "B2 storage is not enabled"}
        
        upload_results = {}
        
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                images = node_output['images']
                uploaded_images = []
                
                for img_data in images:
                    filename = img_data.get('filename')
                    subfolder = img_data.get('subfolder', '')
                    
                    if filename:
                        if subfolder:
                            file_path = os.path.join('/outputs', subfolder, filename)
                        else:
                            file_path = os.path.join('/outputs', filename)
                        
                        if os.path.exists(file_path):
                            metadata = {
                                'prompt_id': prompt_id,
                                'node_id': node_id,
                                'type': img_data.get('type', 'output')
                            }
                            
                            upload_result = b2_storage.upload_file(
                                file_path=file_path,
                                object_name=filename,
                                folder='generations',
                                metadata=metadata
                            )
                            
                            if upload_result:
                                uploaded_images.append({
                                    "filename": filename,
                                    "url": upload_result['url'],
                                    "size": upload_result['size'],
                                    "b2_key": upload_result['key']
                                })
                            else:
                                uploaded_images.append({
                                    "filename": filename,
                                    "error": "Upload failed"
                                })
                
                if uploaded_images:
                    upload_results[node_id] = {
                        "type": "images",
                        "uploads": uploaded_images
                    }
        
        return upload_results
    
    @web_app.get("/")
    async def root():
        """API information"""
        b2_storage = get_b2_storage()
        b2_info = b2_storage.get_storage_info() if b2_storage else {"enabled": False}
        
        # Get current model count
        try:
            import folder_paths
            checkpoint_count = len(folder_paths.get_filename_list("checkpoints"))
        except:
            checkpoint_count = 0
        
        return {
            "name": "ComfyUI on Modal with Backblaze B2",
            "version": "1.1.0",
            "status": "running",
            "models_loaded": checkpoint_count,
            "backblaze_b2": b2_info,
            "endpoints": {
                "POST /prompt": "Queue a workflow (set wait_for_completion=true for sync + B2 upload)",
                "POST /execute_and_upload": "Execute workflow and auto-upload to B2 (simplified)",
                "GET /queue": "Get queue status",
                "GET /history": "Get execution history",
                "GET /history/{prompt_id}": "Get specific execution",
                "POST /history/{prompt_id}/upload_to_b2": "Upload existing outputs to B2",
                "GET /system_stats": "Get system information",
                "GET /b2/status": "Get B2 storage status",
                "POST /interrupt": "Interrupt execution",
                "POST /reload_models": "Reload volumes and rescan models",
            }
        }
    
    @web_app.post("/prompt")
    async def queue_prompt(request: PromptRequest):
        """Queue a ComfyUI workflow for execution"""
        try:
            prompt_server = get_prompt_server()
            # Need to import execution inside function or use fully qualified
            import execution
            
            prompt_id = str(uuid.uuid4())
            
            valid = await execution.validate_prompt(prompt_id, request.prompt, None)
            if not valid[0]:
                return {
                    "error": f"Invalid workflow: {valid[1]}",
                    "valid": False,
                    "node_errors": valid[3] if len(valid) > 3 else {}
                }
            
            outputs_to_execute = valid[2]
            extra_data = {}
            if request.client_id:
                extra_data["client_id"] = request.client_id
            
            number = prompt_server.number
            prompt_server.number += 1
            
            prompt_server.prompt_queue.put((number, prompt_id, request.prompt, extra_data, outputs_to_execute))
            
            if request.wait_for_completion:
                execution_result = wait_for_execution(prompt_id, timeout=TIMEOUT)
                
                b2_storage = get_b2_storage()
                if (request.upload_to_b2 and 
                    b2_storage.is_enabled() and 
                    execution_result.get('status') == 'completed' and 
                    'outputs' in execution_result):
                    
                    b2_uploads = upload_outputs_to_b2(prompt_id, execution_result['outputs'])
                    execution_result['b2_uploads'] = b2_uploads
                
                return {
                    "prompt_id": prompt_id,
                    "number": number,
                    "valid": True,
                    "node_errors": valid[3] if len(valid) > 3 else {},
                    "execution": execution_result
                }
            
            return {
                "prompt_id": prompt_id,
                "number": number,
                "valid": True,
                "node_errors": valid[3] if len(valid) > 3 else {},
                "message": "Workflow queued. Use GET /history/{prompt_id} to check status."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/queue")
    async def get_queue():
        """Get current queue status"""
        try:
            prompt_server = get_prompt_server()
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
            prompt_server = get_prompt_server()
            history = prompt_server.prompt_queue.get_history()
            return history
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/history/{prompt_id}")
    async def get_history_by_id(prompt_id: str):
        """Get execution history for specific prompt"""
        try:
            prompt_server = get_prompt_server()
            history = prompt_server.prompt_queue.get_history(prompt_id=prompt_id)
            return history
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.post("/history/{prompt_id}/upload_to_b2")
    async def upload_history_to_b2(prompt_id: str):
        """Upload outputs from a completed execution to Backblaze B2"""
        try:
            b2_storage = get_b2_storage()
            if not b2_storage.is_enabled():
                raise HTTPException(
                    status_code=400, 
                    detail="Backblaze B2 storage is not enabled"
                )
            
            prompt_server = get_prompt_server()
            history = prompt_server.prompt_queue.get_history(prompt_id=prompt_id)
            
            if prompt_id not in history:
                raise HTTPException(
                    status_code=404,
                    detail=f"No execution found for prompt_id: {prompt_id}"
                )
            
            execution_data = history[prompt_id]
            
            if 'outputs' not in execution_data:
                raise HTTPException(
                    status_code=400,
                    detail="Execution has no outputs to upload"
                )
            
            b2_uploads = upload_outputs_to_b2(prompt_id, execution_data['outputs'])
            
            return {
                "prompt_id": prompt_id,
                "status": "success",
                "b2_uploads": b2_uploads
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/system_stats")
    async def get_system_stats():
        """Get system statistics"""
        try:
            import comfy.model_management
            device = comfy.model_management.get_torch_device()
            device_name = comfy.model_management.get_torch_device_name(device)
            
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
            import comfy.model_management
            comfy.model_management.interrupt_current_processing()
            return {"status": "interrupted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/b2/status")
    async def get_b2_status():
        """Get Backblaze B2 storage status and configuration"""
        try:
            b2_storage = get_b2_storage()
            if not b2_storage.is_enabled():
                return {
                    "enabled": False,
                    "message": "Backblaze B2 storage is not configured"
                }
            
            storage_info = b2_storage.get_storage_info()
            
            recent_files = []
            try:
                files = b2_storage.list_files(prefix="generations/")
                recent_files = sorted(
                    files, 
                    key=lambda x: x.get('LastModified', ''), 
                    reverse=True
                )[:10]
                recent_files = [
                    {
                        "key": f.get('Key'),
                        "size": f.get('Size'),
                        "last_modified": f.get('LastModified')
                    }
                    for f in recent_files
                ]
            except Exception as e:
                recent_files = {"error": str(e)}
            
            return {
                "enabled": True,
                "storage_info": storage_info,
                "recent_uploads": recent_files
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.post("/execute_and_upload")
    async def execute_and_upload(request: PromptRequest):
        """Execute workflow and automatically upload to B2"""
        try:
            request.wait_for_completion = True
            request.upload_to_b2 = True
            
            result = await queue_prompt(request)
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    class DebugFileRequest(BaseModel):
        path: str

    @web_app.post("/debug/read_file")
    async def debug_read_file(request: DebugFileRequest):
        """Debug endpoint to read file content or list directory"""
        try:
            full_path = os.path.join("/root/comfy_app", request.path)
            if not os.path.exists(full_path):
                # Try listing root to debug
                if request.path == "ROOT":
                    return {"path": "/", "content": str(os.listdir("/"))}
                if request.path == "HOME":
                    return {"path": "/root", "content": str(os.listdir("/root"))}
                raise HTTPException(status_code=404, detail=f"File not found: {full_path}")
            
            if os.path.isdir(full_path):
                return {"path": full_path, "content": str(os.listdir(full_path))}
            
            with open(full_path, 'r') as f:
                content = f.read()
            return {"path": full_path, "content": content}
            if not os.path.exists(full_path):
                # Try listing root to debug
                if request.path == "ROOT":
                    return {"path": "/", "content": str(os.listdir("/"))}
                raise HTTPException(status_code=404, detail=f"File not found: {full_path}")
            
            if os.path.isdir(full_path):
                return {"path": full_path, "content": str(os.listdir(full_path))}
            
            with open(full_path, 'r') as f:
                content = f.read()
            return {"path": full_path, "content": content}
        except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))


             
    @web_app.post("/reload_models")
    async def reload_models():
        """Reload volumes and rescan all model directories"""
        try:
            import folder_paths
            # Reload volumes to get latest data
            print("🔄 Reloading volumes...")
            models_volume.reload()
            outputs_volume.reload()
            
            # Clear all filename caches
            if hasattr(folder_paths, 'filename_list_cache'):
                folder_paths.filename_list_cache.clear()
            if hasattr(folder_paths, 'cache_helper'):
                folder_paths.cache_helper.clear()
            
            # Force rescan of all model types
            model_types = ["checkpoints", "vae", "loras", "controlnet", "clip_vision", "upscale_models", "embeddings", "unet", "clip"]
            results = {}
            
            for model_type in model_types:
                try:
                    file_list = folder_paths.get_filename_list(model_type)
                    results[model_type] = len(file_list)
                except Exception as e:
                    results[model_type] = f"error: {str(e)}"
            
            return {
                "status": "success", 
                "message": "Volumes reloaded and models rescanned", 
                "model_counts": results
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/debug/folder_paths")
    async def debug_folder_paths():
        """Debug endpoint to see what folders ComfyUI knows about"""
        try:
            import folder_paths
            debug_info = {}
            
            for folder_type in ["checkpoints", "vae", "loras", "controlnet"]:
                paths = folder_paths.get_folder_paths(folder_type)
                debug_info[folder_type] = {
                    "configured_paths": paths,
                    "files": []
                }
                
                for path in paths:
                    if os.path.exists(path):
                        try:
                            files = os.listdir(path)
                            debug_info[folder_type]["files"].extend([
                                f"{path}/{f}" for f in files if os.path.isfile(os.path.join(path, f))
                            ])
                        except Exception as e:
                            debug_info[folder_type]["error"] = str(e)
            
            return debug_info
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    @web_app.get("/debug/qwen")
    async def debug_qwen_file():
        """Read the qwen_image.py file and check module"""
        try:
            import comfy.text_encoders.qwen_image
            module_file = comfy.text_encoders.qwen_image.__file__
            
            with open("/app/comfy/text_encoders/qwen_image.py", "r") as f:
                content = f.read()
                
            return {
                "module_file": module_file,
                "file_content_snippet": content[:1000],  # First 1000 chars should contain our print and patch
                "has_debug_print": 'DEBUG: Initializing Qwen25_7BVLIModel with 4B Patch' in content,
                "has_config_patch": 'config_4b =' in content
            }
        except Exception as e:
            return {"error": str(e)}

    
    @web_app.get("/outputs")
    async def list_outputs():
        """List all output files"""
        try:
            outputs = []
            output_dir = "/outputs"
            
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    filepath = os.path.join(output_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        outputs.append({
                            "filename": filename,
                            "size": stat.st_size,
                            "modified": stat.st_mtime
                        })
            
            return {"outputs": sorted(outputs, key=lambda x: x['modified'], reverse=True)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/outputs/{filename}")
    async def get_output_file(filename: str):
        """Download a specific output file"""
        try:
            filepath = os.path.join("/outputs", filename)
            if not os.path.exists(filepath):
                raise HTTPException(status_code=404, detail="File not found")
            
            return FileResponse(filepath, media_type="image/png", filename=filename)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/object_info")
    async def get_object_info():
        """Get available node information"""
        try:
            out = {}
            import nodes
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
    
    @web_app.get("/debug/qwen")
    async def debug_qwen_file():
        """Read the qwen_image.py file and check module"""
        try:
            import comfy.text_encoders.qwen_image
            module_file = comfy.text_encoders.qwen_image.__file__
            
            with open("/app/comfy/text_encoders/qwen_image.py", "r") as f:
                content = f.read()
                
            return {
                "module_file": module_file,
                "file_content_snippet": content[:3000],  # Read enough to see the config
                "config_in_file": 'intermediate_size": 9728' in content
            }
        except Exception as e:
            return {"error": str(e)}

    return web_app


# Model management functions
@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=7200,  # 2 hours for large models
    secrets=_get_secrets_list(),
)
def _sanitize_filename(name: str) -> str:
    """Convert a model name to a safe filename"""
    import re
    # Remove or replace invalid filename characters
    # Keep alphanumeric, spaces, hyphens, underscores, dots
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove leading/trailing dots and spaces
    name = name.strip('._ ')
    # Limit length
    if len(name) > 200:
        name = name[:200]
    return name

def _get_civitai_model_name(url: str, civitai_api_key: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract model information from Civitai URL and return (model_name, version_name).
    Returns (None, None) if unable to fetch.
    """
    import re
    import requests
    
    try:
        # Parse Civitai URL to get model_id and version_id
        # Pattern: https://civitai.com/models/12345/model-name/versions/67890
        version_pattern = r'civitai\.com/models/(\d+)/[^/]+/versions/(\d+)'
        match = re.search(version_pattern, url)
        if match:
            model_id = int(match.group(1))
            version_id = int(match.group(2))
        else:
            # Pattern: https://civitai.com/api/download/models/67890
            download_pattern = r'civitai\.com/api/download/models/(\d+)'
            match = re.search(download_pattern, url)
            if match:
                version_id = int(match.group(1))
                model_id = None
            else:
                # Pattern: https://civitai.com/models/12345/model-name
                model_pattern = r'civitai\.com/models/(\d+)'
                match = re.search(model_pattern, url)
                if match:
                    model_id = int(match.group(1))
                    version_id = None
                else:
                    return (None, None)
        
        # Fetch model info from Civitai API
        base_url = "https://civitai.com/api/v1"
        headers = {}
        if civitai_api_key:
            headers['Authorization'] = f'Bearer {civitai_api_key}'
        
        model_name = None
        version_name = None
        
        # Get version info first (if we have version_id)
        if version_id:
            version_url = f"{base_url}/model-versions/{version_id}"
            response = requests.get(version_url, headers=headers, timeout=10)
            if response.status_code == 200:
                version_data = response.json()
                version_name = version_data.get('name', '')
                if not model_id:
                    model_id = version_data.get('modelId')
        
        # Get model info (if we have model_id)
        if model_id:
            model_url = f"{base_url}/models/{model_id}"
            response = requests.get(model_url, headers=headers, timeout=10)
            if response.status_code == 200:
                model_data = response.json()
                model_name = model_data.get('name', '')
        
        return (model_name, version_name)
        
    except Exception as e:
        print(f"   ⚠️  Could not fetch model info from Civitai: {e}")
        return (None, None)

@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=600,
    secrets=_get_secrets_list(),
)
def download_model(url: str, category: str = "checkpoints", filename: str = None):
    """Download a single model from URL to the persistent volume"""
    import urllib.request
    from urllib.parse import urlparse, unquote
    import requests
    
    print(f"📥 Downloading model to /models/{category}/")
    
    model_dir = f"/models/{category}"
    os.makedirs(model_dir, exist_ok=True)
    
    is_civitai = 'civitai.com' in url.lower()
    civitai_api_key = os.environ.get('CIVITAI_API_KEY')
    
    # Try to get human-readable name from Civitai API
    original_filename = filename
    if not filename and is_civitai:
        model_name, version_name = _get_civitai_model_name(url, civitai_api_key)
        if model_name:
            # Build filename from model name and version
            name_parts = [_sanitize_filename(model_name)]
            if version_name:
                name_parts.append(_sanitize_filename(version_name))
            
            # Get file extension from URL
            parsed = urlparse(url)
            original_basename = unquote(os.path.basename(parsed.path))
            if original_basename:
                # Extract extension
                ext = os.path.splitext(original_basename)[1] or '.safetensors'
            else:
                ext = '.safetensors'
            
            filename = '_'.join(name_parts) + ext
            print(f"   📝 Using human-readable name: {filename}")
        else:
            # Fallback to extracting from URL
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path))
            if not filename or filename == '':
                filename = "downloaded_model"
    elif not filename:
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path))
        if not filename or filename == '':
            filename = "downloaded_model"
    
    file_path = os.path.join(model_dir, filename)
    
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"⚠️  File already exists: {filename} ({file_size / 1024 / 1024:.1f} MB)")
        print(f"   Skipping download. Delete it first if you want to re-download.")
        return {"status": "skipped", "path": file_path, "size": file_size}
    
    print(f"🌐 Downloading: {filename}")
    print(f"   From: {url[:80]}...")
    
    if is_civitai and civitai_api_key:
        print(f"   🔑 Using Civitai API authentication")
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}token={civitai_api_key}"
    elif is_civitai and not civitai_api_key:
        print(f"   ⚠️  Civitai URL detected but no API key found. Download may fail for private models.")
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"   Attempt {retry_count + 1}/{max_retries}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                downloaded = 0
                chunk_size = 8192 * 16
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = downloaded * 100 / total_size
                            mb_downloaded = downloaded / 1024 / 1024
                            mb_total = total_size / 1024 / 1024
                            print(f"   Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='\r')
            
            print()
            
            file_size = os.path.getsize(file_path)
            
            if total_size > 0 and file_size < total_size:
                raise Exception(f"Download incomplete: {file_size}/{total_size} bytes")
            
            print(f"✅ Downloaded: {filename} ({file_size / 1024 / 1024:.1f} MB)")
            
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
            retry_count += 1
            print(f"\n❌ Error on attempt {retry_count}: {e}")
            
            if retry_count < max_retries:
                import time
                wait_time = retry_count * 5
                print(f"   Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed after {max_retries} attempts")
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
    categories = [
        "checkpoints", "vae", "loras", "controlnet", 
        "clip_vision", "unet", "embeddings", "upscale_models",
        "text_encoders", "clip"
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
def rename_model(category: str, old_filename: str, new_filename: str):
    """Rename a model file in the persistent volume"""
    import shutil
    
    old_path = os.path.join(f"/models/{category}", old_filename)
    new_path = os.path.join(f"/models/{category}", new_filename)
    
    if not os.path.exists(old_path):
        return {"status": "error", "message": f"File not found: {old_filename}"}
    
    if os.path.exists(new_path):
        return {"status": "error", "message": f"Target file already exists: {new_filename}"}
    
    try:
        shutil.move(old_path, new_path)
        file_size = os.path.getsize(new_path)
        return {
            "status": "success",
            "old_path": old_path,
            "new_path": new_path,
            "size_mb": file_size / 1024 / 1024
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=300,
)
def delete_model(category: str, filename: str):
    """Delete a model from the persistent volume"""
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
    print("🌐 ComfyUI Modal Deployment (FastAPI Version - Fixed)")
    print("=" * 50)
    print("\nTo deploy:")
    print("  modal deploy modal/apps/modal_app_fastapi_fixed.py")
    print("\nYour endpoint will be:")
    print("  https://{workspace}--comfyui-api-web.modal.run")
    print("\nExample endpoints:")
    print("  GET  /                - API information")
    print("  POST /prompt          - Queue a workflow")
    print("  GET  /queue           - Get queue status")
    print("  GET  /system_stats    - Get system information")
