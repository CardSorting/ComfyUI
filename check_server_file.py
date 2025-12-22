import requests
import json

ENDPOINT = "https://cardsorting--comfyui-api-debug-fix-v4-web-v3.modal.run"

def check_file():
    payload = {"path": "comfy/text_encoders/qwen_image.py"}
    try:
        response = requests.post(f"{ENDPOINT}/debug/read_file", json=payload)
        response.raise_for_status()
        content = response.json().get("content", "")
        print("Server file content (partial):")
        # Find intermediate_size
        for line in content.splitlines():
            if "intermediate_size" in line:
                print(f"FOUND: {line.strip()}")
                
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Server response: {e.response.text}")

if __name__ == "__main__":
    check_file()
