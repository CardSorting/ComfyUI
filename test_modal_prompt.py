#!/usr/bin/env python3
"""
Test script to submit a prompt to ComfyUI Modal deployment and get output
"""

import requests
import json
import time
import sys

ENDPOINT = "https://cardsorting--comfyui-api-web.modal.run"

def create_test_workflow(model_name="2440705.safetensors", prompt_text="a beautiful landscape with mountains and sunset, highly detailed, professional photography", negative_prompt="blurry, low quality, distorted, bad anatomy"):
    """Create a simple test workflow"""
    workflow = {
        "1": {
            "inputs": {
                "ckpt_name": model_name
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "text": prompt_text,
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "3": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "5": {
            "inputs": {
                "seed": int(time.time()),
                "steps": 20,
                "cfg": 7.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            },
            "class_type": "KSampler"
        },
        "6": {
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            },
            "class_type": "VAEDecode"
        },
        "7": {
            "inputs": {
                "filename_prefix": "test_output",
                "images": ["6", 0]
            },
            "class_type": "SaveImage"
        }
    }
    return workflow

def submit_prompt(workflow, wait_for_completion=True):
    """Submit a prompt to the API"""
    print(f"🚀 Submitting prompt to {ENDPOINT}...")
    print(f"   Model: {workflow['1']['inputs']['ckpt_name']}")
    print(f"   Prompt: {workflow['2']['inputs']['text'][:60]}...")
    
    payload = {
        "prompt": workflow,
        "wait_for_completion": wait_for_completion
    }
    
    try:
        response = requests.post(
            f"{ENDPOINT}/prompt",
            json=payload,
            timeout=600  # 10 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Full response: {result}")
            
            # Check for errors first
            if result.get('error'):
                print(f"❌ API Error: {result.get('error')}")
                if result.get('node_errors'):
                    print(f"   Node errors: {result.get('node_errors')}")
                return None, result
            
            prompt_id = result.get('prompt_id')
            if prompt_id:
                print(f"✅ Prompt queued successfully!")
                print(f"   Prompt ID: {prompt_id}")
            else:
                print(f"⚠️  No prompt_id in response")
            return prompt_id, result
        else:
            print(f"❌ Failed to submit prompt: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None, None
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - the workflow may be taking longer than expected")
        return None, None
    except Exception as e:
        print(f"❌ Error submitting prompt: {e}")
        return None, None

def check_status(prompt_id):
    """Check the status of a prompt"""
    try:
        response = requests.get(f"{ENDPOINT}/history/{prompt_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"⚠️  Error checking status: {e}")
        return None

def wait_for_completion(prompt_id, timeout=600):
    """Wait for prompt to complete"""
    print(f"\n⏳ Waiting for completion (timeout: {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        history = check_status(prompt_id)
        
        if history and prompt_id in history:
            execution_data = history[prompt_id]
            
            # Check if completed
            if 'outputs' in execution_data:
                print(f"\n✅ Workflow completed successfully!")
                execution_time = time.time() - start_time
                print(f"   Execution time: {execution_time:.1f}s")
                
                # Show outputs
                outputs = execution_data.get('outputs', {})
                if outputs:
                    print(f"\n📸 Generated images:")
                    for node_id, node_output in outputs.items():
                        if 'images' in node_output:
                            for img_info in node_output['images']:
                                filename = img_info.get('filename', 'unknown')
                                subfolder = img_info.get('subfolder', '')
                                print(f"   • {subfolder}/{filename}" if subfolder else f"   • {filename}")
                
                return True, execution_data
            elif 'status' in execution_data:
                status = execution_data['status']
                if status.get('status_str') == 'error':
                    print(f"\n❌ Workflow failed!")
                    messages = status.get('messages', [])
                    for msg in messages:
                        print(f"   Error: {msg}")
                    return False, execution_data
        
        # Check queue
        try:
            queue_response = requests.get(f"{ENDPOINT}/queue", timeout=5)
            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                running = queue_data.get('queue_running', [])
                pending = queue_data.get('queue_pending', [])
                
                # Check if our prompt is still in queue
                still_queued = any(
                    item[1] == prompt_id 
                    for item in running + pending
                )
                
                if not still_queued and prompt_id not in (history or {}):
                    print(f"\n⚠️  Prompt not found in queue or history")
                    return None, None
        except:
            pass
        
        time.sleep(2)
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0:
            print(f"   Still running... ({elapsed}s)", end='\r')
    
    print(f"\n⏱️  Timeout reached ({timeout}s)")
    return None, None

def get_output_file(filename):
    """Download an output file"""
    try:
        response = requests.get(f"{ENDPOINT}/outputs/{filename}", timeout=30)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"⚠️  Error downloading file: {e}")
        return None

def main():
    """Main function"""
    print("=" * 70)
    print("ComfyUI Modal - Test Prompt")
    print("=" * 70)
    
    # Get prompt text from command line or use default
    prompt_text = sys.argv[1] if len(sys.argv) > 1 else "a beautiful landscape with mountains and sunset, highly detailed, professional photography"
    
    # Create workflow
    workflow = create_test_workflow(prompt_text=prompt_text)
    
    # Submit prompt
    prompt_id, result = submit_prompt(workflow, wait_for_completion=False)
    
    if not prompt_id:
        print("\n❌ Failed to submit prompt. Exiting.")
        return
    
    # Wait for completion
    success, execution_data = wait_for_completion(prompt_id)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ Test completed successfully!")
        print("=" * 70)
        
        # Show how to access the image
        outputs = execution_data.get('outputs', {})
        if outputs:
            print("\n📥 To download the generated image:")
            for node_id, node_output in outputs.items():
                if 'images' in node_output:
                    for img_info in node_output['images']:
                        filename = img_info.get('filename', 'unknown')
                        print(f"   curl {ENDPOINT}/outputs/{filename} -o {filename}")
    elif success is False:
        print("\n" + "=" * 70)
        print("❌ Test failed!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("⚠️  Test status unknown")
        print("=" * 70)
        print(f"   Check status: curl {ENDPOINT}/history/{prompt_id}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

