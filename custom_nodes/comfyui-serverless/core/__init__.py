"""
Core utilities and base classes for the ComfyUI Serverless plugin.

This module provides foundational components following industry best practices:
- Configuration management with Pydantic
- Structured logging
- Error handling
- Type safety
"""

from .config import PluginConfig, get_plugin_config, load_config
from .exceptions import (
    ServerlessPluginError,
    ConfigurationError,
    IntegrationError,
    DownloadError,
    ValidationError
)
from .logging import setup_plugin_logging, get_logger, log_performance, log_async_performance
from .types import (
    DownloadResult,
    ModelSource,
    HeadlessConfig,
    ModalConfig,
    DownloadStatus
)
from .retry import (
    RetryConfig,
    retry_with_backoff,
    retry_async_with_backoff,
    CircuitBreaker
)
from .cache import (
    TTLCache,
    FileCache,
    cached_with_ttl,
    cache_key
)
from .validation import (
    Validator,
    URLValidator,
    CivitaiURLValidator,
    HuggingFaceURLValidator,
    validate,
    validate_url,
    validate_civitai_url,
    validate_huggingface_url
)
from .health import (
    HealthStatus,
    HealthCheckResult,
    HealthChecker,
    get_health_checker
)

__all__ = [
    # Configuration
    'PluginConfig',
    'get_plugin_config',
    'load_config',
    # Exceptions
    'ServerlessPluginError',
    'ConfigurationError',
    'IntegrationError',
    'DownloadError',
    'ValidationError',
    # Logging
    'setup_plugin_logging',
    'get_logger',
    'log_performance',
    'log_async_performance',
    # Types
    'DownloadResult',
    'ModelSource',
    'HeadlessConfig',
    'ModalConfig',
    'DownloadStatus',
    # Retry
    'RetryConfig',
    'retry_with_backoff',
    'retry_async_with_backoff',
    'CircuitBreaker',
    # Cache
    'TTLCache',
    'FileCache',
    'cached_with_ttl',
    'cache_key',
    # Validation
    'Validator',
    'URLValidator',
    'CivitaiURLValidator',
    'HuggingFaceURLValidator',
    'validate',
    'validate_url',
    'validate_civitai_url',
    'validate_huggingface_url',
    # Health
    'HealthStatus',
    'HealthCheckResult',
    'HealthChecker',
    'get_health_checker',
]

