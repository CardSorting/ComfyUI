"""
Model Download Nodes

ComfyUI nodes for downloading models from various sources.
These nodes can be used in workflows to download models programmatically.
"""

import os
import logging
from typing import Optional, Dict, Any
from comfy_api.latest import io

logger = logging.getLogger(__name__)


class CivitaiDownloadNode(io.ComfyNode):
    """
    Download a model from Civitai.
    
    This node downloads models from Civitai URLs and places them in the
    appropriate ComfyUI model directory.
    """
    
    @classmethod
    def define_schema(cls) -> io.Schema:
        """Define the node schema."""
        return io.Schema(
            node_id="CivitaiDownload",
            display_name="Download from Civitai",
            category="serverless/model_download",
            description="Download a model from Civitai.com",
            inputs={
                "url": io.Schema.Input(
                    type="String",
                    description="Civitai model URL or model ID",
                    default=""
                ),
                "api_key": io.Schema.Input(
                    type="String",
                    description="Civitai API key (optional, can use CIVITAI_API_KEY env var)",
                    default=""
                ),
                "category": io.Schema.Input(
                    type="Combo",
                    description="Model category (auto-detected if empty)",
                    options=["", "checkpoints", "loras", "vae", "controlnet", "embeddings", "upscale_models"],
                    default=""
                ),
            },
            outputs={
                "status": io.Schema.Output(
                    type="String",
                    description="Download status message"
                ),
                "file_path": io.Schema.Output(
                    type="String",
                    description="Path to downloaded file"
                ),
                "success": io.Schema.Output(
                    type="Boolean",
                    description="Whether download was successful"
                ),
            }
        )
    
    @classmethod
    def execute(
        cls,
        url: str,
        api_key: str = "",
        category: str = ""
    ) -> io.NodeOutput:
        """Execute the node."""
        try:
            import sys
            from pathlib import Path
            # Import from main codebase (compatibility)
            COMFYUI_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()
            if str(COMFYUI_ROOT) not in sys.path:
                sys.path.insert(0, str(COMFYUI_ROOT))
            
            try:
                from civitai_integration import CivitaiModelManager
            except ImportError:
                from ...integrations.civitai import CivitaiModelManager
            
            # Get API key from parameter or environment
            api_key = api_key or os.environ.get('CIVITAI_API_KEY')
            
            # Create manager
            manager = CivitaiModelManager(api_key=api_key)
            
            # Download model
            if category:
                # Use custom directory if specified
                import folder_paths
                model_dir = folder_paths.get_folder_paths(category)[0]
                success = manager.download_from_url(url, custom_dir=model_dir)
            else:
                success = manager.download_from_url(url)
            
            if success:
                return io.NodeOutput(
                    status="Download completed successfully",
                    file_path="",  # TODO: Return actual file path
                    success=True
                )
            else:
                return io.NodeOutput(
                    status="Download failed",
                    file_path="",
                    success=False
                )
                
        except Exception as e:
            logger.error(f"Error downloading from Civitai: {e}")
            return io.NodeOutput(
                status=f"Error: {str(e)}",
                file_path="",
                success=False
            )


class HuggingFaceDownloadNode(io.ComfyNode):
    """
    Download a model from HuggingFace Hub.
    
    This node downloads models from HuggingFace and places them in the
    appropriate ComfyUI model directory.
    """
    
    @classmethod
    def define_schema(cls) -> io.Schema:
        """Define the node schema."""
        return io.Schema(
            node_id="HuggingFaceDownload",
            display_name="Download from HuggingFace",
            category="serverless/model_download",
            description="Download a model from HuggingFace Hub",
            inputs={
                "repo_id": io.Schema.Input(
                    type="String",
                    description="HuggingFace repository ID (e.g., 'runwayml/stable-diffusion-v1-5')",
                    default=""
                ),
                "branch": io.Schema.Input(
                    type="String",
                    description="Repository branch (default: 'main')",
                    default="main"
                ),
                "api_token": io.Schema.Input(
                    type="String",
                    description="HuggingFace API token (optional)",
                    default=""
                ),
                "category": io.Schema.Input(
                    type="Combo",
                    description="Model category (auto-detected if empty)",
                    options=["", "checkpoints", "loras", "vae", "controlnet", "embeddings", "upscale_models"],
                    default=""
                ),
            },
            outputs={
                "status": io.Schema.Output(
                    type="String",
                    description="Download status message"
                ),
                "file_path": io.Schema.Output(
                    type="String",
                    description="Path to downloaded file(s)"
                ),
                "success": io.Schema.Output(
                    type="Boolean",
                    description="Whether download was successful"
                ),
            }
        )
    
    @classmethod
    def execute(
        cls,
        repo_id: str,
        branch: str = "main",
        api_token: str = "",
        category: str = ""
    ) -> io.NodeOutput:
        """Execute the node."""
        try:
            import sys
            from pathlib import Path
            # Import from main codebase (compatibility)
            COMFYUI_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()
            if str(COMFYUI_ROOT) not in sys.path:
                sys.path.insert(0, str(COMFYUI_ROOT))
            
            try:
                from huggingface_integration import HuggingFaceModelManager, HuggingFaceURLParser
            except ImportError:
                from ...integrations.huggingface import HuggingFaceModelManager, HuggingFaceURLParser
            
            # Get API token from parameter or environment
            api_token = api_token or os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_HUB_TOKEN')
            
            # Create manager
            manager = HuggingFaceModelManager(api_token=api_token)
            
            # Download model
            if category:
                # Use custom directory if specified
                import folder_paths
                model_dir = folder_paths.get_folder_paths(category)[0]
                success = manager.download_model(repo_id, branch=branch, custom_dir=model_dir)
            else:
                success = manager.download_model(repo_id, branch=branch)
            
            if success:
                return io.NodeOutput(
                    status="Download completed successfully",
                    file_path="",  # TODO: Return actual file path
                    success=True
                )
            else:
                return io.NodeOutput(
                    status="Download failed",
                    file_path="",
                    success=False
                )
                
        except Exception as e:
            logger.error(f"Error downloading from HuggingFace: {e}")
            return io.NodeOutput(
                status=f"Error: {str(e)}",
                file_path="",
                success=False
            )


