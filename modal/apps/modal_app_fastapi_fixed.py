"""
ComfyUI on Modal.com - FastAPI Version (Fixed)

This version fixes the recursive build loop by:
1. Using lazy secret resolution (only resolved when function runs)
2. Using absolute paths for add_local_dir
3. Moving all print statements out of module-level code

Usage:
    modal deploy modal/apps/modal_app_fastapi_fixed.py
"""

import modal
import os
from pathlib import Path

# Modal app configuration
app = modal.App("comfyui-api")

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
    .add_local_dir(
        str(COMFYUI_ROOT), 
        remote_path="/app",
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
        b2_secret = modal.Secret.from_name("backblaze-b2-credentials", create_if_missing=False)
        secrets.append(b2_secret)
    except Exception:
        pass  # Secret doesn't exist
    
    try:
        civitai_secret = modal.Secret.from_name("civitai-api-key", create_if_missing=False)
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
def web():
    """FastAPI app that runs inside the GPU container with ComfyUI"""
    import sys
    sys.path.insert(0, "/app")  # ComfyUI root
    sys.path.insert(0, "/app/modal/apps")  # For b2_storage module
    
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, FileResponse
    from pydantic import BaseModel
    import uuid
    import json
    import time
    
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
    folder_paths.add_model_folder_path("checkpoints", "/models/checkpoints", is_default=True)
    folder_paths.add_model_folder_path("vae", "/models/vae", is_default=True)
    folder_paths.add_model_folder_path("loras", "/models/loras", is_default=True)
    folder_paths.add_model_folder_path("controlnet", "/models/controlnet", is_default=True)
    folder_paths.add_model_folder_path("clip_vision", "/models/clip_vision", is_default=True)
    folder_paths.add_model_folder_path("upscale_models", "/models/upscale_models", is_default=True)
    folder_paths.add_model_folder_path("embeddings", "/models/embeddings", is_default=True)
    
    print(f"📁 Configured model paths: {folder_paths.get_folder_paths('checkpoints')}")
    
    # NOW import ComfyUI modules
    import main
    import execution
    import comfy.model_management
    
    # Configure for headless mode
    args.headless = True
    args.disable_all_custom_nodes = True
    args.whitelist_custom_nodes = ["websocket_image_save.py"]
    
    print("🚀 Initializing ComfyUI...")
    
    # Initialize ComfyUI (this loads nodes and starts execution thread)
    event_loop, prompt_server, _ = main.start_comfyui()
    event_loop.run_until_complete(prompt_server.setup())
    
    # Check how many nodes were loaded
    import nodes
    print(f"📦 Loaded {len(nodes.NODE_CLASS_MAPPINGS)} node types")
    
    # Verify the prompt worker thread is running
    import threading
    active_threads = [t.name for t in threading.enumerate()]
    print(f"🔄 Active threads: {active_threads}")
    
    print("✅ ComfyUI initialized successfully!")
    
    # Initialize Backblaze B2 storage (gracefully handle if not available)
    b2_storage = None
    try:
        from b2_storage import BackblazeB2Storage
        b2_storage = BackblazeB2Storage()
        
        if b2_storage.is_enabled():
            storage_info = b2_storage.get_storage_info()
            print(f"☁️  Backblaze B2 enabled: {storage_info['bucket']}")
        else:
            print("⚠️  Backblaze B2 storage is disabled - files will be served from Modal")
    except Exception as e:
        print(f"⚠️  Backblaze B2 storage initialization failed: {type(e).__name__}: {e}")
        print("   Files will be served from Modal volumes")
        
        # Create a dummy b2_storage object to prevent errors
        class DummyB2Storage:
            def is_enabled(self): return False
            def get_storage_info(self): return {"enabled": False}
            def upload_file(self, *args, **kwargs): return None
            def list_files(self, *args, **kwargs): return []
        b2_storage = DummyB2Storage()
    
    # Create FastAPI app
    web_app = FastAPI(
        title="ComfyUI API on Modal",
        description="Serverless ComfyUI API powered by Modal",
        version="1.0.0"
    )
    
    class PromptRequest(BaseModel):
        prompt: dict
        client_id: str | None = None
        upload_to_b2: bool = True
        wait_for_completion: bool = False
    
    def wait_for_execution(prompt_id: str, timeout: int = 600) -> dict:
        """Wait for a workflow execution to complete and return results"""
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
        b2_info = b2_storage.get_storage_info() if b2_storage else {"enabled": False}
        
        return {
            "name": "ComfyUI on Modal with Backblaze B2",
            "version": "1.0.0",
            "status": "running",
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
            }
        }
    
    @web_app.post("/prompt")
    async def queue_prompt(request: PromptRequest):
        """Queue a ComfyUI workflow for execution"""
        try:
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
    
    @web_app.post("/history/{prompt_id}/upload_to_b2")
    async def upload_history_to_b2(prompt_id: str):
        """Upload outputs from a completed execution to Backblaze B2"""
        try:
            if not b2_storage.is_enabled():
                raise HTTPException(
                    status_code=400, 
                    detail="Backblaze B2 storage is not enabled"
                )
            
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
            comfy.model_management.interrupt_current_processing()
            return {"status": "interrupted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/b2/status")
    async def get_b2_status():
        """Get Backblaze B2 storage status and configuration"""
        try:
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
    
    @web_app.get("/debug/folder_paths")
    async def debug_folder_paths():
        """Debug endpoint to see what folders ComfyUI knows about"""
        try:
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
                    else:
                        debug_info[folder_type]["path_exists"] = False
            
            debug_info["available_checkpoints"] = folder_paths.get_filename_list("checkpoints")
            
            return debug_info
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
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


# Model management functions
@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=7200,  # 2 hours for large models
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
    
    if not filename:
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
    
    is_civitai = 'civitai.com' in url.lower()
    civitai_api_key = os.environ.get('CIVITAI_API_KEY')
    
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

