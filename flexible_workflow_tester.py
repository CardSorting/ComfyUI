#!/usr/bin/env python3
"""
Flexible ComfyUI Workflow Tester

This script dynamically detects available models and creates workflows
based on what's actually available in the system, rather than hardcoding
specific model names.
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

class FlexibleWorkflowTester:
    def __init__(self, comfyui_url: str = "http://localhost:8188"):
        self.comfyui_url = comfyui_url
        self.available_models = {}
        self.available_custom_nodes = []
        
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models from ComfyUI API."""
        try:
            # Get model types
            response = requests.get(f"{self.comfyui_url}/models")
            if response.status_code == 200:
                model_types = response.json()
                print(f"Found model types: {model_types}")
                
                # Get models for each type
                for model_type in model_types:
                    if model_type in ["configs", "custom_nodes"]:
                        continue
                        
                    try:
                        response = requests.get(f"{self.comfyui_url}/models/{model_type}")
                        if response.status_code == 200:
                            models = response.json()
                            if models:  # Only add if there are models
                                self.available_models[model_type] = models
                                print(f"  {model_type}: {len(models)} models")
                    except Exception as e:
                        print(f"  Error getting {model_type} models: {e}")
                        
        except Exception as e:
            print(f"Error getting model types: {e}")
            
        return self.available_models
    
    def get_available_custom_nodes(self) -> List[str]:
        """Get available custom nodes from ComfyUI."""
        try:
            response = requests.get(f"{self.comfyui_url}/object_info")
            if response.status_code == 200:
                object_info = response.json()
                # Filter for custom nodes (nodes not in core ComfyUI)
                core_nodes = {
                    "CheckpointLoaderSimple", "CLIPTextEncode", "KSampler", "VAEDecode", 
                    "EmptyLatentImage", "PreviewImage", "LoadImage", "SaveImage"
                }
                
                custom_nodes = []
                for node_name, node_info in object_info.items():
                    if node_name not in core_nodes:
                        custom_nodes.append(node_name)
                        
                self.available_custom_nodes = custom_nodes
                print(f"Found {len(custom_nodes)} custom nodes")
                
        except Exception as e:
            print(f"Error getting custom nodes: {e}")
            
        return self.available_custom_nodes
    
    def create_basic_workflow(self) -> Dict[str, Any]:
        """Create a basic workflow using available models."""
        if not self.available_models.get("checkpoints"):
            raise ValueError("No checkpoint models available")
            
        # Use first available checkpoint
        checkpoint = self.available_models["checkpoints"][0]
        
        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": checkpoint
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "text": "a beautiful landscape, detailed, high quality, photorealistic",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "text": "blurry, low quality, distorted, bad anatomy",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "4": {
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "5": {
                "inputs": {
                    "seed": int(time.time()),
                    "steps": 20,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                },
                "class_type": "KSampler"
            },
            "6": {
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                },
                "class_type": "VAEDecode"
            },
            "7": {
                "inputs": {
                    "images": ["6", 0]
                },
                "class_type": "PreviewImage"
            }
        }
        
        return workflow
    
    def create_custom_node_workflow(self) -> Dict[str, Any]:
        """Create a workflow using available custom nodes."""
        workflow = self.create_basic_workflow()
        
        # Add custom nodes if available
        if "UltralyticsDetectorProvider" in self.available_custom_nodes:
            # Add face detection if face model is available
            if self.available_models.get("ultralytics") and "bbox" in self.available_models["ultralytics"]:
                face_models = [m for m in self.available_models["ultralytics"] if "face" in m.lower()]
                if face_models:
                    workflow["8"] = {
                        "inputs": {
                            "model_name": f"bbox/{face_models[0]}"
                        },
                        "class_type": "UltralyticsDetectorProvider"
                    }
        
        if "SAMLoader" in self.available_custom_nodes:
            # Add SAM if SAM model is available
            if self.available_models.get("sams"):
                sam_model = self.available_models["sams"][0]
                workflow["9"] = {
                    "inputs": {
                        "model_name": sam_model,
                        "device_mode": "AUTO"
                    },
                    "class_type": "SAMLoader"
                }
        
        return workflow
    
    def execute_workflow(self, workflow: Dict[str, Any], client_id: str = "flexible_test") -> Optional[str]:
        """Execute a workflow and return the prompt ID."""
        try:
            payload = {
                "prompt": workflow,
                "client_id": client_id
            }
            
            response = requests.post(f"{self.comfyui_url}/prompt", json=payload)
            if response.status_code == 200:
                result = response.json()
                if "prompt_id" in result:
                    return result["prompt_id"]
                else:
                    print(f"Error in workflow execution: {result}")
            else:
                print(f"HTTP Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error executing workflow: {e}")
            
        return None
    
    def wait_for_completion(self, prompt_id: str, timeout: int = 60) -> bool:
        """Wait for workflow completion and return success status."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.comfyui_url}/history/{prompt_id}")
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        status = history[prompt_id].get("status", {})
                        if status.get("completed", False):
                            if status.get("status_str") == "success":
                                print(f"✅ Workflow {prompt_id} completed successfully")
                                return True
                            else:
                                print(f"❌ Workflow {prompt_id} failed: {status.get('status_str')}")
                                return False
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(2)
        
        print(f"⏰ Workflow {prompt_id} timed out after {timeout} seconds")
        return False
    
    def test_basic_workflow(self) -> bool:
        """Test basic workflow with available models."""
        print("\n🧪 Testing Basic Workflow")
        print("=" * 40)
        
        try:
            workflow = self.create_basic_workflow()
            prompt_id = self.execute_workflow(workflow, "basic_test")
            
            if prompt_id:
                print(f"Workflow submitted with ID: {prompt_id}")
                return self.wait_for_completion(prompt_id)
            else:
                print("Failed to submit workflow")
                return False
                
        except Exception as e:
            print(f"Error in basic workflow test: {e}")
            return False
    
    def test_custom_node_workflow(self) -> bool:
        """Test custom node workflow with available models."""
        print("\n🔧 Testing Custom Node Workflow")
        print("=" * 40)
        
        try:
            workflow = self.create_custom_node_workflow()
            prompt_id = self.execute_workflow(workflow, "custom_test")
            
            if prompt_id:
                print(f"Custom workflow submitted with ID: {prompt_id}")
                return self.wait_for_completion(prompt_id)
            else:
                print("Failed to submit custom workflow")
                return False
                
        except Exception as e:
            print(f"Error in custom node workflow test: {e}")
            return False
    
    def run_full_test(self) -> Dict[str, bool]:
        """Run complete test suite."""
        print("🚀 Starting Flexible ComfyUI Workflow Testing")
        print("=" * 50)
        
        # Get available models and custom nodes
        print("\n📋 Discovering Available Models and Custom Nodes")
        self.get_available_models()
        self.get_available_custom_nodes()
        
        results = {}
        
        # Test basic workflow
        results["basic_workflow"] = self.test_basic_workflow()
        
        # Test custom node workflow if custom nodes are available
        if self.available_custom_nodes:
            results["custom_node_workflow"] = self.test_custom_node_workflow()
        else:
            print("\n⚠️  No custom nodes available, skipping custom node test")
            results["custom_node_workflow"] = None
        
        # Print summary
        print("\n📊 Test Results Summary")
        print("=" * 30)
        for test_name, result in results.items():
            if result is True:
                print(f"✅ {test_name}: PASSED")
            elif result is False:
                print(f"❌ {test_name}: FAILED")
            else:
                print(f"⏭️  {test_name}: SKIPPED")
        
        return results

def main():
    """Main function to run the flexible workflow tester."""
    tester = FlexibleWorkflowTester()
    results = tester.run_full_test()
    
    # Exit with appropriate code
    if all(r for r in results.values() if r is not None):
        exit(0)  # Success
    else:
        exit(1)  # Failure

if __name__ == "__main__":
    main()
