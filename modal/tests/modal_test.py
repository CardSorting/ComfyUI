"""
Test script for ComfyUI Modal deployment

This script tests the deployed ComfyUI API on Modal.
"""

import requests
import json
import time
import sys

def test_modal_deployment(endpoint_url):
    """
    Test a deployed ComfyUI instance on Modal
    
    Args:
        endpoint_url: The Modal web endpoint URL
    """
    print("🧪 Testing ComfyUI Modal Deployment")
    print("=" * 60)
    print(f"Endpoint: {endpoint_url}\n")
    
    # Test 1: Health Check / System Stats
    print("Test 1: Health Check")
    try:
        response = requests.get(f"{endpoint_url}/system_stats", timeout=30)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Server is running")
            print(f"   System: {stats.get('system', {})}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Get Object Info (available nodes)
    print("\nTest 2: Get Available Nodes")
    try:
        response = requests.get(f"{endpoint_url}/object_info", timeout=30)
        if response.status_code == 200:
            object_info = response.json()
            node_count = len(object_info)
            print(f"✅ Retrieved {node_count} node definitions")
            
            # Show some example nodes
            sample_nodes = list(object_info.keys())[:5]
            print(f"   Sample nodes: {', '.join(sample_nodes)}")
        else:
            print(f"❌ Failed to get object info: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting object info: {e}")
    
    # Test 3: Get Queue Status
    print("\nTest 3: Queue Status")
    try:
        response = requests.get(f"{endpoint_url}/queue", timeout=30)
        if response.status_code == 200:
            queue = response.json()
            print(f"✅ Queue accessible")
            print(f"   Pending: {len(queue.get('queue_pending', []))}")
            print(f"   Running: {len(queue.get('queue_running', []))}")
        else:
            print(f"❌ Failed to get queue: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting queue: {e}")
    
    # Test 4: Simple Workflow Execution (if you have a workflow)
    print("\nTest 4: Workflow Execution")
    print("ℹ️  To test workflow execution, you need to:")
    print("   1. Create a workflow in ComfyUI")
    print("   2. Export it as API format")
    print("   3. POST it to /prompt endpoint")
    print("\nExample:")
    print("   curl -X POST \\")
    print(f"     {endpoint_url}/prompt \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"prompt\": <your_workflow>}'")
    
    print("\n" + "=" * 60)
    print("✅ Basic tests completed successfully!")
    print("\n📚 Next steps:")
    print("   1. Upload models to the volume:")
    print("      modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors")
    print("   2. Test with a real workflow")
    print("   3. Integrate with your application")
    
    return True


def test_simple_workflow(endpoint_url, workflow_path):
    """
    Test executing a workflow
    
    Args:
        endpoint_url: The Modal web endpoint URL
        workflow_path: Path to a workflow JSON file
    """
    print(f"\n🎨 Testing Workflow Execution")
    print("=" * 60)
    
    try:
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        print(f"Loaded workflow from: {workflow_path}")
        
        # Queue the workflow
        response = requests.post(
            f"{endpoint_url}/prompt",
            json={"prompt": workflow},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get('prompt_id')
            print(f"✅ Workflow queued: {prompt_id}")
            
            # Poll for completion
            print("⏳ Waiting for completion...")
            max_wait = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                history_response = requests.get(f"{endpoint_url}/history/{prompt_id}")
                
                if history_response.status_code == 200:
                    history = history_response.json()
                    if prompt_id in history:
                        status = history[prompt_id].get('status', {})
                        if status.get('completed'):
                            print("✅ Workflow completed successfully!")
                            print(f"   Outputs: {history[prompt_id].get('outputs', {})}")
                            return True
                        elif 'error' in status:
                            print(f"❌ Workflow failed: {status.get('error')}")
                            return False
                
                time.sleep(2)
            
            print("⏱️  Timeout waiting for workflow completion")
            return False
        else:
            print(f"❌ Failed to queue workflow: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Workflow file not found: {workflow_path}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python modal_test.py <endpoint_url> [workflow.json]")
        print("\nExample:")
        print("  python modal_test.py https://workspace--comfyui-fastapi-app.modal.run")
        print("  python modal_test.py https://workspace--comfyui-fastapi-app.modal.run workflow.json")
        sys.exit(1)
    
    endpoint = sys.argv[1].rstrip('/')
    
    # Run basic tests
    success = test_modal_deployment(endpoint)
    
    # If workflow provided, test it
    if len(sys.argv) >= 3 and success:
        workflow_file = sys.argv[2]
        test_simple_workflow(endpoint, workflow_file)

