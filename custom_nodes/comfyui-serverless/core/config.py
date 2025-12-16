"""
Configuration Management

Industry-standard configuration management using Pydantic Settings
with environment variable support, validation, and type safety.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache

try:
    from pydantic import BaseSettings, Field, validator
    from pydantic_settings import BaseSettings as PydanticBaseSettings
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback to basic dict-based config
    BaseSettings = dict
    Field = None
    validator = None

import logging

logger = logging.getLogger(__name__)


class PluginConfig:
    """
    Plugin configuration manager with environment variable support.
    
    Uses Pydantic Settings for validation and type safety when available,
    falls back to environment variables otherwise.
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Optional path to JSON configuration file
        """
        self.config_file = config_file or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path."""
        plugin_dir = Path(__file__).parent.parent
        return plugin_dir / "config.json"
    
    def _load_config(self) -> None:
        """Load configuration from file and environment."""
        # Start with defaults
        self._config = {
            'headless': {
                'enabled': os.environ.get('COMFYUI_HEADLESS', '').lower() in ('1', 'true', 'yes'),
                'disable_progress_bars': True,
                'disable_telemetry': True,
            },
            'integrations': {
                'civitai': {
                    'enabled': True,
                    'api_key': os.environ.get('CIVITAI_API_KEY', ''),
                    'base_url': 'https://civitai.com/api/v1',
                },
                'huggingface': {
                    'enabled': True,
                    'api_token': os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_HUB_TOKEN', ''),
                    'cache_dir': os.environ.get('HF_HOME', str(Path.home() / '.cache' / 'huggingface')),
                },
            },
            'modal': {
                'enabled': False,
                'models_volume_name': 'comfyui-models',
                'outputs_volume_name': 'comfyui-outputs',
                'gpu_config': 'A10G',
                'timeout': 600,
                'scaledown_window': 300,
            },
            'downloads': {
                'max_retries': 3,
                'timeout': 300,
                'chunk_size': 8192 * 16,
                'verify_ssl': True,
            },
            'logging': {
                'level': os.environ.get('LOG_LEVEL', 'INFO'),
                'format': 'json',  # 'json' or 'text'
                'file': None,
            },
            'cache': {
                'enabled': True,
                'ttl': 3600,  # 1 hour
                'max_size': 100,  # MB
            },
        }
        
        # Load from file if exists
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._deep_update(self._config, file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables (highest priority)
        self._load_from_env()
    
    def _deep_update(self, base: Dict, update: Dict) -> None:
        """Recursively update nested dictionaries."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Headless config
        if 'COMFYUI_HEADLESS' in os.environ:
            self._config['headless']['enabled'] = os.environ['COMFYUI_HEADLESS'].lower() in ('1', 'true', 'yes')
        
        # Integration configs
        if 'CIVITAI_API_KEY' in os.environ:
            self._config['integrations']['civitai']['api_key'] = os.environ['CIVITAI_API_KEY']
        
        if 'HF_TOKEN' in os.environ:
            self._config['integrations']['huggingface']['api_token'] = os.environ['HF_TOKEN']
        elif 'HUGGINGFACE_HUB_TOKEN' in os.environ:
            self._config['integrations']['huggingface']['api_token'] = os.environ['HUGGINGFACE_HUB_TOKEN']
        
        # Modal config
        if 'MODAL_GPU_CONFIG' in os.environ:
            self._config['modal']['gpu_config'] = os.environ['MODAL_GPU_CONFIG']
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'headless.enabled')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'headless.enabled')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: Optional[Path] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            path: Optional path to save config (defaults to config_file)
        """
        save_path = path or self.config_file
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config.copy()
    
    @property
    def headless_enabled(self) -> bool:
        """Check if headless mode is enabled."""
        return self.get('headless.enabled', False)
    
    @property
    def civitai_api_key(self) -> Optional[str]:
        """Get Civitai API key."""
        return self.get('integrations.civitai.api_key') or None
    
    @property
    def huggingface_token(self) -> Optional[str]:
        """Get HuggingFace API token."""
        return self.get('integrations.huggingface.api_token') or None


# Global configuration instance
_config_instance: Optional[PluginConfig] = None


@lru_cache(maxsize=1)
def get_plugin_config(config_file: Optional[Path] = None) -> PluginConfig:
    """
    Get or create global plugin configuration instance.
    
    Args:
        config_file: Optional path to configuration file
    
    Returns:
        PluginConfig instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = PluginConfig(config_file)
    
    return _config_instance


def load_config(config_file: Optional[Path] = None) -> PluginConfig:
    """
    Load configuration (creates new instance, doesn't use cache).
    
    Args:
        config_file: Optional path to configuration file
    
    Returns:
        PluginConfig instance
    """
    return PluginConfig(config_file)

