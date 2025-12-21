
import json
import requests
import sys
import time

API_URL = "https://cardsorting--comfyui-api-debug-web.modal.run"

def test_workflow(workflow_file):
    print(f"Loading workflow from {workflow_file}...")
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)

    payload = {
        "prompt": workflow,
        "wait_for_completion": True
    }

    print(f"Sending request to {API_URL}/prompt...")
    start_time = time.time()
    try:
        response = requests.post(f"{API_URL}/prompt", json=payload)
        response.raise_for_status()
        result = response.json()
        
        duration = time.time() - start_time
        print(f"Request completed in {duration:.2f} seconds")
        
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        
        if 'node_errors' in result and result['node_errors']:
            print("\n❌ Node Errors detected!")
            sys.exit(1)
            
        if 'execution' in result and result['execution']['status'] == 'completed':
            print("\n✅ Workflow executed successfully!")
        else:
            print("\n⚠️ Workflow finished but status is not 'completed'")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error sending request: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_workflow.py <workflow_json>")
        sys.exit(1)
    
    test_workflow(sys.argv[1])
