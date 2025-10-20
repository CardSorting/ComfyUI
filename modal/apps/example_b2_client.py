"""
Example ComfyUI client with Backblaze B2 support
This can be used as a reference or dropped into your Django app
"""

import requests
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class ComfyUIB2Client:
    """
    ComfyUI client that automatically uploads to Backblaze B2
    
    Example usage:
        client = ComfyUIB2Client("https://your-modal-endpoint.modal.run")
        
        workflow = {...}  # Your ComfyUI workflow
        result = client.execute(workflow)
        
        # Get B2 URLs
        images = client.get_image_urls(result)
        for img in images:
            print(f"URL: {img['url']}")
    """
    
    def __init__(self, endpoint: str):
        """
        Initialize client
        
        Args:
            endpoint: Your Modal ComfyUI endpoint URL
        """
        self.endpoint = endpoint.rstrip('/')
        self.session = requests.Session()
    
    def execute(
        self, 
        workflow: dict, 
        wait: bool = True,
        timeout: int = 600
    ) -> dict:
        """
        Execute a ComfyUI workflow and get B2 URLs
        
        Args:
            workflow: The ComfyUI workflow dictionary
            wait: If True, waits for completion and uploads to B2
            timeout: Maximum time to wait in seconds
        
        Returns:
            Dict with execution results and B2 URLs
        """
        try:
            logger.info("Executing ComfyUI workflow...")
            
            response = self.session.post(
                f"{self.endpoint}/prompt",
                json={
                    "prompt": workflow,
                    "wait_for_completion": wait,
                    "upload_to_b2": True
                },
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Log execution details
            if "execution" in result:
                exec_time = result["execution"].get("execution_time", 0)
                logger.info(f"Execution completed in {exec_time:.2f}s")
                
                if "b2_uploads" in result["execution"]:
                    upload_count = sum(
                        len(data.get("uploads", []))
                        for data in result["execution"]["b2_uploads"].values()
                    )
                    logger.info(f"Uploaded {upload_count} files to B2")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def get_image_urls(self, result: dict) -> List[Dict[str, any]]:
        """
        Extract B2 image URLs from execution result
        
        Args:
            result: Result from execute()
        
        Returns:
            List of dicts with image info:
            [
                {
                    "url": "https://...",
                    "size": 2457600,
                    "filename": "ComfyUI_00001_.png",
                    "b2_key": "generations/2025/10/20/...",
                    "node_id": "9"
                }
            ]
        """
        images = []
        
        if "execution" not in result:
            logger.warning("No execution data in result")
            return images
        
        execution = result["execution"]
        
        # Check for errors
        if execution.get("status") == "error":
            error_msg = execution.get("error", "Unknown error")
            logger.error(f"Execution failed: {error_msg}")
            return images
        
        # Extract B2 uploads
        if "b2_uploads" in execution:
            b2_uploads = execution["b2_uploads"]
            
            for node_id, upload_data in b2_uploads.items():
                if upload_data.get("type") == "images":
                    for image in upload_data.get("uploads", []):
                        if "url" in image:
                            images.append({
                                "url": image["url"],
                                "size": image.get("size"),
                                "filename": image.get("filename"),
                                "b2_key": image.get("b2_key"),
                                "node_id": node_id
                            })
        
        return images
    
    def check_health(self) -> dict:
        """Check ComfyUI service health"""
        try:
            response = self.session.get(f"{self.endpoint}/", timeout=10)
            response.raise_for_status()
            return {
                "status": "healthy",
                "info": response.json()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_b2_status(self) -> dict:
        """Check if Backblaze B2 is enabled and working"""
        try:
            response = self.session.get(f"{self.endpoint}/b2/status", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"B2 status check failed: {e}")
            return {
                "enabled": False,
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize client
    client = ComfyUIB2Client("https://cardsorting--comfyui-api-web.modal.run")
    
    # Check health
    health = client.check_health()
    print(f"Service status: {health['status']}")
    
    # Check B2
    b2_status = client.check_b2_status()
    if b2_status.get("enabled"):
        print(f"B2 enabled: {b2_status['storage_info']['bucket']}")
    else:
        print("B2 not enabled")
    
    # Example workflow (replace with your actual workflow)
    example_workflow = {
        "3": {
            "inputs": {
                "seed": 42,
                "steps": 20,
                "cfg": 8.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        # ... rest of your workflow
    }
    
    # Execute (commented out - uncomment to test)
    # result = client.execute(example_workflow)
    # images = client.get_image_urls(result)
    # 
    # for img in images:
    #     print(f"Image URL: {img['url']}")
    #     print(f"Size: {img['size'] / 1024:.1f} KB")

