#!/usr/bin/env python3
"""
Civitai Integration Module for ComfyUI Model Download CLI

This module provides integration with Civitai's API for downloading models
and automatically organizing them into the correct ComfyUI directories.
"""

import os
import sys
import json
import logging
import requests
import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Add ComfyUI to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import folder_paths
except ImportError as e:
    print(f"Error importing ComfyUI modules: {e}")
    sys.exit(1)

logger = logging.getLogger(__name__)

class CivitaiAPI:
    """Client for interacting with Civitai's API."""
    
    BASE_URL = "https://civitai.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CIVITAI_API_KEY')
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def get_model_info(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model information from Civitai API."""
        try:
            url = f"{self.BASE_URL}/models/{model_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info for ID {model_id}: {e}")
            return None
    
    def get_model_version_info(self, version_id: int) -> Optional[Dict[str, Any]]:
        """Get model version information from Civitai API."""
        try:
            url = f"{self.BASE_URL}/model-versions/{version_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model version info for ID {version_id}: {e}")
            return None
    
    def search_models(self, query: str, limit: int = 10, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for models on Civitai."""
        try:
            params = {
                'query': query,
                'limit': min(limit, 100),  # Civitai has a max limit
                'page': 1
            }
            if model_type:
                params['types'] = model_type
            
            url = f"{self.BASE_URL}/models"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            return []
    
    def get_download_url(self, version_id: int, filename: Optional[str] = None) -> Optional[str]:
        """Get download URL for a model version."""
        try:
            version_info = self.get_model_version_info(version_id)
            if not version_info:
                return None
            
            files = version_info.get('files', [])
            if not files:
                return None
            
            # If filename specified, find matching file
            if filename:
                for file_info in files:
                    if file_info.get('name') == filename:
                        return file_info.get('downloadUrl')
            
            # Return the first file (usually the main model file)
            return files[0].get('downloadUrl')
        except Exception as e:
            logger.error(f"Failed to get download URL for version {version_id}: {e}")
            return None

class CivitaiURLParser:
    """Parser for Civitai URLs to extract model and version information."""
    
    @staticmethod
    def parse_civitai_url(url: str) -> Optional[Dict[str, Any]]:
        """Parse a Civitai URL and extract model ID and version ID."""
        try:
            # Remove any trailing slashes and normalize
            url = url.strip().rstrip('/')
            
            # Pattern for direct model version URLs (check this first)
            # https://civitai.com/models/12345/model-name/versions/67890
            version_pattern = r'civitai\.com/models/(\d+)/[^/]+/versions/(\d+)'
            match = re.search(version_pattern, url)
            if match:
                model_id = int(match.group(1))
                version_id = int(match.group(2))
                
                return {
                    'model_id': model_id,
                    'version_id': version_id,
                    'url_type': 'version'
                }
            
            # Pattern for model URLs with optional version
            # https://civitai.com/models/12345/model-name
            # https://civitai.com/models/12345/model-name?modelVersionId=67890
            model_pattern = r'civitai\.com/models/(\d+)(?:/[^/?]*)?(?:\?.*modelVersionId=(\d+))?'
            
            match = re.search(model_pattern, url)
            if match:
                model_id = int(match.group(1))
                version_id = int(match.group(2)) if match.group(2) else None
                
                return {
                    'model_id': model_id,
                    'version_id': version_id,
                    'url_type': 'model'
                }
            
            # Pattern for direct download URLs
            # https://civitai.com/api/download/models/67890
            download_pattern = r'civitai\.com/api/download/models/(\d+)'
            match = re.search(download_pattern, url)
            if match:
                version_id = int(match.group(1))
                
                return {
                    'model_id': None,  # Will need to be resolved
                    'version_id': version_id,
                    'url_type': 'download'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse Civitai URL {url}: {e}")
            return None
    
    @staticmethod
    def is_civitai_url(url: str) -> bool:
        """Check if a URL is a Civitai URL."""
        return 'civitai.com' in url.lower()

class CivitaiModelManager:
    """Manages Civitai models and their organization in ComfyUI."""
    
    # Mapping of Civitai model types to ComfyUI directories
    MODEL_TYPE_MAPPING = {
        'Checkpoint': 'checkpoints',
        'LORA': 'loras',
        'LoCon': 'loras',  # LoCon is a type of LoRA
        'TextualInversion': 'embeddings',
        'Hypernetwork': 'hypernetworks',
        'AestheticGradient': 'embeddings',  # Aesthetic gradients are often stored with embeddings
        'Controlnet': 'controlnet',
        'Poses': 'controlnet',  # Poses are often used with ControlNet
        'VAE': 'vae',
        'Upscaler': 'upscale_models',
        'MotionModule': 'motion_modules',  # For video generation
        'Wildcards': 'wildcards',  # For prompt wildcards
        'Other': 'checkpoints'  # Default fallback
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api = CivitaiAPI(api_key)
        self.url_parser = CivitaiURLParser()
        self.supported_extensions = {'.ckpt', '.pt', '.pt2', '.bin', '.pth', '.safetensors', '.pkl', '.sft', '.yaml', '.json'}
    
    def get_model_directory(self, model_type: str) -> str:
        """Get the ComfyUI directory for a given model type."""
        if model_type not in folder_paths.folder_names_and_paths:
            raise ValueError(f"Unknown model type: {model_type}")
        
        paths = folder_paths.get_folder_paths(model_type)
        if not paths:
            raise ValueError(f"No directory configured for model type: {model_type}")
        
        return paths[0]
    
    def determine_model_type(self, civitai_type: str, filename: str) -> str:
        """Determine the ComfyUI model type from Civitai type and filename."""
        # First try direct mapping
        if civitai_type in self.MODEL_TYPE_MAPPING:
            return self.MODEL_TYPE_MAPPING[civitai_type]
        
        # Fallback: try to determine from filename
        filename_lower = filename.lower()
        
        if any(ext in filename_lower for ext in ['lora', 'lycoris']):
            return 'loras'
        elif any(ext in filename_lower for ext in ['vae']):
            return 'vae'
        elif any(ext in filename_lower for ext in ['controlnet', 'control']):
            return 'controlnet'
        elif any(ext in filename_lower for ext in ['upscaler', 'upscale', 'esrgan']):
            return 'upscale_models'
        elif any(ext in filename_lower for ext in ['embedding', 'textual']):
            return 'embeddings'
        elif any(ext in filename_lower for ext in ['hypernetwork']):
            return 'hypernetworks'
        else:
            # Default to checkpoints for main models
            return 'checkpoints'
    
    def download_from_url(self, url: str, custom_dir: Optional[str] = None) -> bool:
        """Download a model from a Civitai URL with automatic model type detection."""
        try:
            # Parse the URL
            url_info = self.url_parser.parse_civitai_url(url)
            if not url_info:
                logger.error(f"Invalid Civitai URL: {url}")
                return False
            
            model_id = url_info['model_id']
            version_id = url_info['version_id']
            url_type = url_info['url_type']
            
            # If we have a download URL but no model_id, try to get it from version
            if url_type == 'download' and not model_id and version_id:
                version_info = self.api.get_model_version_info(version_id)
                if version_info:
                    model_id = version_info.get('modelId')
                    if not model_id:
                        logger.error(f"Could not determine model ID from version {version_id}")
                        return False
                else:
                    logger.error(f"Could not get version info for {version_id}")
                    return False
            
            if not model_id:
                logger.error(f"Could not determine model ID from URL: {url}")
                return False
            
            # Download the model with automatic type detection
            return self.download_model(model_id, version_id, custom_dir=custom_dir)
            
        except Exception as e:
            logger.error(f"Failed to download from URL {url}: {e}")
            return False
    
    def download_model(self, model_id: int, version_id: Optional[int] = None, 
                      filename: Optional[str] = None, custom_dir: Optional[str] = None) -> bool:
        """Download a model from Civitai and place it in the correct directory."""
        try:
            # Get model information
            model_info = self.api.get_model_info(model_id)
            if not model_info:
                logger.error(f"Failed to get model info for ID {model_id}")
                return False
            
            # Get version information
            if version_id:
                version_info = self.api.get_model_version_info(version_id)
            else:
                # Use the latest version
                versions = model_info.get('modelVersions', [])
                if not versions:
                    logger.error(f"No versions found for model {model_id}")
                    return False
                version_info = versions[0]
                version_id = version_info['id']
            
            if not version_info:
                logger.error(f"Failed to get version info for version {version_id}")
                return False
            
            # Determine model type and directory
            civitai_type = model_info.get('type', 'Other')
            files = version_info.get('files', [])
            
            if not files:
                logger.error(f"No files found for model version {version_id}")
                return False
            
            # Find the file to download
            target_file = None
            if filename:
                for file_info in files:
                    if file_info.get('name') == filename:
                        target_file = file_info
                        break
            else:
                # Use the first file (usually the main model)
                target_file = files[0]
            
            if not target_file:
                logger.error(f"File {filename} not found in model version {version_id}")
                return False
            
            # Determine the correct directory
            if custom_dir:
                model_dir = custom_dir
            else:
                comfyui_type = self.determine_model_type(civitai_type, target_file['name'])
                model_dir = self.get_model_directory(comfyui_type)
            
            # Ensure directory exists
            Path(model_dir).mkdir(parents=True, exist_ok=True)
            
            # Download the file
            download_url = target_file.get('downloadUrl')
            if not download_url:
                logger.error(f"No download URL found for file {target_file['name']}")
                return False
            
            # Add API key to download URL if available
            if self.api.api_key:
                separator = '&' if '?' in download_url else '?'
                download_url = f"{download_url}{separator}token={self.api.api_key}"
            
            # Download file
            destination = os.path.join(model_dir, target_file['name'])
            success = self._download_file(download_url, destination)
            
            if success:
                logger.info(f"Successfully downloaded {target_file['name']} to {destination}")
                
                # Save metadata
                self._save_metadata(destination, model_info, version_info, target_file)
                
                return True
            else:
                logger.error(f"Failed to download {target_file['name']}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {e}")
            return False
    
    def _download_file(self, url: str, destination: str) -> bool:
        """Download a file from URL to destination."""
        try:
            logger.info(f"Downloading {url} to {destination}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            sys.stdout.write(f"\rProgress: {percent:.1f}%")
                            sys.stdout.flush()
            
            print()  # New line after progress
            logger.info(f"Successfully downloaded {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def _save_metadata(self, file_path: str, model_info: Dict, version_info: Dict, file_info: Dict):
        """Save metadata about the downloaded model."""
        try:
            metadata = {
                'civitai_model_id': model_info.get('id'),
                'civitai_version_id': version_info.get('id'),
                'model_name': model_info.get('name'),
                'model_type': model_info.get('type'),
                'version_name': version_info.get('name'),
                'file_name': file_info.get('name'),
                'file_size': file_info.get('sizeKB', 0) * 1024,  # Convert KB to bytes
                'download_date': str(Path(file_path).stat().st_mtime),
                'description': model_info.get('description', ''),
                'tags': model_info.get('tags', []),
                'creator': model_info.get('creator', {}).get('username', ''),
                'nsfw': model_info.get('nsfw', False)
            }
            
            # Save metadata as JSON file
            metadata_path = f"{file_path}.civitai.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")
    
    def search_and_download(self, query: str, model_type: Optional[str] = None, 
                           limit: int = 5, auto_download: bool = False) -> List[Dict[str, Any]]:
        """Search for models and optionally download them."""
        results = self.api.search_models(query, limit, model_type)
        
        if not results:
            logger.info("No models found")
            return []
        
        print(f"Found {len(results)} models:")
        print("=" * 60)
        
        for i, model in enumerate(results, 1):
            print(f"{i}. {model.get('name', 'Unknown')}")
            print(f"   Type: {model.get('type', 'Unknown')}")
            print(f"   Creator: {model.get('creator', {}).get('username', 'Unknown')}")
            print(f"   Downloads: {model.get('downloadCount', 0):,}")
            print(f"   ID: {model.get('id')}")
            print()
        
        if auto_download:
            # Download the first result
            if results:
                model = results[0]
                model_id = model.get('id')
                if model_id:
                    logger.info(f"Auto-downloading model {model['name']}")
                    return self.download_model(model_id)
        
        return results
    
    def list_model_types(self) -> Dict[str, str]:
        """List available model types and their mappings."""
        return self.MODEL_TYPE_MAPPING.copy()
    
    def get_model_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a downloaded model."""
        metadata_path = f"{file_path}.civitai.json"
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read metadata: {e}")
        return None

def main():
    """Test the Civitai integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Civitai integration")
    parser.add_argument('--api-key', help='Civitai API key')
    parser.add_argument('--model-id', type=int, help='Model ID to download')
    parser.add_argument('--version-id', type=int, help='Version ID to download')
    parser.add_argument('--search', help='Search query')
    parser.add_argument('--list-types', action='store_true', help='List model types')
    
    args = parser.parse_args()
    
    manager = CivitaiModelManager(args.api_key)
    
    if args.list_types:
        print("Model type mappings:")
        for civitai_type, comfyui_type in manager.list_model_types().items():
            print(f"  {civitai_type} -> {comfyui_type}")
    
    elif args.search:
        results = manager.search_and_download(args.search, limit=5)
        print(f"Search completed. Found {len(results)} models.")
    
    elif args.model_id:
        success = manager.download_model(args.model_id, args.version_id)
        print(f"Download {'successful' if success else 'failed'}")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
