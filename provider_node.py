#!/usr/bin/env python3
"""
Provider Node - GPU compute provider for the decentralized cluster
Integrated directly into ComfyUI container
"""

import os
import sys
import time
import json
import base64
import logging
import threading
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import torch
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProviderNode:
    """GPU Provider Node that pulls and executes jobs using ComfyUI API"""
    
    def __init__(
        self,
        coordinator_url: str,
        provider_id: str,
        wallet_address: str,
        gpu_type: str,
        gpu_memory_gb: int,
        supported_models: list,
        max_concurrent_jobs: int = 1,
        comfyui_url: str = "http://localhost:8188",
    ):
        self.coordinator_url = coordinator_url
        self.provider_id = provider_id
        self.wallet_address = wallet_address
        self.gpu_type = gpu_type
        self.gpu_memory_gb = gpu_memory_gb
        self.supported_models = supported_models
        self.max_concurrent_jobs = max_concurrent_jobs
        self.comfyui_url = comfyui_url
        self.comfyui_api_url = f"{comfyui_url}/api"
        
        # State
        self.current_jobs = 0
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.running = False
        self.thread = None
        
        logger.info(f"Provider initialized: {provider_id}")
        logger.info(f"Device: {self.device}")
        logger.info(f"GPU: {gpu_type} ({gpu_memory_gb}GB)")
        logger.info(f"Supported models: {', '.join(supported_models)}")
        logger.info(f"ComfyUI API: {self.comfyui_api_url}")
    
    def register(self) -> bool:
        """Register provider with coordinator"""
        url = f"{self.coordinator_url}/api/v1/provider/register"
        payload = {
            "wallet_address": self.wallet_address,
            "gpu_type": self.gpu_type,
            "gpu_memory_gb": self.gpu_memory_gb,
            "supported_models": self.supported_models,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "base_rate": 100000,  # 0.0001 SOL per job
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.provider_id = data["id"]
            logger.info(f"✅ Registered successfully: {self.provider_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register: {e}")
            return False
    
    def heartbeat(self) -> bool:
        """Send heartbeat to coordinator"""
        url = f"{self.coordinator_url}/api/v1/provider/heartbeat"
        payload = {
            "provider_id": self.provider_id,
            "current_jobs": self.current_jobs,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            return False
    
    def pull_job(self) -> Optional[Dict[str, Any]]:
        """Pull next job from coordinator"""
        url = f"{self.coordinator_url}/api/v1/provider/jobs/next"
        params = {"provider_id": self.provider_id}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("job"):
                return data["job"]
            return None
        except Exception as e:
            logger.warning(f"Failed to pull job: {e}")
            return None
    
    def submit_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Submit job result to coordinator"""
        url = f"{self.coordinator_url}/api/v1/provider/jobs/{job_id}/result"
        payload = {
            "provider_id": self.provider_id,
            "result": result,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            logger.info(f"✅ Result submitted for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to submit result: {e}")
            return False
    
    def wait_for_comfyui_ready(self, timeout: int = 60) -> bool:
        """Wait for ComfyUI API to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to access the queue endpoint as a health check
                response = requests.get(f"{self.comfyui_api_url}/queue", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ ComfyUI API is ready")
                    return True
            except Exception as e:
                logger.debug(f"ComfyUI not ready yet: {e}")
            time.sleep(2)
        
        logger.error("❌ ComfyUI API not ready after timeout")
        return False
    
    def execute_workflow(self, workflow: Dict[str, Any], timeout: int = 600) -> Dict[str, Any]:
        """Execute a ComfyUI workflow and wait for completion"""
        try:
            # Submit workflow
            prompt_url = f"{self.comfyui_api_url}/prompt"
            payload = {
                "prompt": workflow,
                "client_id": f"provider_{self.provider_id}"
            }
            
            logger.info("Submitting workflow to ComfyUI...")
            response = requests.post(prompt_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            prompt_id = result.get("prompt_id")
            if not prompt_id:
                raise Exception(f"No prompt_id in response: {result}")
            
            logger.info(f"Workflow submitted, prompt_id: {prompt_id}")
            
            # Wait for completion
            start_time = time.time()
            history_url = f"{self.comfyui_url}/history/{prompt_id}"
            
            while time.time() - start_time < timeout:
                time.sleep(2)
                
                try:
                    history_response = requests.get(history_url, timeout=10)
                    if history_response.status_code == 200:
                        history = history_response.json()
                        
                        if prompt_id in history:
                            exec_data = history[prompt_id]
                            
                            # Check for completion
                            if "outputs" in exec_data:
                                elapsed = time.time() - start_time
                                logger.info(f"✅ Workflow completed in {elapsed:.2f}s")
                                
                                # Extract images from outputs
                                images_base64 = []
                                for node_id, node_output in exec_data["outputs"].items():
                                    if "images" in node_output:
                                        for img_info in node_output["images"]:
                                            filename = img_info.get("filename")
                                            subfolder = img_info.get("subfolder", "")
                                            
                                            # Download image
                                            if subfolder:
                                                image_url = f"{self.comfyui_url}/output/{subfolder}/{filename}"
                                            else:
                                                image_url = f"{self.comfyui_url}/output/{filename}"
                                            
                                            img_response = requests.get(image_url, timeout=30)
                                            if img_response.status_code == 200:
                                                # Convert to base64
                                                img_base64 = base64.b64encode(img_response.content).decode()
                                                images_base64.append({
                                                    "filename": filename,
                                                    "base64": img_base64,
                                                    "content_type": "image/png"
                                                })
                                
                                return {
                                    "status": "success",
                                    "images": images_base64,
                                    "execution_time": elapsed,
                                    "outputs": exec_data.get("outputs", {})
                                }
                            
                            # Check for errors
                            if "status" in exec_data:
                                status = exec_data["status"]
                                if status.get("status_str") == "error":
                                    error_msg = "Unknown error"
                                    if "messages" in status:
                                        for msg in status["messages"]:
                                            if "execution_error" in msg:
                                                error_msg = msg["execution_error"].get("exception_message", error_msg)
                                    raise Exception(f"Workflow failed: {error_msg}")
                
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error checking status: {e}")
                    continue
            
            raise Exception(f"Workflow timeout after {timeout}s")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise
    
    def execute_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single job"""
        job_id = job["id"]
        workflow = job.get("workflow")
        
        if not workflow:
            raise Exception("No workflow in job")
        
        logger.info(f"Executing job {job_id}")
        logger.info(f"Workflow nodes: {len(workflow)}")
        
        try:
            # Execute workflow
            start_time = time.time()
            result = self.execute_workflow(workflow, timeout=600)
            elapsed = time.time() - start_time
            
            return {
                "status": "success",
                "images": result.get("images", []),
                "execution_time": elapsed,
                "workflow_outputs": result.get("outputs", {})
            }
            
        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def _run_loop(self):
        """Main provider loop (runs in background thread)"""
        logger.info("🚀 Provider node starting...")
        
        # Wait for ComfyUI to be ready
        if not self.wait_for_comfyui_ready():
            logger.error("ComfyUI not ready, exiting provider node")
            return
        
        # Register with coordinator
        if not self.register():
            logger.error("Failed to register, exiting")
            return
        
        logger.info("👂 Listening for jobs...")
        
        # Main loop
        poll_interval = 5  # seconds
        last_heartbeat = 0
        heartbeat_interval = 30  # seconds
        
        while self.running:
            try:
                # Send heartbeat
                current_time = time.time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.heartbeat()
                    last_heartbeat = current_time
                
                # Check if we have capacity
                if self.current_jobs >= self.max_concurrent_jobs:
                    time.sleep(poll_interval)
                    continue
                
                # Pull next job
                job = self.pull_job()
                
                if job:
                    logger.info(f"📦 Job received: {job['id']}")
                    self.current_jobs += 1
                    
                    try:
                        # Execute job
                        result = self.execute_job(job)
                        
                        # Submit result
                        self.submit_result(job["id"], result)
                        
                    except Exception as e:
                        logger.error(f"Job failed: {e}")
                        # Report failure to coordinator
                        self.submit_result(job["id"], {
                            "status": "error",
                            "error": str(e)
                        })
                    finally:
                        self.current_jobs -= 1
                    
                    # Short interval when processing jobs
                    time.sleep(1)
                else:
                    # No jobs available, wait longer
                    time.sleep(poll_interval)
                    
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(poll_interval)
        
        logger.info("Provider node stopped")
    
    def start(self):
        """Start the provider node in a background thread"""
        if self.running:
            logger.warning("Provider node already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Provider node started in background thread")
    
    def stop(self):
        """Stop the provider node"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Provider node stopped")


def create_provider_node() -> Optional[ProviderNode]:
    """Create and return a provider node instance from environment variables"""
    
    # Check if provider node is enabled
    if os.getenv("ENABLE_PROVIDER_NODE", "").lower() not in ("1", "true", "yes"):
        return None
    
    # Load configuration from environment
    coordinator_url = os.getenv("COORDINATOR_URL")
    wallet_address = os.getenv("WALLET_ADDRESS")
    
    if not coordinator_url or not wallet_address:
        logger.warning("Provider node disabled: COORDINATOR_URL or WALLET_ADDRESS not set")
        return None
    
    provider_id = os.getenv("PROVIDER_ID", "")
    comfyui_url = os.getenv("COMFYUI_URL", "http://localhost:8188")
    
    # GPU configuration
    gpu_type = os.getenv("GPU_TYPE", "Unknown")
    gpu_memory_gb = int(os.getenv("GPU_MEMORY_GB", "16"))
    
    # Detect GPU if available
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_type = gpu_name
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory // (1024**3)
        logger.info(f"Detected GPU: {gpu_name} ({gpu_memory_gb}GB)")
    else:
        logger.warning("No GPU detected, running on CPU")
    
    # Supported models
    supported_models = os.getenv(
        "SUPPORTED_MODELS",
        "runwayml/stable-diffusion-v1-5,stabilityai/stable-diffusion-xl-base-1.0"
    ).split(",")
    
    # Create provider node
    provider = ProviderNode(
        coordinator_url=coordinator_url,
        provider_id=provider_id,
        wallet_address=wallet_address,
        gpu_type=gpu_type,
        gpu_memory_gb=gpu_memory_gb,
        supported_models=supported_models,
        max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", "1")),
        comfyui_url=comfyui_url,
    )
    
    return provider


# Global provider node instance
_provider_node: Optional[ProviderNode] = None


def start_provider_node():
    """Start the provider node (called from main.py)"""
    global _provider_node
    
    _provider_node = create_provider_node()
    if _provider_node:
        _provider_node.start()
        logger.info("✅ Provider node enabled and started")
    else:
        logger.info("ℹ️  Provider node disabled (set ENABLE_PROVIDER_NODE=1 to enable)")


def stop_provider_node():
    """Stop the provider node"""
    global _provider_node
    
    if _provider_node:
        _provider_node.stop()
        _provider_node = None

