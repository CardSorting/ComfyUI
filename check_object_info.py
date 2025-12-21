
import requests
import json

API_URL = "https://cardsorting--comfyui-api-web.modal.run"

def check_object_info():
    try:
        response = requests.get(f"{API_URL}/object_info")
        response.raise_for_status()
        info = response.json()
        
        nodes_to_check = ["UNETLoader", "CLIPLoader", "VAELoader"]
        
        for node in nodes_to_check:
            if node in info:
                print(f"\n--- {node} ---")
                print(json.dumps(info[node]['input'], indent=2))
            else:
                print(f"\n❌ {node} not found in object_info")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_object_info()
