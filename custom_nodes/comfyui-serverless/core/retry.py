"""
Retry Mechanisms

Industry-standard retry logic with exponential backoff,
jitter, and circuit breaker patterns.
"""

import time
import random
from typing import Callable, TypeVar, Optional, List, Type
from functools import wraps
import logging

from .exceptions import ServerlessPluginError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            retryable_exceptions: List of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.initial_delay * (self.exponential_base ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)  # Ensure non-negative
        
        return delay


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        config: Retry configuration (uses defaults if None)
        on_retry: Optional callback called before each retry
    
    Usage:
        @retry_with_backoff()
        def my_function():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.debug(f"Exception {type(e).__name__} is not retryable, raising immediately")
                        raise
                    
                    # Check if we have more attempts
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt + 1)
                        
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {config.max_attempts} attempts")
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic failed unexpectedly")
        
        return wrapper
    
    return decorator


def retry_async_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        config: Retry configuration (uses defaults if None)
        on_retry: Optional callback called before each retry
    
    Usage:
        @retry_async_with_backoff()
        async def my_function():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.debug(f"Exception {type(e).__name__} is not retryable, raising immediately")
                        raise
                    
                    # Check if we have more attempts
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt + 1)
                        
                        # Use asyncio.sleep for async functions
                        import asyncio
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {config.max_attempts} attempts")
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic failed unexpectedly")
        
        return wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by stopping requests when
    failure rate exceeds threshold.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds before attempting to close circuit
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            if time.time() - (self.last_failure_time or 0) > self.timeout:
                self.state = "half_open"
                logger.info("Circuit breaker: Moving to half-open state")
            else:
                raise ServerlessPluginError(
                    "Circuit breaker is open",
                    error_code="CIRCUIT_OPEN",
                    context={'state': self.state}
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == "half_open":
            self.state = "closed"
            logger.info("Circuit breaker: Closed after successful call")
        
        self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker: Opened after {self.failure_count} failures"
            )

