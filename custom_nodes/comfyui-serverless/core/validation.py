"""
Input Validation

Comprehensive validation utilities with type checking,
range validation, and custom validators.
"""

import re
from typing import Any, Callable, Optional, List, Union
from urllib.parse import urlparse
from pathlib import Path

from .exceptions import ValidationError


class Validator:
    """Base validator class."""
    
    @staticmethod
    def validate(value: Any) -> bool:
        """Validate value. Returns True if valid."""
        raise NotImplementedError
    
    @staticmethod
    def error_message(value: Any) -> str:
        """Get error message for invalid value."""
        return "Validation failed"


class URLValidator(Validator):
    """Validate URLs."""
    
    @staticmethod
    def validate(value: Any) -> bool:
        """Check if value is a valid URL."""
        if not isinstance(value, str):
            return False
        
        try:
            result = urlparse(value)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def error_message(value: Any) -> str:
        return f"Invalid URL: {value}"


class CivitaiURLValidator(Validator):
    """Validate Civitai URLs."""
    
    CIVITAI_PATTERNS = [
        r'civitai\.com/models/(\d+)',
        r'civitai\.com/api/download/models/(\d+)',
    ]
    
    @staticmethod
    def validate(value: Any) -> bool:
        """Check if value is a valid Civitai URL."""
        if not isinstance(value, str):
            return False
        
        return any(re.search(pattern, value) for pattern in CivitaiURLValidator.CIVITAI_PATTERNS)
    
    @staticmethod
    def error_message(value: Any) -> str:
        return f"Invalid Civitai URL: {value}"


class HuggingFaceURLValidator(Validator):
    """Validate HuggingFace URLs."""
    
    @staticmethod
    def validate(value: Any) -> bool:
        """Check if value is a valid HuggingFace URL."""
        if not isinstance(value, str):
            return False
        
        pattern = r'huggingface\.co/([^/]+)/([^/]+)'
        return bool(re.search(pattern, value))
    
    @staticmethod
    def error_message(value: Any) -> str:
        return f"Invalid HuggingFace URL: {value}"


class PathValidator(Validator):
    """Validate file paths."""
    
    @staticmethod
    def validate(value: Any) -> bool:
        """Check if value is a valid path."""
        if isinstance(value, (str, Path)):
            try:
                Path(value)
                return True
            except Exception:
                return False
        return False
    
    @staticmethod
    def error_message(value: Any) -> str:
        return f"Invalid path: {value}"


class RangeValidator(Validator):
    """Validate numeric ranges."""
    
    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        """Initialize range validator."""
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> bool:
        """Check if value is within range."""
        try:
            num_value = float(value)
            
            if self.min_value is not None and num_value < self.min_value:
                return False
            
            if self.max_value is not None and num_value > self.max_value:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def error_message(self, value: Any) -> str:
        range_str = []
        if self.min_value is not None:
            range_str.append(f">= {self.min_value}")
        if self.max_value is not None:
            range_str.append(f"<= {self.max_value}")
        
        return f"Value {value} out of range ({', '.join(range_str)})"


class TypeValidator(Validator):
    """Validate value types."""
    
    def __init__(self, expected_type: type):
        """Initialize type validator."""
        self.expected_type = expected_type
    
    def validate(self, value: Any) -> bool:
        """Check if value is of expected type."""
        return isinstance(value, self.expected_type)
    
    def error_message(self, value: Any) -> str:
        return f"Expected {self.expected_type.__name__}, got {type(value).__name__}"


class ChoiceValidator(Validator):
    """Validate value is in allowed choices."""
    
    def __init__(self, choices: List[Any]):
        """Initialize choice validator."""
        self.choices = choices
    
    def validate(self, value: Any) -> bool:
        """Check if value is in choices."""
        return value in self.choices
    
    def error_message(self, value: Any) -> str:
        return f"Value {value} not in allowed choices: {self.choices}"


def validate(
    value: Any,
    validators: List[Validator],
    raise_on_error: bool = True
) -> bool:
    """
    Validate value against multiple validators.
    
    Args:
        value: Value to validate
        validators: List of validators to apply
        raise_on_error: Whether to raise exception on validation failure
    
    Returns:
        True if valid, False otherwise
    
    Raises:
        ValidationError: If validation fails and raise_on_error is True
    """
    for validator in validators:
        if not validator.validate(value):
            error_msg = validator.error_message(value)
            
            if raise_on_error:
                raise ValidationError(
                    error_msg,
                    error_code="VALIDATION_FAILED",
                    context={'value': value, 'validator': validator.__class__.__name__}
                )
            
            return False
    
    return True


def validate_url(url: str, raise_on_error: bool = True) -> bool:
    """Validate URL."""
    return validate(url, [URLValidator()], raise_on_error)


def validate_civitai_url(url: str, raise_on_error: bool = True) -> bool:
    """Validate Civitai URL."""
    return validate(url, [CivitaiURLValidator()], raise_on_error)


def validate_huggingface_url(url: str, raise_on_error: bool = True) -> bool:
    """Validate HuggingFace URL."""
    return validate(url, [HuggingFaceURLValidator()], raise_on_error)

