#!/usr/bin/env python3
"""
Example script showing how to use ComfyUI in headless mode via API
"""

import requests
import json
import time

class ComfyUIHeadlessClient:
    def __init__(self, base_url="http://localhost:8188"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def get_system_info(self):
        """Get system information"""
        response = requests.get(f"{self.api_url}/system_stats")
        return response.json()
    
    def get_object_info(self):
        """Get available node information"""
        response = requests.get(f"{self.api_url}/object_info")
        return response.json()
    
    def get_queue_status(self):
        """Get current queue status"""
        response = requests.get(f"{self.api_url}/queue")
        return response.json()
    
    def submit_prompt(self, prompt, client_id=None):
        """Submit a workflow prompt for execution"""
        data = {
            "prompt": prompt,
            "client_id": client_id or "headless_client"
        }
        response = requests.post(f"{self.api_url}/prompt", json=data)
        return response.json()
    
    def get_history(self, prompt_id=None):
        """Get execution history"""
        url = f"{self.api_url}/history"
        if prompt_id:
            url += f"/{prompt_id}"
        response = requests.get(url)
        return response.json()
    
    def interrupt(self):
        """Interrupt current execution"""
        response = requests.post(f"{self.api_url}/interrupt")
        return response.status_code == 200
    
    def free_memory(self, unload_models=False):
        """Free memory and optionally unload models"""
        data = {
            "unload_models": unload_models,
            "free_memory": True
        }
        response = requests.post(f"{self.api_url}/free", json=data)
        return response.status_code == 200

def example_usage():
    """Example of how to use the headless client"""
    print("ComfyUI Headless API Example")
    print("=" * 40)
    
    # Initialize client
    client = ComfyUIHeadlessClient()
    
    try:
        # Check if ComfyUI is running
        print("1. Checking system info...")
        system_info = client.get_system_info()
        print(f"   ComfyUI Version: {system_info['system']['comfyui_version']}")
        print(f"   Python Version: {system_info['system']['python_version']}")
        
        # Get available nodes
        print("\n2. Getting available nodes...")
        object_info = client.get_object_info()
        node_count = len(object_info)
        print(f"   Available nodes: {node_count}")
        
        # Get queue status
        print("\n3. Getting queue status...")
        queue_status = client.get_queue_status()
        print(f"   Queue running: {len(queue_status['queue_running'])}")
        print(f"   Queue pending: {len(queue_status['queue_pending'])}")
        
        # Example workflow (this would need to be a valid ComfyUI workflow)
        print("\n4. Example workflow submission...")
        example_workflow = {
            "1": {
                "inputs": {
                    "text": "a beautiful landscape",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Prompt)"
                }
            },
            "4": {
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.ckpt"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {
                    "title": "Load Checkpoint"
                }
            }
        }
        
        print("   Note: This is just an example workflow structure.")
        print("   In practice, you would need a complete, valid ComfyUI workflow.")
        
        # Uncomment the following lines to actually submit a workflow:
        # result = client.submit_prompt(example_workflow)
        # print(f"   Prompt submitted: {result}")
        
        print("\n✓ All API calls completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to ComfyUI server.")
        print("   Make sure ComfyUI is running in headless mode:")
        print("   python main.py --headless --listen 0.0.0.0 --port 8188")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    example_usage()
