#!/usr/bin/env python3
"""
Simple workflow tester that shows step-by-step execution
"""
import requests
import json
import time
import sys

ENDPOINT = "https://cardsorting--comfyui-api-web-dev.modal.run"

def main():
    # Load workflow
    print("📄 Loading workflow...")
    with open("test_workflow_sdxl_turbo.json") as f:
        workflow = json.load(f)
    print(f"✓ Loaded workflow with {len(workflow)} nodes\n")
    
    # Submit workflow
    print("🚀 Submitting workflow...")
    response = requests.post(
        f"{ENDPOINT}/prompt",
        json={"prompt": workflow},
        timeout=30
    )
    
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
    for i in range(60):  # Check for up to 60 seconds
        time.sleep(2)
        
        # Check queue
        queue = requests.get(f"{ENDPOINT}/queue").json()
        running = len(queue.get('queue_running', []))
        pending = len(queue.get('queue_pending', []))
        
        # Check history
        history = requests.get(f"{ENDPOINT}/history").json()
        
        if prompt_id and prompt_id in history:
            print(f"\n✅ Execution completed!")
            exec_info = history[prompt_id]
            
            if 'status' in exec_info and exec_info['status']:
                status = exec_info['status']
                print(f"  Status: {status.get('status_str', 'unknown')}")
                if status.get('messages'):
                    print(f"  Messages: {status['messages']}")
            
            if 'outputs' in exec_info:
                print(f"\n📁 Outputs:")
                for node_id, output in exec_info['outputs'].items():
                    print(f"  Node {node_id}: {output}")
            
            return
        
        print(f"  [{i*2}s] Queue - Running: {running}, Pending: {pending}", end='\r')
    
    print(f"\n⚠️  Timeout - workflow may still be processing")
    print(f"   Check history: curl {ENDPOINT}/history/{prompt_id}")

if __name__ == "__main__":
    main()

