"""
Model Integration Modules

This package contains integrations for downloading models from various sources:
- Civitai: Civitai.com model downloads
- HuggingFace: HuggingFace Hub model downloads
"""

# Import managers for easy access
try:
    from .civitai import CivitaiModelManager, CivitaiAPI, CivitaiURLParser
except ImportError as e:
    # Civitai integration may have optional dependencies
    CivitaiModelManager = None
    CivitaiAPI = None
    CivitaiURLParser = None

try:
    from .huggingface import HuggingFaceModelManager, HuggingFaceURLParser
except ImportError as e:
    # HuggingFace integration requires huggingface_hub
    HuggingFaceModelManager = None
    HuggingFaceURLParser = None

__all__ = [
    'CivitaiModelManager',
    'CivitaiAPI',
    'CivitaiURLParser',
    'HuggingFaceModelManager',
    'HuggingFaceURLParser',
]

