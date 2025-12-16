"""
Health Check System

Industry-standard health check implementation for monitoring
plugin status and dependencies.
"""

import time
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """
    Result of a health check.
    
    Attributes:
        status: Health status
        message: Human-readable message
        details: Additional details dictionary
        timestamp: Check timestamp
        duration_ms: Check duration in milliseconds
    """
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0


class HealthChecker:
    """
    Health check manager.
    
    Manages multiple health checks and provides aggregated status.
    """
    
    def __init__(self):
        """Initialize health checker."""
        self._checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._cache_ttl: float = 60.0  # Cache results for 60 seconds
        self._cached_results: Dict[str, tuple[HealthCheckResult, float]] = {}
    
    def register_check(
        self,
        name: str,
        check_func: Callable[[], HealthCheckResult],
        cache_ttl: Optional[float] = None
    ) -> None:
        """
        Register a health check.
        
        Args:
            name: Check name
            check_func: Function that returns HealthCheckResult
            cache_ttl: Optional cache TTL override
        """
        self._checks[name] = check_func
        if cache_ttl is not None:
            # Store cache TTL per check (future enhancement)
            pass
    
    def check(self, name: Optional[str] = None) -> HealthCheckResult:
        """
        Run a specific health check or all checks.
        
        Args:
            name: Optional check name (runs all if None)
        
        Returns:
            HealthCheckResult or aggregated result
        """
        if name:
            return self._run_check(name)
        else:
            return self._run_all_checks()
    
    def _run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self._checks:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' not found"
            )
        
        # Check cache
        if name in self._cached_results:
            result, cached_time = self._cached_results[name]
            if time.time() - cached_time < self._cache_ttl:
                return result
        
        # Run check
        start_time = time.time()
        try:
            result = self._checks[name]()
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            
            # Cache result
            self._cached_results[name] = (result, time.time())
            
            return result
        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}", exc_info=True)
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def _run_all_checks(self) -> HealthCheckResult:
        """Run all health checks and aggregate results."""
        results: Dict[str, HealthCheckResult] = {}
        overall_status = HealthStatus.HEALTHY
        
        for name in self._checks:
            result = self._run_check(name)
            results[name] = result
            
            # Determine overall status
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        # Aggregate message
        healthy_count = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
        total_count = len(results)
        
        message = f"{healthy_count}/{total_count} checks healthy"
        
        return HealthCheckResult(
            status=overall_status,
            message=message,
            details={'checks': {name: r.to_dict() for name, r in results.items()}}
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get overall health status as dictionary.
        
        Returns:
            Status dictionary
        """
        result = self._run_all_checks()
        return {
            'status': result.status.value,
            'message': result.message,
            'timestamp': result.timestamp,
            'details': result.details
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or create global health checker instance."""
    global _health_checker
    
    if _health_checker is None:
        _health_checker = HealthChecker()
        _register_default_checks(_health_checker)
    
    return _health_checker


def _register_default_checks(checker: HealthChecker) -> None:
    """Register default health checks."""
    
    def check_config() -> HealthCheckResult:
        """Check configuration."""
        try:
            from .config import get_plugin_config
            config = get_plugin_config()
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Configuration loaded",
                details={'config_file': str(config.config_file) if hasattr(config, 'config_file') else None}
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Configuration check failed: {e}"
            )
    
    def check_integrations() -> HealthCheckResult:
        """Check integrations availability."""
        details = {}
        status = HealthStatus.HEALTHY
        
        # Check Civitai
        try:
            from ..integrations.civitai import CivitaiModelManager
            details['civitai'] = 'available'
        except Exception as e:
            details['civitai'] = f'unavailable: {e}'
            status = HealthStatus.DEGRADED
        
        # Check HuggingFace
        try:
            from ..integrations.huggingface import HuggingFaceModelManager
            details['huggingface'] = 'available'
        except Exception as e:
            details['huggingface'] = f'unavailable: {e}'
            status = HealthStatus.DEGRADED
        
        return HealthCheckResult(
            status=status,
            message="Integration checks completed",
            details=details
        )
    
    checker.register_check("config", check_config)
    checker.register_check("integrations", check_integrations)


# Add to_dict method to HealthCheckResult
def _health_check_result_to_dict(self) -> Dict[str, Any]:
    """Convert HealthCheckResult to dictionary."""
    return {
        'status': self.status.value,
        'message': self.message,
        'details': self.details,
        'timestamp': self.timestamp,
        'duration_ms': self.duration_ms,
    }

HealthCheckResult.to_dict = _health_check_result_to_dict

