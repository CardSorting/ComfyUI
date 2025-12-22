#!/usr/bin/env python3
"""
Test Endlustria Lumica Workflow
"""
import requests
import json
import time
import sys

# Replace with your actual workspace domain if different
# The user's workspace domain can be inferred from recent logs or commands, 
# or we can try to grab it from the modal deploy output.
# For now, using the one from test_workflow_simple.py
ENDPOINT = "https://cardsorting--comfyui-api-debug-fix-v3-web-v3.modal.run"

def main():
    # Load workflow
    print("📄 Loading Endlustria workflow...")
    with open("test_workflow_endlustria.json") as f:
        workflow = json.load(f)
    print(f"✓ Loaded workflow with {len(workflow)} nodes\n")
    
    # Submit workflow
    print(f"🚀 Submitting workflow to {ENDPOINT}...")
    try:
        response = requests.post(
            f"{ENDPOINT}/prompt",
            json={"prompt": workflow},
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    if response.status_code != 200:
        print(f"❌ Failed: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    result = response.json()
    print(f"✓ Workflow queued!")
    print(f"  Prompt ID: {result.get('prompt_id')}")
    print(f"  Queue number: {result.get('number')}\n")
    
    prompt_id = result.get('prompt_id')
    
    # Monitor execution
    print("⏳ Waiting for execution...")
    start_time = time.time()
    for i in range(120):  # Check for up to 2 minutes
        if time.time() - start_time > 120:
            break
            
        time.sleep(2)
        
        try:
            # Check history
            history_url = f"{ENDPOINT}/history/{prompt_id}"
            history_resp = requests.get(history_url)
            
            if history_resp.status_code == 200:
                history_data = history_resp.json()
                if prompt_id in history_data:
                    print(f"\n✅ Execution completed!")
                    exec_info = history_data[prompt_id]
                    
                    if 'outputs' in exec_info:
                        print(f"\n📁 Outputs:")
                        for node_id, output in exec_info['outputs'].items():
                            print(f"  Node {node_id}: {output}")
                            if 'images' in output:
                                for img in output['images']:
                                    fname = img.get('filename')
                                    print(f"  Image: {fname}")
                                    
                    return
        except Exception as e:
            print(f"Warning: Error checking status: {e}")
            
        print(f"  Checking status... {i*2}s", end='\r')
    
    print(f"\n⚠️  Timeout or processing took longer than expected.")
    print(f"   Check history: curl {ENDPOINT}/history/{prompt_id}")

if __name__ == "__main__":
    main()
