"""
Custom Exceptions

Industry-standard exception hierarchy for better error handling
and debugging.
"""

from typing import Optional, Dict, Any


class ServerlessPluginError(Exception):
    """
    Base exception for all plugin errors.
    
    Provides structured error information with context.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            context: Additional context dictionary
            cause: Underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """String representation with context."""
        parts = [self.message]
        
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")
        
        if self.cause:
            parts.append(f"Caused by: {self.cause}")
        
        return " | ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'cause': str(self.cause) if self.cause else None,
        }


class ConfigurationError(ServerlessPluginError):
    """Raised when configuration is invalid or missing."""
    pass


class IntegrationError(ServerlessPluginError):
    """Raised when integration (Civitai, HuggingFace) fails."""
    pass


class DownloadError(ServerlessPluginError):
    """Raised when model download fails."""
    pass


class ValidationError(ServerlessPluginError):
    """Raised when input validation fails."""
    pass


class HeadlessConfigError(ConfigurationError):
    """Raised when headless mode configuration fails."""
    pass


class ModalDeploymentError(ServerlessPluginError):
    """Raised when Modal deployment fails."""
    pass