class GenericModelDownloadNode(io.ComfyNode):
    """
    Download a model from any URL with automatic source detection.
    
    This node automatically detects whether a URL is from Civitai or
    HuggingFace and uses the appropriate download method.
    """
    
    @classmethod
    def define_schema(cls) -> io.Schema:
        """Define the node schema."""
        return io.Schema(
            node_id="GenericModelDownload",
            display_name="Download Model (Auto-detect)",
            category="serverless/model_download",
            description="Download a model from any URL with automatic source detection",
            inputs={
                "url": io.Schema.Input(
                    type="String",
                    description="Model URL (Civitai or HuggingFace)",
                    default=""
                ),
                "civitai_api_key": io.Schema.Input(
                    type="String",
                    description="Civitai API key (optional)",
                    default=""
                ),
                "hf_api_token": io.Schema.Input(
                    type="String",
                    description="HuggingFace API token (optional)",
                    default=""
                ),
                "category": io.Schema.Input(
                    type="Combo",
                    description="Model category (auto-detected if empty)",
                    options=["", "checkpoints", "loras", "vae", "controlnet", "embeddings", "upscale_models"],
                    default=""
                ),
            },
            outputs={
                "status": io.Schema.Output(
                    type="String",
                    description="Download status message"
                ),
                "file_path": io.Schema.Output(
                    type="String",
                    description="Path to downloaded file"
                ),
                "success": io.Schema.Output(
                    type="Boolean",
                    description="Whether download was successful"
                ),
                "source": io.Schema.Output(
                    type="String",
                    description="Detected source (civitai, huggingface, or unknown)"
                ),
            }
        )
    
    @classmethod
    def execute(
        cls,
        url: str,
        civitai_api_key: str = "",
        hf_api_token: str = "",
        category: str = ""
    ) -> io.NodeOutput:
        """Execute the node."""
        try:
            # Detect source
            url_lower = url.lower()
            
            if 'civitai.com' in url_lower:
                # Use Civitai download
                import sys
                from pathlib import Path
                COMFYUI_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()
                if str(COMFYUI_ROOT) not in sys.path:
                    sys.path.insert(0, str(COMFYUI_ROOT))
                
                try:
                    from civitai_integration import CivitaiModelManager
                except ImportError:
                    from ...integrations.civitai import CivitaiModelManager
                
                api_key = civitai_api_key or os.environ.get('CIVITAI_API_KEY')
                manager = CivitaiModelManager(api_key=api_key)
                
                if category:
                    import folder_paths
                    model_dir = folder_paths.get_folder_paths(category)[0]
                    success = manager.download_from_url(url, custom_dir=model_dir)
                else:
                    success = manager.download_from_url(url)
                
                source = "civitai"
                
            elif 'huggingface.co' in url_lower:
                # Use HuggingFace download
                import sys
                from pathlib import Path
                COMFYUI_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()
                if str(COMFYUI_ROOT) not in sys.path:
                    sys.path.insert(0, str(COMFYUI_ROOT))
                
                try:
                    from huggingface_integration import HuggingFaceModelManager, HuggingFaceURLParser
                except ImportError:
                    from ...integrations.huggingface import HuggingFaceModelManager, HuggingFaceURLParser
                
                api_token = hf_api_token or os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_HUB_TOKEN')
                manager = HuggingFaceModelManager(api_token=api_token)
                
                # Parse URL to get repo_id
                parser = HuggingFaceURLParser()
                url_info = parser.parse_hf_url(url)
                
                if url_info:
                    repo_id = url_info['repo_id']
                    branch = url_info.get('branch', 'main')
                    
                    if category:
                        import folder_paths
                        model_dir = folder_paths.get_folder_paths(category)[0]
                        success = manager.download_model(repo_id, branch=branch, custom_dir=model_dir)
                    else:
                        success = manager.download_model(repo_id, branch=branch)
                else:
                    success = False
                
                source = "huggingface"
                
            else:
                return io.NodeOutput(
                    status="Unknown URL source. Supported: Civitai or HuggingFace",
                    file_path="",
                    success=False,
                    source="unknown"
                )
            
            if success:
                return io.NodeOutput(
                    status="Download completed successfully",
                    file_path="",
                    success=True,
                    source=source
                )
            else:
                return io.NodeOutput(
                    status="Download failed",
                    file_path="",
                    success=False,
                    source=source
                )
                
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            return io.NodeOutput(
                status=f"Error: {str(e)}",
                file_path="",
                success=False,
                source="unknown"
            )

