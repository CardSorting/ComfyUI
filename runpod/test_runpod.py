#!/usr/bin/env python3
"""
Test script for RunPod Serverless ComfyUI deployment

Usage:
    python runpod/test_runpod.py YOUR_ENDPOINT_ID YOUR_API_KEY
    
Or set environment variables:
    export RUNPOD_ENDPOINT_ID=your_endpoint_id
    export RUNPOD_API_KEY=your_api_key
    python runpod/test_runpod.py
"""

import requests
import json
import time
import sys
import os
from pathlib import Path


def create_simple_workflow():
    """Create a simple SDXL workflow for testing"""
    # This is a basic SDXL workflow
    # You should replace this with your actual workflow
    workflow = {
        "3": {
            "inputs": {
                "seed": 42,
                "steps": 20,
                "cfg": 8.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "4": {
            "inputs": {
                "ckpt_name": "sd_xl_turbo_1.0_fp16.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "5": {
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {
                "text": "beautiful landscape, mountains, sunset, highly detailed",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {
                "text": "blurry, low quality, distorted",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            },
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["8", 0]
            },
            "class_type": "SaveImage"
        }
    }
    
    return workflow


def test_runpod_endpoint(endpoint_id, api_key, workflow=None):
    """
    Test a RunPod serverless endpoint
    
    Args:
        endpoint_id: Your RunPod endpoint ID
        api_key: Your RunPod API key
        workflow: ComfyUI workflow dict (optional, uses default if not provided)
    """
    
    print("=" * 80)
    print("RunPod Serverless ComfyUI Test")
    print("=" * 80)
    print(f"Endpoint ID: {endpoint_id}")
    print("")
    
    # Use default workflow if none provided
    if workflow is None:
        print("Using default SDXL Turbo workflow...")
        workflow = create_simple_workflow()
    
    # RunPod API endpoints
    base_url = "https://api.runpod.ai/v2"
    run_url = f"{base_url}/{endpoint_id}/run"
    status_url_template = f"{base_url}/{endpoint_id}/status"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare request payload
    payload = {
        "input": {
            "workflow": workflow,
            "return_images": True
        }
    }
    
    print("Step 1: Submitting workflow to RunPod...")
    print("")
    
    try:
        # Submit the job
        start_time = time.time()
        response = requests.post(run_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"✗ Error submitting job: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        job_data = response.json()
        job_id = job_data.get("id")
        
        if not job_id:
            print(f"✗ No job ID returned: {job_data}")
            return False
        
        print(f"✓ Job submitted successfully!")
        print(f"Job ID: {job_id}")
        print("")
        
        # Poll for results
        print("Step 2: Waiting for job to complete...")
        print("")
        
        status_url = f"{status_url_template}/{job_id}"
        max_wait = 300  # 5 minutes
        poll_interval = 2  # seconds
        elapsed = 0
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            # Check status
            status_response = requests.get(status_url, headers={"Authorization": f"Bearer {api_key}"})
            
            if status_response.status_code != 200:
                print(f"✗ Error checking status: {status_response.status_code}")
                continue
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            print(f"Status: {status} (elapsed: {elapsed}s)")
            
            if status == "COMPLETED":
                total_time = time.time() - start_time
                print("")
                print("✓ Job completed successfully!")
                print(f"Total time: {total_time:.2f}s")
                print("")
                
                # Get output
                output = status_data.get("output", {})
                
                if output.get("status") == "error":
                    print(f"✗ Workflow execution error: {output.get('error')}")
                    if "trace" in output:
                        print(f"Trace: {output['trace']}")
                    return False
                
                print("=" * 80)
                print("Results:")
                print("=" * 80)
                print(f"Status: {output.get('status')}")
                print(f"Execution time: {output.get('execution_time')}s")
                print(f"Output files: {len(output.get('output_files', []))}")
                
                if output.get('outputs'):
                    print(f"Images returned: {len(output['outputs'])}")
                    
                    # Save images
                    output_dir = Path("runpod_test_output")
                    output_dir.mkdir(exist_ok=True)
                    
                    for idx, img_data in enumerate(output['outputs']):
                        filename = img_data.get('filename', f'output_{idx}.png')
                        filepath = output_dir / filename
                        
                        # Decode and save
                        import base64
                        img_bytes = base64.b64decode(img_data['data'])
                        with open(filepath, 'wb') as f:
                            f.write(img_bytes)
                        
                        print(f"  ✓ Saved: {filepath}")
                
                print("")
                print("=" * 80)
                print("Test PASSED ✓")
                print("=" * 80)
                return True
            
            elif status == "FAILED":
                error = status_data.get("error", "Unknown error")
                print("")
                print(f"✗ Job failed: {error}")
                print("")
                print("=" * 80)
                print("Test FAILED ✗")
                print("=" * 80)
                return False
            
            elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                # Still running, continue polling
                continue
            
            else:
                print(f"Unknown status: {status}")
        
        # Timeout
        print("")
        print(f"✗ Timeout after {max_wait}s")
        print("")
        print("=" * 80)
        print("Test FAILED ✗")
        print("=" * 80)
        return False
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    
    # Get credentials from args or environment
    if len(sys.argv) >= 3:
        endpoint_id = sys.argv[1]
        api_key = sys.argv[2]
    else:
        endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")
        api_key = os.environ.get("RUNPOD_API_KEY")
    
    if not endpoint_id or not api_key:
        print("Usage:")
        print("  python runpod/test_runpod.py ENDPOINT_ID API_KEY")
        print("")
        print("Or set environment variables:")
        print("  export RUNPOD_ENDPOINT_ID=your_endpoint_id")
        print("  export RUNPOD_API_KEY=your_api_key")
        print("  python runpod/test_runpod.py")
        sys.exit(1)
    
    # Load custom workflow if provided
    workflow = None
    if len(sys.argv) >= 4:
        workflow_file = sys.argv[3]
        if os.path.exists(workflow_file):
            print(f"Loading workflow from: {workflow_file}")
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
    
    # Run test
    success = test_runpod_endpoint(endpoint_id, api_key, workflow)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

