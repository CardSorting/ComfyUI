#!/usr/bin/env python3
"""
Advanced Flexible ComfyUI Workflow Tester

This script provides advanced workflow testing capabilities with intelligent
model selection, workflow templates, and comprehensive testing scenarios.
"""

import requests
import json
import time
import os
import random
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

@dataclass
class WorkflowTestResult:
    name: str
    success: bool
    execution_time: float
    prompt_id: str
    error_message: Optional[str] = None
    models_used: Dict[str, str] = None

class AdvancedWorkflowTester:
    def __init__(self, comfyui_url: str = "http://localhost:8188"):
        self.comfyui_url = comfyui_url
        self.available_models = {}
        self.available_custom_nodes = []
        self.model_preferences = {
            "checkpoints": ["pony", "realistic", "stable", "diffusion"],
            "loras": ["style", "character", "concept"],
            "vae": ["vae", "autoencoder"],
            "upscale": ["esrgan", "upscaler", "real"]
        }
        
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models from ComfyUI API with intelligent categorization."""
        try:
            response = requests.get(f"{self.comfyui_url}/models")
            if response.status_code == 200:
                model_types = response.json()
                print(f"📋 Found {len(model_types)} model types")
                
                for model_type in model_types:
                    if model_type in ["configs", "custom_nodes"]:
                        continue
                        
                    try:
                        response = requests.get(f"{self.comfyui_url}/models/{model_type}")
                        if response.status_code == 200:
                            models = response.json()
                            if models:
                                self.available_models[model_type] = models
                                print(f"  📁 {model_type}: {len(models)} models")
                                
                                # Show some examples
                                if len(models) <= 3:
                                    for model in models:
                                        print(f"    • {model}")
                                else:
                                    for model in models[:2]:
                                        print(f"    • {model}")
                                    print(f"    • ... and {len(models)-2} more")
                    except Exception as e:
                        print(f"  ❌ Error getting {model_type}: {e}")
                        
        except Exception as e:
            print(f"❌ Error getting model types: {e}")
            
        return self.available_models
    
    def get_available_custom_nodes(self) -> List[str]:
        """Get available custom nodes with categorization."""
        try:
            response = requests.get(f"{self.comfyui_url}/object_info")
            if response.status_code == 200:
                object_info = response.json()
                
                # Core ComfyUI nodes
                core_nodes = {
                    "CheckpointLoaderSimple", "CLIPTextEncode", "KSampler", "VAEDecode", 
                    "EmptyLatentImage", "PreviewImage", "LoadImage", "SaveImage",
                    "LoraLoader", "VAELoader", "UpscaleModelLoader"
                }
                
                # Categorize custom nodes
                custom_nodes = {}
                for node_name, node_info in object_info.items():
                    if node_name not in core_nodes:
                        category = self._categorize_custom_node(node_name)
                        if category not in custom_nodes:
                            custom_nodes[category] = []
                        custom_nodes[category].append(node_name)
                
                self.available_custom_nodes = custom_nodes
                
                print(f"🔧 Found {sum(len(nodes) for nodes in custom_nodes.values())} custom nodes:")
                for category, nodes in custom_nodes.items():
                    print(f"  📂 {category}: {len(nodes)} nodes")
                    if len(nodes) <= 3:
                        for node in nodes:
                            print(f"    • {node}")
                    else:
                        for node in nodes[:2]:
                            print(f"    • {node}")
                        print(f"    • ... and {len(nodes)-2} more")
                        
        except Exception as e:
            print(f"❌ Error getting custom nodes: {e}")
            
        return self.available_custom_nodes
    
    def _categorize_custom_node(self, node_name: str) -> str:
        """Categorize custom nodes based on their name."""
        node_lower = node_name.lower()
        
        if "detector" in node_lower or "ultralytics" in node_lower:
            return "Detection"
        elif "sam" in node_lower or "segment" in node_lower:
            return "Segmentation"
        elif "detailer" in node_lower or "face" in node_lower:
            return "Enhancement"
        elif "control" in node_lower or "controlnet" in node_lower:
            return "Control"
        elif "upscale" in node_lower or "esrgan" in node_lower:
            return "Upscaling"
        elif "wildcard" in node_lower or "template" in node_lower:
            return "Templates"
        else:
            return "Other"
    
    def select_best_model(self, model_type: str, preference: str = None) -> Optional[str]:
        """Intelligently select the best model for a given type."""
        models = self.available_models.get(model_type, [])
        if not models:
            return None
            
        if len(models) == 1:
            return models[0]
            
        # If preference is given, try to match it
        if preference:
            preferred = [m for m in models if preference.lower() in m.lower()]
            if preferred:
                return preferred[0]
        
        # Use model preferences
        preferences = self.model_preferences.get(model_type, [])
        for pref in preferences:
            preferred = [m for m in models if pref.lower() in m.lower()]
            if preferred:
                return preferred[0]
        
        # Fallback to first model
        return models[0]
    
    def create_workflow_template(self, template_type: str, **kwargs) -> Dict[str, Any]:
        """Create workflow templates with dynamic model selection."""
        base_workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": self.select_best_model("checkpoints", kwargs.get("checkpoint_preference"))
                },
                "class_type": "CheckpointLoaderSimple"
            }
        }
        
        if template_type == "basic":
            return self._create_basic_template(base_workflow, **kwargs)
        elif template_type == "lora":
            return self._create_lora_template(base_workflow, **kwargs)
        elif template_type == "upscale":
            return self._create_upscale_template(base_workflow, **kwargs)
        elif template_type == "detection":
            return self._create_detection_template(base_workflow, **kwargs)
        else:
            return self._create_basic_template(base_workflow, **kwargs)
    
    def _create_basic_template(self, base_workflow: Dict, **kwargs) -> Dict[str, Any]:
        """Create basic text-to-image workflow."""
        prompt = kwargs.get("prompt", "a beautiful landscape, detailed, high quality, photorealistic")
        negative = kwargs.get("negative", "blurry, low quality, distorted, bad anatomy")
        
        workflow = base_workflow.copy()
        workflow.update({
            "2": {
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "text": negative,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "4": {
                "inputs": {
                    "width": kwargs.get("width", 512),
                    "height": kwargs.get("height", 512),
                    "batch_size": kwargs.get("batch_size", 1)
                },
                "class_type": "EmptyLatentImage"
            },
            "5": {
                "inputs": {
                    "seed": kwargs.get("seed", random.randint(1, 1000000)),
                    "steps": kwargs.get("steps", 20),
                    "cfg": kwargs.get("cfg", 7.5),
                    "sampler_name": kwargs.get("sampler", "euler"),
                    "scheduler": kwargs.get("scheduler", "normal"),
                    "denoise": kwargs.get("denoise", 1.0),
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
        })
        
        return workflow
    
    def _create_lora_template(self, base_workflow: Dict, **kwargs) -> Dict[str, Any]:
        """Create workflow with LoRA support."""
        workflow = self._create_basic_template(base_workflow, **kwargs)
        
        # Add LoRA if available
        lora_model = self.select_best_model("loras", kwargs.get("lora_preference"))
        if lora_model:
            workflow["8"] = {
                "inputs": {
                    "model": ["1", 0],
                    "clip": ["1", 1],
                    "lora_name": lora_model,
                    "strength_model": kwargs.get("lora_strength", 1.0),
                    "strength_clip": kwargs.get("lora_clip_strength", 1.0)
                },
                "class_type": "LoraLoader"
            }
            
            # Update connections to use LoRA outputs
            workflow["5"]["inputs"]["model"] = ["8", 0]
            workflow["2"]["inputs"]["clip"] = ["8", 1]
            workflow["3"]["inputs"]["clip"] = ["8", 1]
        
        return workflow
    
    def _create_upscale_template(self, base_workflow: Dict, **kwargs) -> Dict[str, Any]:
        """Create workflow with upscaling."""
        workflow = self._create_basic_template(base_workflow, **kwargs)
        
        # Add upscaling if available
        upscale_model = self.select_best_model("upscale_models", kwargs.get("upscale_preference"))
        if upscale_model:
            workflow["8"] = {
                "inputs": {
                    "model_name": upscale_model
                },
                "class_type": "UpscaleModelLoader"
            }
            workflow["9"] = {
                "inputs": {
                    "upscale_model": ["8", 0],
                    "image": ["6", 0]
                },
                "class_type": "ImageUpscaleWithModel"
            }
            workflow["10"] = {
                "inputs": {
                    "images": ["9", 0]
                },
                "class_type": "PreviewImage"
            }
        
        return workflow
    
    def _create_detection_template(self, base_workflow: Dict, **kwargs) -> Dict[str, Any]:
        """Create workflow with detection capabilities."""
        workflow = self._create_basic_template(base_workflow, **kwargs)
        
        # Add detection if available
        detection_nodes = self.available_custom_nodes.get("Detection", [])
        if "UltralyticsDetectorProvider" in detection_nodes:
            bbox_model = self.select_best_model("ultralytics_bbox")
            if bbox_model:
                workflow["8"] = {
                    "inputs": {
                        "model_name": bbox_model
                    },
                    "class_type": "UltralyticsDetectorProvider"
                }
        
        # Add SAM if available
        sam_nodes = self.available_custom_nodes.get("Segmentation", [])
        if "SAMLoader" in sam_nodes:
            sam_model = self.select_best_model("sams")
            if sam_model:
                workflow["9"] = {
                    "inputs": {
                        "model_name": sam_model,
                        "device_mode": "AUTO"
                    },
                    "class_type": "SAMLoader"
                }
        
        return workflow
    
    def execute_workflow(self, workflow: Dict[str, Any], client_id: str = "advanced_test") -> Tuple[Optional[str], float]:
        """Execute a workflow and return prompt ID and execution time."""
        start_time = time.time()
        
        try:
            payload = {
                "prompt": workflow,
                "client_id": client_id
            }
            
            response = requests.post(f"{self.comfyui_url}/prompt", json=payload)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if "prompt_id" in result:
                    return result["prompt_id"], execution_time
                else:
                    print(f"❌ Error in workflow execution: {result}")
            else:
                print(f"❌ HTTP Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error executing workflow: {e}")
            
        return None, time.time() - start_time
    
    def wait_for_completion(self, prompt_id: str, timeout: int = 120) -> Tuple[bool, str]:
        """Wait for workflow completion and return success status and error message."""
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
                                return True, ""
                            else:
                                error_msg = status.get("messages", [{}])[-1].get("execution_error", {}).get("exception_message", "Unknown error")
                                return False, error_msg
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️  Error checking status: {e}")
                time.sleep(2)
        
        return False, "Timeout"
    
    def run_comprehensive_test(self) -> List[WorkflowTestResult]:
        """Run comprehensive workflow tests."""
        print("🚀 Starting Advanced ComfyUI Workflow Testing")
        print("=" * 60)
        
        # Discover available models and custom nodes
        print("\n📋 Discovering Available Models and Custom Nodes")
        self.get_available_models()
        self.get_available_custom_nodes()
        
        results = []
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Basic Text-to-Image",
                "template": "basic",
                "prompt": "a serene mountain landscape at sunset, detailed, photorealistic",
                "width": 512,
                "height": 512
            },
            {
                "name": "Portrait Generation",
                "template": "basic",
                "prompt": "portrait of a person, detailed face, high quality, professional photography",
                "width": 512,
                "height": 768
            },
            {
                "name": "Landscape with LoRA",
                "template": "lora",
                "prompt": "fantasy landscape, magical forest, detailed, high quality",
                "lora_preference": "style"
            },
            {
                "name": "High-Resolution Upscaling",
                "template": "upscale",
                "prompt": "detailed architectural building, high quality, professional",
                "width": 512,
                "height": 512
            },
            {
                "name": "Detection Workflow",
                "template": "detection",
                "prompt": "group of people in a park, detailed, photorealistic",
                "width": 512,
                "height": 512
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            print("-" * 40)
            
            try:
                # Create workflow
                workflow = self.create_workflow_template(
                    scenario["template"], 
                    **{k: v for k, v in scenario.items() if k not in ["name", "template"]}
                )
                
                # Execute workflow
                prompt_id, execution_time = self.execute_workflow(workflow, f"test_{len(results)}")
                
                if prompt_id:
                    print(f"📤 Workflow submitted (ID: {prompt_id[:8]}...)")
                    
                    # Wait for completion
                    success, error_msg = self.wait_for_completion(prompt_id)
                    
                    result = WorkflowTestResult(
                        name=scenario["name"],
                        success=success,
                        execution_time=execution_time,
                        prompt_id=prompt_id,
                        error_message=error_msg if not success else None
                    )
                    
                    if success:
                        print(f"✅ Completed in {execution_time:.2f}s")
                    else:
                        print(f"❌ Failed: {error_msg}")
                        
                else:
                    result = WorkflowTestResult(
                        name=scenario["name"],
                        success=False,
                        execution_time=execution_time,
                        prompt_id="",
                        error_message="Failed to submit workflow"
                    )
                    print("❌ Failed to submit workflow")
                
                results.append(result)
                
            except Exception as e:
                result = WorkflowTestResult(
                    name=scenario["name"],
                    success=False,
                    execution_time=0,
                    prompt_id="",
                    error_message=str(e)
                )
                print(f"❌ Error: {e}")
                results.append(result)
        
        # Print comprehensive summary
        print("\n📊 Comprehensive Test Results")
        print("=" * 50)
        
        successful = 0
        total = len(results)
        
        for result in results:
            status = "✅ PASSED" if result.success else "❌ FAILED"
            time_str = f"({result.execution_time:.2f}s)" if result.execution_time > 0 else ""
            print(f"{status} {result.name} {time_str}")
            
            if not result.success and result.error_message:
                print(f"    💬 {result.error_message}")
            
            if result.success:
                successful += 1
        
        print(f"\n🎯 Overall Results: {successful}/{total} tests passed ({successful/total*100:.1f}%)")
        
        return results

def main():
    """Main function to run the advanced workflow tester."""
    tester = AdvancedWorkflowTester()
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    successful_tests = sum(1 for r in results if r.success)
    total_tests = len(results)
    
    if successful_tests == total_tests:
        exit(0)  # All tests passed
    elif successful_tests > 0:
        exit(2)  # Some tests passed
    else:
        exit(1)  # All tests failed

if __name__ == "__main__":
    main()
