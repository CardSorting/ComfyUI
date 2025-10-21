#!/usr/bin/env python3
"""
RunPod Serverless Handler for ComfyUI

This handler receives workflow requests from RunPod and executes them using ComfyUI.
"""

import runpod
import json
import sys
import os
import time
import uuid
import base64
from pathlib import Path

# Add ComfyUI to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import ComfyUI modules
import execution
import folder_paths
from nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from comfy_execution.graph import ExecutionGraph
from comfy_execution.graph_utils import is_link
import server


def setup_environment():
    """Set up the ComfyUI environment"""
    print("Setting up ComfyUI environment...")
    
    # Ensure output directory exists
    output_dir = folder_paths.get_output_directory()
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure input directory exists
    input_dir = folder_paths.get_input_directory()
    os.makedirs(input_dir, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    print(f"Input directory: {input_dir}")
    
    # List available checkpoints
    checkpoints = folder_paths.get_filename_list("checkpoints")
    print(f"Available checkpoints: {len(checkpoints)}")
    if checkpoints:
        print(f"  - {checkpoints[0]}")
        if len(checkpoints) > 1:
            print(f"  ... and {len(checkpoints) - 1} more")


def validate_workflow(workflow):
    """Validate that the workflow is properly formatted"""
    if not isinstance(workflow, dict):
        return False, "Workflow must be a dictionary"
    
    # Check for basic workflow structure
    if not workflow:
        return False, "Workflow is empty"
    
    # Workflow should have node IDs as keys
    for node_id, node_data in workflow.items():
        if not isinstance(node_data, dict):
            return False, f"Node {node_id} data must be a dictionary"
        
        if "class_type" not in node_data:
            return False, f"Node {node_id} missing 'class_type'"
        
        # Check if class type exists
        class_type = node_data["class_type"]
        if class_type not in NODE_CLASS_MAPPINGS:
            return False, f"Unknown node class: {class_type}"
    
    return True, "Workflow is valid"


def execute_workflow(workflow, client_id=None, return_images=True):
    """
    Execute a ComfyUI workflow
    
    Args:
        workflow: ComfyUI workflow dictionary
        client_id: Client ID for execution tracking
        return_images: Whether to return base64 encoded images
    
    Returns:
        dict: Execution results
    """
    if client_id is None:
        client_id = str(uuid.uuid4())
    
    print(f"Executing workflow with client_id: {client_id}")
    
    # Validate workflow
    valid, message = validate_workflow(workflow)
    if not valid:
        return {
            "status": "error",
            "error": f"Invalid workflow: {message}"
        }
    
    try:
        # Get the PromptServer instance
        if not hasattr(server, 'PromptServer') or server.PromptServer.instance is None:
            # Initialize a minimal server instance if needed
            print("Warning: PromptServer not initialized, creating minimal instance")
            from server import PromptServer
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            server_instance = PromptServer(loop)
            server.PromptServer.instance = server_instance
        
        # Create execution instance
        from execution import PromptExecutor, validate_prompt
        
        # Wrap workflow in prompt format if needed
        if "prompt" not in workflow:
            prompt = {"prompt": workflow, "client_id": client_id}
        else:
            prompt = workflow
            if "client_id" not in prompt:
                prompt["client_id"] = client_id
        
        # Validate the prompt
        valid_result = validate_prompt(prompt["prompt"])
        if not valid_result[0]:
            return {
                "status": "error",
                "error": f"Workflow validation failed: {valid_result[1]}"
            }
        
        print("Workflow validated successfully")
        
        # Create executor
        executor = PromptExecutor(server.PromptServer.instance)
        
        # Track execution
        output_images = []
        output_dir = folder_paths.get_output_directory()
        
        # Get list of files before execution
        files_before = set(os.listdir(output_dir)) if os.path.exists(output_dir) else set()
        
        # Execute the workflow
        print("Starting workflow execution...")
        start_time = time.time()
        
        # Execute
        result = executor.execute(
            prompt["prompt"],
            prompt_id=str(uuid.uuid4()),
            extra_data={},
            execute_outputs=[]
        )
        
        execution_time = time.time() - start_time
        print(f"Workflow execution completed in {execution_time:.2f}s")
        
        # Get list of files after execution
        files_after = set(os.listdir(output_dir)) if os.path.exists(output_dir) else set()
        new_files = files_after - files_before
        
        print(f"New files generated: {len(new_files)}")
        
        # Collect output images
        if return_images and new_files:
            for filename in sorted(new_files):
                filepath = os.path.join(output_dir, filename)
                
                # Only process image files
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    try:
                        with open(filepath, 'rb') as f:
                            image_data = f.read()
                            image_b64 = base64.b64encode(image_data).decode('utf-8')
                            
                            output_images.append({
                                "filename": filename,
                                "data": image_b64,
                                "type": "image"
                            })
                        print(f"Encoded image: {filename}")
                    except Exception as e:
                        print(f"Error encoding image {filename}: {e}")
        
        return {
            "status": "success",
            "message": "Workflow executed successfully",
            "execution_time": round(execution_time, 2),
            "outputs": output_images if return_images else [],
            "output_files": list(new_files),
            "client_id": client_id
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error executing workflow: {e}")
        print(error_trace)
        
        return {
            "status": "error",
            "error": str(e),
            "trace": error_trace
        }


def handler(event):
    """
    RunPod handler function
    
    Expected input format:
    {
        "input": {
            "workflow": {...},          # ComfyUI workflow JSON (required)
            "return_images": true,      # Whether to return base64 images (default: true)
            "client_id": "optional-id"  # Optional client ID
        }
    }
    
    Returns:
    {
        "status": "success" | "error",
        "outputs": [...],               # Base64 encoded images (if return_images=true)
        "output_files": [...],          # List of generated files
        "execution_time": 12.34,        # Execution time in seconds
        "client_id": "...",             # Client ID used
        "error": "..."                  # Error message (if status=error)
    }
    """
    try:
        print("=" * 80)
        print("RunPod Handler - New Request")
        print("=" * 80)
        
        # Get input data
        input_data = event.get("input", {})
        
        if not input_data:
            return {
                "status": "error",
                "error": "No input data provided"
            }
        
        # Extract parameters
        workflow = input_data.get("workflow")
        return_images = input_data.get("return_images", True)
        client_id = input_data.get("client_id")
        
        if not workflow:
            return {
                "status": "error",
                "error": "No workflow provided in input"
            }
        
        print(f"Workflow nodes: {len(workflow)}")
        print(f"Return images: {return_images}")
        
        # Execute the workflow
        result = execute_workflow(
            workflow=workflow,
            client_id=client_id,
            return_images=return_images
        )
        
        print("=" * 80)
        print(f"Request completed: {result['status']}")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Handler error: {e}")
        print(error_trace)
        
        return {
            "status": "error",
            "error": f"Handler error: {str(e)}",
            "trace": error_trace
        }


# Initialize environment on container start
print("Initializing ComfyUI for RunPod...")
setup_environment()
print("Initialization complete!")


if __name__ == "__main__":
    # Start the RunPod serverless handler
    print("Starting RunPod serverless handler...")
    runpod.serverless.start({"handler": handler})

