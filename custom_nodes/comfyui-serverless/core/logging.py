"""
Structured Logging

Industry-standard structured logging with JSON support,
context propagation, and performance monitoring.
"""

import logging
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from functools import wraps
import time


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Produces JSON logs that are easy to parse and search.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration * 1000
        
        if hasattr(record, 'error_code'):
            log_data['error_code'] = record.error_code
        
        return json.dumps(log_data, default=str)


class ContextFilter(logging.Filter):
    """Add context to log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record."""
        if self.context:
            record.context = self.context
        return True


def setup_plugin_logging(
    level: str = "INFO",
    format_type: str = "text",
    log_file: Optional[Path] = None,
    context: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Set up structured logging for the plugin.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 'json' or 'text'
        log_file: Optional file to write logs to
        context: Optional context dictionary to add to all logs
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger("comfyui_serverless")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if format_type == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    if context:
        console_handler.addFilter(ContextFilter(context))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        if context:
            file_handler.addFilter(ContextFilter(context))
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Optional logger name (defaults to plugin name)
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"comfyui_serverless.{name}")
    return logging.getLogger("comfyui_serverless")


def log_performance(func):
    """
    Decorator to log function execution time.
    
    Usage:
        @log_performance
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.debug(
                f"{func.__name__} completed",
                extra={
                    'function': func.__name__,
                    'duration': duration,
                    'status': 'success'
                }
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"{func.__name__} failed: {e}",
                extra={
                    'function': func.__name__,
                    'duration': duration,
                    'status': 'error',
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    return wrapper


def log_async_performance(func):
    """
    Decorator to log async function execution time.
    
    Usage:
        @log_async_performance
        async def my_function():
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.debug(
                f"{func.__name__} completed",
                extra={
                    'function': func.__name__,
                    'duration': duration,
                    'status': 'success'
                }
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"{func.__name__} failed: {e}",
                extra={
                    'function': func.__name__,
                    'duration': duration,
                    'status': 'error',
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    return wrapper

