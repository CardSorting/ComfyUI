"""
Headless Mode Utilities

Utilities for configuring and managing ComfyUI in headless mode.
This module provides functions to set up headless mode before ComfyUI initialization.
"""

import os
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_headless_mode() -> bool:
    """
    Check if headless mode is enabled.
    
    Returns:
        True if headless mode is enabled, False otherwise
    """
    return (
        os.environ.get('COMFYUI_HEADLESS', '').lower() in ('1', 'true', 'yes') or
        os.environ.get('DISABLE_PROGRESS_BARS', '').lower() in ('1', 'true', 'yes')
    )


def setup_headless_environment() -> None:
    """
    Configure environment for headless mode.
    
    This function sets environment variables and configures progress bars
    to prevent broken pipe errors in headless/serverless environments.
    """
    if not is_headless_mode():
        return
    
    logger.info("Setting up headless environment...")
    
    # Set headless mode environment variable if not already set
    os.environ['COMFYUI_HEADLESS'] = '1'
    os.environ['DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    
    # Configure TQDM for headless mode
    tqdm_env_vars = {
        'TQDM_DISABLE': '1',
        'TQDM_DISABLE_PROGRESS_BAR': '1',
        'TQDM_MINITERS': '0',
        'TQDM_MAXITERS': '0',
        'TQDM_POSITION': '0',
        'TQDM_LEAVE': 'false',
        'TQDM_NCOLS': '0',
        'TQDM_DESC': '',
        'TQDM_UNIT': '',
        'TQDM_UNIT_SCALE': 'false',
        'TQDM_RATE': '0',
        'TQDM_POSTFIX': '',
        'TQDM_BAR_FORMAT': '',
        'TQDM_SMOOTHING': '0',
        'TQDM_DYNAMIC_NCOLS': 'false',
        'TQDM_ASCII': 'true',
        'TQDM_DISABLE_TQDM': '1'
    }
    
    for key, value in tqdm_env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
    
    # Monkey patch TQDM if it's already imported
    try:
        import tqdm
        from tqdm import tqdm as tqdm_class
        
        # Create a no-op tqdm class for headless mode
        class NoOpTqdm:
            def __init__(self, *args, **kwargs):
                self.n = 0
                self.total = kwargs.get('total', 1)
                self.desc = kwargs.get('desc', '')
                self.unit = kwargs.get('unit', '')
                self.leave = kwargs.get('leave', False)
                self.position = kwargs.get('position', 0)
                self.disable = True
            
            def update(self, n=1):
                self.n += n
                return self
            
            def close(self):
                pass
            
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass
            
            def __iter__(self):
                return iter(range(self.total))
        
        # Replace tqdm with no-op version
        tqdm.tqdm = NoOpTqdm
        tqdm.trange = lambda *args, **kwargs: NoOpTqdm(*args, **kwargs)
        
        logger.debug("TQDM monkey-patched for headless mode")
    except ImportError:
        # TQDM not imported yet, environment variables will handle it
        pass


def configure_headless_mode(enable: bool = True) -> None:
    """
    Explicitly enable or disable headless mode.
    
    Args:
        enable: If True, enable headless mode. If False, disable it.
    """
    if enable:
        os.environ['COMFYUI_HEADLESS'] = '1'
        os.environ['DISABLE_PROGRESS_BARS'] = '1'
        setup_headless_environment()
        logger.info("Headless mode enabled")
    else:
        os.environ.pop('COMFYUI_HEADLESS', None)
        os.environ.pop('DISABLE_PROGRESS_BARS', None)
        logger.info("Headless mode disabled")


def get_headless_config() -> dict:
    """
    Get current headless mode configuration.
    
    Returns:
        Dictionary with headless configuration
    """
    return {
        'enabled': is_headless_mode(),
        'comfyui_headless': os.environ.get('COMFYUI_HEADLESS', ''),
        'disable_progress_bars': os.environ.get('DISABLE_PROGRESS_BARS', ''),
        'tqdm_disabled': os.environ.get('TQDM_DISABLE', ''),
    }

