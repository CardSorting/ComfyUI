"""
Civitai Integration Module

This module provides integration with Civitai's API for downloading models.
It's a refactored version of the standalone civitai_integration.py that
works as part of the ComfyUI Serverless plugin.

For the full implementation, see: ../../civitai_integration.py
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
    # Import the existing Civitai integration
    from civitai_integration import (
        CivitaiAPI,
        CivitaiURLParser,
        CivitaiModelManager
    )
except ImportError:
    # If the main integration doesn't exist, provide a minimal stub
    # This allows the plugin to load even if the main integration is missing
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("civitai_integration.py not found. Civitai features will be limited.")
    
    # Provide minimal stubs
    class CivitaiAPI:
        def __init__(self, api_key: Optional[str] = None):
            raise ImportError("Civitai integration not available. Install required dependencies.")
    
    class CivitaiURLParser:
        @staticmethod
        def parse_civitai_url(url: str):
            return None
        
        @staticmethod
        def is_civitai_url(url: str) -> bool:
            return 'civitai.com' in url.lower()
    
    class CivitaiModelManager:
        def __init__(self, api_key: Optional[str] = None):
            raise ImportError("Civitai integration not available. Install required dependencies.")

__all__ = ['CivitaiAPI', 'CivitaiURLParser', 'CivitaiModelManager']

