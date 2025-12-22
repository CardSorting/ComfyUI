import requests
import json

ENDPOINT = "https://cardsorting--comfyui-api-debug-fix-v4-web-v3.modal.run"

def check_file():
    payload = {"path": "comfy/model_detection.py"}
    try:
        response = requests.post(f"{ENDPOINT}/debug/read_file", json=payload)
        response.raise_for_status()
        content = response.json().get("content", "")
        print("Server file content (partial):")
        
        # Check order of checks
        lines = content.splitlines()
        z_image_line = -1
        lumina_line = -1
        
        for i, line in enumerate(lines):
            if "Omnigen2 Variant (z_image_turbo)" in line:
                z_image_line = i
                print(f"FOUND Z-Image-Turbo check at line {i}")
            if "Lumina 2" in line and "Omnigen2" not in line: # Avoid confusing comments
                 # Simple heuristic
                 if "if '{}cap_embedder.1.weight'" in line or "Lumina 2" in line:
                     # Be careful matching
                     pass
        
        for i, line in enumerate(lines):
             if "Omnigen2 Variant (z_image_turbo)" in line:
                 print(f"Z-Image-Turbo Block Start: Line {i}")
             if "Lumina 2" in line:
                 print(f"Lumina 2 Block Start (Approx): Line {i}")
                 
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Server response: {e.response.text}")

if __name__ == "__main__":
    check_file()
