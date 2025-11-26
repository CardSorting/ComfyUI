"""
ComfyUI on Modal.com - FastAPI Version (Robust)

This version includes error handling for missing secrets and other common issues.

Usage:
    modal deploy modal/apps/modal_app_fastapi_robust.py
"""

import modal
import os

# Modal app configuration
app = modal.App("comfyui-api")

# Define the container image
# Using optimized build with better error handling
# PyTorch installation is the slowest step (~10-15 min) but necessary
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git", "wget", "curl", "build-essential",
        "libglib2.0-0", "libsm6", "libxext6", "libxrender-dev",
        "libgomp1", "libgl1-mesa-glx",
    )
    # PyTorch installation - this is the slowest step (~10-15 minutes)
    # If this stalls, check Modal dashboard for progress
    .pip_install(
        "torch", "torchvision", "torchaudio",
        index_url="https://download.pytorch.org/whl/cu121"
    )
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
    # Add ComfyUI root directory LAST - this must be the final step
    # Exclude large/unnecessary directories to speed up deployment
    # Use copy=False to add files at runtime (not baked into image) - faster builds
    .add_local_dir(
        "../..", 
        remote_path="/app",
        copy=False,  # Files added at runtime, not during build - much faster!
        ignore=[
            # Exclude model directories (use volumes instead)
            "models/**",
            "output/**",
            "input/**",
            "!input/example.png",  # Keep example image
            
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
            
            # Exclude test files and documentation (not needed at runtime)
            "tests/**",
            "tests-unit/**",
            "docs/**",
            "*.md",
            "!README.md",  # Keep main README
            "!modal/**/*.md",  # Keep modal docs
            
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
            "!modal/**/*.sh",  # Keep modal scripts
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
GPU_CONFIG = "A10G"  # String format is correct (new Modal API)
TIMEOUT = 600
SCALEDOWN_WINDOW = 300

# Handle secrets gracefully - make them optional
# If secrets don't exist, the app will still work but B2/Civitai features won't
secrets_list = []
try:
    b2_secret = modal.Secret.from_name("backblaze-b2-credentials", create_if_missing=False)
    secrets_list.append(b2_secret)
    print("✅ Backblaze B2 secret found")
except Exception:
    print("⚠️  Backblaze B2 secret not found - B2 uploads will be disabled")

try:
    civitai_secret = modal.Secret.from_name("civitai-api-key", create_if_missing=False)
    secrets_list.append(civitai_secret)
    print("✅ Civitai API key secret found")
except Exception:
    print("⚠️  Civitai API key secret not found - Civitai downloads will be limited")


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
    secrets=secrets_list if secrets_list else None,  # Only add secrets if they exist
)
@modal.asgi_app()
def web():
    """FastAPI app that runs inside the GPU container with ComfyUI"""
    import sys
    sys.path.insert(0, "/app")  # ComfyUI root
    sys.path.insert(0, "/app/modal/apps")  # For b2_storage module
    
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uuid
    import json
    import time
    
    # Set environment variables
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
    # Add as default paths (insert at position 0) so they're checked first
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
    # Disable problematic custom nodes that require dependencies not available in serverless
    # (comfyui-impact-pack and comfyui-impact-subpack require cv2/OpenCV)
    args.disable_all_custom_nodes = True
    args.whitelist_custom_nodes = ["websocket_image_save.py"]  # Only allow core custom nodes
    
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
        print(f"⚠️  Backblaze B2 storage not available: {e}")
        print("   Files will be served from Modal volumes")
    
    # Create FastAPI app
    web_app = FastAPI(
        title="ComfyUI API on Modal",
        description="Serverless ComfyUI API powered by Modal",
        version="1.0.0"
    )
    
    class PromptRequest(BaseModel):
        prompt: dict
        client_id: str | None = None
        upload_to_b2: bool = True  # Auto-upload to B2 by default
        wait_for_completion: bool = False  # Set to True for synchronous execution
    
    def wait_for_execution(prompt_id: str, timeout: int = 600) -> dict:
        """
        Wait for a workflow execution to complete and return results
        
        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dict with execution status and output files
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check history for this prompt
            history = prompt_server.prompt_queue.get_history(prompt_id=prompt_id)
            
            if prompt_id in history:
                execution_data = history[prompt_id]
                
                # Check if execution is complete
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
            
            # Check queue status
            current_queue = prompt_server.prompt_queue.get_current_queue_volatile()
            queue_running = current_queue[0]
            queue_pending = current_queue[1]
            
            # Check if still in queue
            still_queued = any(
                item[1] == prompt_id 
                for item in queue_running + queue_pending
            )
            
            if not still_queued:
                # Not in queue but not in history - might have failed
                time.sleep(0.5)
                continue
            
            # Still processing, wait a bit
            time.sleep(1)
        
        return {
            "status": "timeout",
            "prompt_id": prompt_id,
            "message": f"Execution did not complete within {timeout} seconds"
        }
    
    def upload_outputs_to_b2(prompt_id: str, outputs: dict) -> dict:
        """
        Upload output files to Backblaze B2
        
        Args:
            prompt_id: The prompt ID
            outputs: Output data from ComfyUI execution
            
        Returns:
            Dict mapping node IDs to B2 upload results
        """
        if not b2_storage or not b2_storage.is_enabled():
            return {"error": "B2 storage is not enabled"}
        
        import os
        upload_results = {}
        
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                images = node_output['images']
                uploaded_images = []
                
                for img_data in images:
                    filename = img_data.get('filename')
                    subfolder = img_data.get('subfolder', '')
                    
                    if filename:
                        # Construct the full file path
                        if subfolder:
                            file_path = os.path.join('/outputs', subfolder, filename)
                        else:
                            file_path = os.path.join('/outputs', filename)
                        
                        if os.path.exists(file_path):
                            # Upload to B2
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
        b2_info = {"enabled": False}
        if b2_storage:
            b2_info = b2_storage.get_storage_info() if b2_storage else {"enabled": False}
        
        return {
            "name": "ComfyUI on Modal",
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
    
    # ... (rest of the endpoints would be the same as the original file)
    # For brevity, I'm showing the key changes - the rest of the endpoints
    # should be copied from modal_app_fastapi.py
    
    return web_app


# Additional functions (download_model, list_models, delete_model) would go here
# They should also handle missing secrets gracefully

