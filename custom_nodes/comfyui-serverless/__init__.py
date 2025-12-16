"""
ComfyUI Serverless Plugin

A ComfyUI extension that provides:
- Headless mode utilities and configuration
- Modal.com deployment support
- Civitai and HuggingFace model download integrations
- Serverless deployment utilities

This plugin enables easy migration to future ComfyUI releases by isolating
serverless and model management features from the core codebase.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Plugin metadata
__version__ = "0.1.0"
__author__ = "ComfyUI Serverless Team"
__description__ = "Serverless deployment and model management for ComfyUI"

# Import extension
from .extension import ServerlessExtension

# Export for compatibility (lazy imports to handle missing dependencies)
try:
    from .integrations.civitai import CivitaiModelManager, CivitaiAPI, CivitaiURLParser
except ImportError:
    CivitaiModelManager = None
    CivitaiAPI = None
    CivitaiURLParser = None

try:
    from .integrations.huggingface import HuggingFaceModelManager, HuggingFaceURLParser
except ImportError:
    HuggingFaceModelManager = None
    HuggingFaceURLParser = None
from .serverless.headless_utils import (
    configure_headless_mode,
    is_headless_mode,
    setup_headless_environment
)
from .serverless.modal_host import (
    create_modal_comfyui_app,
    get_modal_comfyui_config
)

# ComfyUI plugin entrypoint
async def comfy_entrypoint() -> ServerlessExtension:
    """
    ComfyUI plugin entrypoint.
    
    This function is called by ComfyUI to load the extension.
    Returns a ServerlessExtension instance that provides nodes and initialization.
    """
    logger.info(f"Loading ComfyUI Serverless Plugin v{__version__}")
    
    # Configure headless mode if environment variable is set
    if os.environ.get('COMFYUI_HEADLESS', '').lower() in ('1', 'true', 'yes'):
        logger.info("Headless mode detected, configuring...")
        setup_headless_environment()
    
    return ServerlessExtension()

# For synchronous entrypoint (fallback)
def comfy_entrypoint_sync() -> ServerlessExtension:
    """Synchronous entrypoint for compatibility."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to handle this differently
            # For now, create extension without async init
            extension = ServerlessExtension()
            return extension
        else:
            return loop.run_until_complete(comfy_entrypoint())
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(comfy_entrypoint())

# Export all public APIs
__all__ = [
    'comfy_entrypoint',
    'comfy_entrypoint_sync',
    'ServerlessExtension',
    'CivitaiModelManager',
    'CivitaiAPI',
    'CivitaiURLParser',
    'HuggingFaceModelManager',
    'HuggingFaceURLParser',
    'configure_headless_mode',
    'is_headless_mode',
    'setup_headless_environment',
    'create_modal_comfyui_app',
    'get_modal_comfyui_config',
]

