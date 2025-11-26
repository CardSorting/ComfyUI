#!/usr/bin/env python3
"""Script to rename model file in Modal volume to human-readable name"""
import modal
from typing import Tuple, Optional

app = modal.App("rename-model")

# Get the volume
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=False)

# Use the same image as the main app
image = modal.Image.debian_slim().pip_install(["requests"])

def _get_secrets_list():
    """
    Get secrets lazily - only called when actually needed.
    This prevents issues with secret resolution during module import.
    """
    secrets = []
    
    try:
        civitai_secret = modal.Secret.from_name("civitai-api-key")
        secrets.append(civitai_secret)
    except Exception:
        pass  # Secret doesn't exist
    
    return secrets

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

def _get_model_name_from_civitai_id(model_id_or_version_id: int, is_version_id: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch model information from Civitai API using model ID or version ID.
    Returns (model_name, version_name) or (None, None) if unable to fetch.
    """
    import os
    import requests
    
    try:
        base_url = "https://civitai.com/api/v1"
        headers = {}
        civitai_api_key = os.environ.get('CIVITAI_API_KEY')
        if civitai_api_key:
            headers['Authorization'] = f'Bearer {civitai_api_key}'
        
        model_name = None
        version_name = None
        
        if is_version_id:
            # Get version info first
            version_url = f"{base_url}/model-versions/{model_id_or_version_id}"
            response = requests.get(version_url, headers=headers, timeout=10)
            if response.status_code == 200:
                version_data = response.json()
                version_name = version_data.get('name', '')
                model_id = version_data.get('modelId')
                
                # Get model info
                if model_id:
                    model_url = f"{base_url}/models/{model_id}"
                    response = requests.get(model_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        model_data = response.json()
                        model_name = model_data.get('name', '')
        else:
            # Get model info directly
            model_url = f"{base_url}/models/{model_id_or_version_id}"
            response = requests.get(model_url, headers=headers, timeout=10)
            if response.status_code == 200:
                model_data = response.json()
                model_name = model_data.get('name', '')
                # Get latest version name
                versions = model_data.get('modelVersions', [])
                if versions:
                    version_name = versions[0].get('name', '')
        
        return (model_name, version_name)
        
    except Exception as e:
        print(f"   ⚠️  Could not fetch model info from Civitai: {e}")
        return (None, None)

@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=300,
    secrets=_get_secrets_list(),
)
def rename_model(old_filename: str = None, model_id: int = None, version_id: int = None):
    """
    Rename a model file to a human-readable name.
    
    Args:
        old_filename: The current filename (e.g., "2440705.safetensors")
        model_id: Optional Civitai model ID to fetch name from API
        version_id: Optional Civitai version ID to fetch name from API
    """
    import os
    import shutil
    import re
    
    checkpoints_dir = "/models/checkpoints"
    if not os.path.exists(checkpoints_dir):
        return {"status": "error", "message": f"Directory not found: {checkpoints_dir}"}
    
    files = os.listdir(checkpoints_dir)
    print(f"Files in checkpoints directory: {files}")
    
    # Find the file to rename
    old_file = None
    if old_filename:
        # Look for exact match or file containing the pattern
        for f in files:
            if f == old_filename or old_filename in f:
                old_file = f
                break
    else:
        # Try to find files with numeric IDs (like 2440705.safetensors)
        for f in files:
            # Check if filename is just a number with extension
            match = re.match(r'^(\d+)\.(safetensors|ckpt|pt|pth|bin)$', f)
            if match:
                old_file = f
                numeric_id = int(match.group(1))
                # Use as version_id if not provided
                if not version_id and not model_id:
                    version_id = numeric_id
                break
    
    if not old_file:
        return {"status": "error", "message": f"No file found to rename. Files: {files}"}
    
    old_path = os.path.join(checkpoints_dir, old_file)
    
    if not os.path.exists(old_path):
        return {"status": "error", "message": f"File not found: {old_path}"}
    
    # Try to get human-readable name
    new_filename = None
    if version_id or model_id:
        model_name, version_name = _get_model_name_from_civitai_id(
            version_id or model_id, 
            is_version_id=bool(version_id)
        )
        if model_name:
            # Build filename from model name and version
            name_parts = [_sanitize_filename(model_name)]
            if version_name:
                name_parts.append(_sanitize_filename(version_name))
            
            # Get file extension from old filename
            ext = os.path.splitext(old_file)[1] or '.safetensors'
            new_filename = '_'.join(name_parts) + ext
            print(f"   📝 Generated human-readable name: {new_filename}")
    
    # Fallback: if we couldn't get a name, try to improve the existing name
    if not new_filename:
        # Check if there's a metadata file
        metadata_path = old_path + ".civitai.json"
        if os.path.exists(metadata_path):
            import json
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    model_name = metadata.get('model', {}).get('name', '')
                    version_name = metadata.get('version', {}).get('name', '')
                    if model_name:
                        name_parts = [_sanitize_filename(model_name)]
                        if version_name:
                            name_parts.append(_sanitize_filename(version_name))
                        ext = os.path.splitext(old_file)[1] or '.safetensors'
                        new_filename = '_'.join(name_parts) + ext
                        print(f"   📝 Generated name from metadata: {new_filename}")
            except Exception as e:
                print(f"   ⚠️  Could not read metadata: {e}")
    
    # Final fallback: use a generic name
    if not new_filename:
        # Extract numeric ID and create a slightly better name
        match = re.match(r'^(\d+)\.(safetensors|ckpt|pt|pth|bin)$', old_file)
        if match:
            numeric_id = match.group(1)
            ext = match.group(2)
            new_filename = f"model_{numeric_id}.{ext}"
        else:
            # Just add a prefix
            new_filename = f"model_{old_file}"
        print(f"   ⚠️  Using fallback name: {new_filename}")
    
    new_path = os.path.join(checkpoints_dir, new_filename)
    
    if old_file == new_filename:
        return {"status": "already_named", "path": old_path, "filename": old_file}
    
    if os.path.exists(new_path):
        return {"status": "already_exists", "path": new_path, "message": f"Target file already exists: {new_filename}"}
    
    try:
        shutil.move(old_path, new_path)
        file_size = os.path.getsize(new_path)
        models_volume.commit()
        return {
            "status": "success",
            "old_filename": old_file,
            "new_filename": new_filename,
            "old_path": old_path,
            "new_path": new_path,
            "size_mb": file_size / 1024 / 1024
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    old_filename = None
    model_id = None
    version_id = None
    
    if len(sys.argv) > 1:
        # First arg can be filename or model_id
        arg1 = sys.argv[1]
        if arg1.isdigit():
            version_id = int(arg1)
        else:
            old_filename = arg1
    
    if len(sys.argv) > 2:
        # Second arg can be model_id if first was version_id
        arg2 = sys.argv[2]
        if arg2.isdigit():
            if version_id:
                model_id = int(arg2)
            else:
                version_id = int(arg2)
    
    with app.run():
        result = rename_model.remote(
            old_filename=old_filename,
            model_id=model_id,
            version_id=version_id
        )
        print("Result:", result)

