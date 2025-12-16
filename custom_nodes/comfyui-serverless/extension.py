"""
ComfyUI Serverless Extension

Main extension class that provides nodes and initialization hooks.
Enhanced with industry best practices: error handling, logging, configuration.
"""

import os
import logging
from typing import List, Optional
from comfy_api.latest import ComfyExtension

from .core import (
    get_plugin_config,
    get_logger,
    log_async_performance,
    ServerlessPluginError,
    ConfigurationError,
    PluginConfig
)
from .nodes.model_download import (
    CivitaiDownloadNode,
    HuggingFaceDownloadNode,
    GenericModelDownloadNode
)

logger = get_logger(__name__)


class ServerlessExtension(ComfyExtension):
    """
    ComfyUI Serverless Extension
    
    Provides nodes for model downloads and serverless deployment utilities.
    Enhanced with configuration management, error handling, and observability.
    """
    
    def __init__(self, config: Optional[PluginConfig] = None):
        """
        Initialize the extension.
        
        Args:
            config: Optional PluginConfig instance (uses global config if None)
        """
        self._initialized = False
        self._headless_configured = False
        self._config = config or get_plugin_config()
        self._nodes: List[type] = []
    
    @log_async_performance
    async def on_load(self) -> None:
        """
        Called when the extension is loaded.
        
        This is where we can initialize global resources and configure
        headless mode if needed. Enhanced with error handling and logging.
        """
        if self._initialized:
            logger.debug("Extension already initialized, skipping on_load")
            return
        
        try:
            logger.info("ComfyUI Serverless Extension: on_load() called")
            
            # Load configuration
            try:
                self._config = get_plugin_config()
                logger.debug("Configuration loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load configuration: {e}, using defaults")
                raise ConfigurationError(
                    "Failed to load plugin configuration",
                    error_code="CONFIG_LOAD_FAILED",
                    cause=e
                )
            
            # Configure headless mode if enabled
            if not self._headless_configured:
                try:
                    from .serverless.headless_utils import setup_headless_environment, is_headless_mode
                    
                    if is_headless_mode() or self._config.headless_enabled:
                        logger.info("Configuring headless mode...")
                        setup_headless_environment()
                        self._headless_configured = True
                        logger.info("Headless mode configured successfully")
                except Exception as e:
                    logger.error(f"Failed to configure headless mode: {e}", exc_info=True)
                    # Don't fail extension load if headless config fails
                    # It's not critical for plugin operation
            
            # Initialize nodes list
            self._nodes = [
                CivitaiDownloadNode,
                HuggingFaceDownloadNode,
                GenericModelDownloadNode,
            ]
            
            self._initialized = True
            logger.info(
                f"ComfyUI Serverless Extension: Initialization complete "
                f"({len(self._nodes)} nodes ready)"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize extension: {e}", exc_info=True)
            raise ServerlessPluginError(
                "Extension initialization failed",
                error_code="EXTENSION_INIT_FAILED",
                cause=e
            )
    
    @log_async_performance
    async def get_node_list(self) -> List[type]:
        """
        Returns a list of nodes provided by this extension.
        
        Returns:
            List of ComfyNode classes
        
        Raises:
            ServerlessPluginError: If extension not initialized
        """
        if not self._initialized:
            logger.warning("Extension not initialized, initializing now...")
            await self.on_load()
        
        if not self._nodes:
            logger.warning("No nodes available, returning empty list")
            return []
        
        logger.debug(f"Returning {len(self._nodes)} nodes")
        return self._nodes
    
    def get_config(self) -> PluginConfig:
        """
        Get extension configuration.
        
        Returns:
            PluginConfig instance
        """
        return self._config

