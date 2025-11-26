#!/usr/bin/env python3
"""Script to rename model file in Modal volume"""
import modal

app = modal.App("rename-model")

# Get the volume
models_volume = modal.Volume.from_name("comfyui-models", create_if_missing=False)

# Use the same image as the main app
image = modal.Image.debian_slim().pip_install([])

@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=300,
)
def rename_model():
    import os
    import shutil
    
    checkpoints_dir = "/models/checkpoints"
    if not os.path.exists(checkpoints_dir):
        return {"status": "error", "message": f"Directory not found: {checkpoints_dir}"}
    
    files = os.listdir(checkpoints_dir)
    print(f"Files in checkpoints directory: {files}")
    
    # Find the file (might be 2440705 or something else)
    old_file = None
    for f in files:
        if '2440705' in f:
            old_file = f
            break
    
    if not old_file:
        return {"status": "error", "message": f"No file containing '2440705' found. Files: {files}"}
    
    old_path = os.path.join(checkpoints_dir, old_file)
    new_path = os.path.join(checkpoints_dir, "2440705.safetensors")
    
    if old_file == "2440705.safetensors":
        return {"status": "already_renamed", "path": old_path}
    
    if not os.path.exists(old_path):
        return {"status": "error", "message": f"File not found: {old_path}"}
    
    if os.path.exists(new_path):
        return {"status": "already_exists", "path": new_path}
    
    try:
        shutil.move(old_path, new_path)
        file_size = os.path.getsize(new_path)
        models_volume.commit()
        return {
            "status": "success",
            "old_path": old_path,
            "new_path": new_path,
            "size_mb": file_size / 1024 / 1024
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    with app.run():
        result = rename_model.remote()
        print("Result:", result)

