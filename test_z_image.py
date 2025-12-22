import json
import requests
import time
import sys
import os

ENDPOINT = "https://cardsorting--comfyui-api-debug-fix-v4-web-v3.modal.run"

def run_test():
    with open("z_image_turbo_workflow.json", "r") as f:
        workflow = json.load(f)

    # Clean up workflow for API
    # The API expects "prompt": { node_id: { inputs: ..., class_type: ... } }
    # My workflow file seems to be in API format (keys are node IDs)
    
    print(f"🚀 Sending workflow to {ENDPOINT}...")
    
    payload = {
        "prompt": workflow,
        "wait_for_completion": True,
        "client_id": "test_script_z_image"
    }
    
    try:
        response = requests.post(f"{ENDPOINT}/prompt", json=payload, timeout=600)
        response.raise_for_status()
        result = response.json()
        
        print(json.dumps(result, indent=2))
        
        if result.get("execution", {}).get("status") == "completed":
            print("\n✅ Generation successful!")
            # Save outputs info
            outputs = result.get("execution", {}).get("outputs", {})
            for node_id, output in outputs.items():
                if "images" in output:
                    for img in output["images"]:
                        print(f"Generated image: {img['filename']}")
                        # Try to download it
                        filename = img['filename']
                        res = requests.get(f"{ENDPOINT}/outputs/{filename}")
                        if res.status_code == 200:
                            with open(filename, "wb") as f:
                                f.write(res.content)
                            print(f"Saved to {filename}")
        else:
            print("\n❌ Generation failed or timed out.")
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Server response: {e.response.text}")

if __name__ == "__main__":
    run_test()
