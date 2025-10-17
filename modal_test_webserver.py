"""
Minimal test to verify Modal's web_server decorator works
"""
import modal

app = modal.App("test-webserver")

image = modal.Image.debian_slim(python_version="3.11")

@app.function(image=image, gpu="A10G")
@modal.web_server(8000, startup_timeout=30)
def simple_server():
    """Test if Modal's web_server works at all"""
    import subprocess
    
    print("Starting simple HTTP server on port 8000...")
    
    # Start a simple Python HTTP server
    subprocess.run([
        "python", "-m", "http.server", "8000", "--bind", "0.0.0.0"
    ], check=True)

@app.local_entrypoint()
def main():
    print("Test deployment")
    print("Run: modal deploy modal_test_webserver.py")
    print("Endpoint: https://{workspace}--test-webserver-simple-server.modal.run")

