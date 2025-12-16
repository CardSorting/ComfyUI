"""
ComfyUI Serverless Nodes

This package contains ComfyUI nodes for serverless functionality:
- Model download nodes (Civitai, HuggingFace, Generic)
- Headless configuration nodes (optional)
"""

from .model_download import (
    CivitaiDownloadNode,
    HuggingFaceDownloadNode,
    GenericModelDownloadNode
)

__all__ = [
    'CivitaiDownloadNode',
    'HuggingFaceDownloadNode',
    'GenericModelDownloadNode',
]

