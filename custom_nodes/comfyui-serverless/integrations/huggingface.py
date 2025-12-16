"""
HuggingFace Integration Module

This module provides integration with HuggingFace Hub for downloading models.
It's a refactored version of the standalone huggingface_integration.py that
works as part of the ComfyUI Serverless plugin.

For the full implementation, see: ../../huggingface_integration.py
This module provides a compatibility layer that imports from the main codebase.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Import from the main ComfyUI codebase
# This allows the plugin to use existing integrations without duplication
COMFYUI_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()
sys.path.insert(0, str(COMFYUI_ROOT))

try:
    # Import the existing HuggingFace integration
    from huggingface_integration import (
        HuggingFaceURLParser,
        HuggingFaceModelManager
    )
except ImportError:
    # If the main integration doesn't exist, provide a minimal stub
    # This allows the plugin to load even if the main integration is missing
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("huggingface_integration.py not found. HuggingFace features will be limited.")
    
    # Provide minimal stubs
    class HuggingFaceURLParser:
        @staticmethod
        def parse_hf_url(url: str):
            return None
        
        @staticmethod
        def is_huggingface_url(url: str) -> bool:
            return 'huggingface.co' in url.lower()
    
    class HuggingFaceModelManager:
        def __init__(self, api_token: Optional[str] = None):
            raise ImportError("HuggingFace integration not available. Install huggingface_hub: pip install huggingface_hub")

__all__ = ['HuggingFaceURLParser', 'HuggingFaceModelManager']

