"""
Type Definitions

Comprehensive type definitions for type safety and IDE support.
"""

from typing import TypedDict, Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ModelSource(str, Enum):
    """Model source types."""
    CIVITAI = "civitai"
    HUGGINGFACE = "huggingface"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class DownloadStatus(str, Enum):
    """Download status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadResult:
    """
    Result of a model download operation.
    
    Attributes:
        success: Whether download succeeded
        file_path: Path to downloaded file
        status: Download status
        source: Model source
        message: Status message
        metadata: Additional metadata
        error: Error message if failed
    """
    success: bool
    file_path: Optional[Path] = None
    status: DownloadStatus = DownloadStatus.PENDING
    source: ModelSource = ModelSource.UNKNOWN
    message: str = ""
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'file_path': str(self.file_path) if self.file_path else None,
            'status': self.status.value,
            'source': self.source.value,
            'message': self.message,
            'metadata': self.metadata or {},
            'error': self.error,
        }


class HeadlessConfig(TypedDict, total=False):
    """Headless mode configuration."""
    enabled: bool
    disable_progress_bars: bool
    disable_telemetry: bool
    disable_auto_launch: bool
    tqdm_disabled: bool


class ModalConfig(TypedDict, total=False):
    """Modal deployment configuration."""
    app_name: str
    models_volume_name: str
    outputs_volume_name: str
    gpu_config: str
    timeout: int
    scaledown_window: int
    image_base: str
    python_version: str


class CivitaiConfig(TypedDict, total=False):
    """Civitai integration configuration."""
    enabled: bool
    api_key: Optional[str]
    base_url: str
    timeout: int
    max_retries: int


class HuggingFaceConfig(TypedDict, total=False):
    """HuggingFace integration configuration."""
    enabled: bool
    api_token: Optional[str]
    cache_dir: str
    timeout: int
    max_retries: int


class PluginMetadata(TypedDict):
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: str
    comfyui_version: Optional[str]


class NodeInfo(TypedDict):
    """Information about a node."""
    node_id: str
    display_name: str
    category: str
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]

