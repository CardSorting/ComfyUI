#!/usr/bin/env python3
"""
ComfyUI Advanced Model Download CLI Tool

This is an enhanced version of the model download tool with additional features:
- Model validation and metadata extraction
- Batch downloads
- Model search functionality
- Better progress tracking
- Configuration file support

Usage:
    python download_models_advanced.py --help
    python download_models_advanced.py search --query "stable diffusion"
    python download_models_advanced.py batch-download --config models.json
"""

import argparse
import os
import sys
import logging
import hashlib
import shutil
import urllib.request
import urllib.parse
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import urlparse
import re

# Add ComfyUI to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import folder_paths
    from comfy.cli_args import args
except ImportError as e:
    print(f"Error importing ComfyUI modules: {e}")
    print("Make sure you're running this script from the ComfyUI directory")
    sys.exit(1)

# Try to import optional dependencies
try:
    from huggingface_hub import hf_hub_download, list_repo_files, HfApi, search_models
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import safetensors
    SAFETENSORS_AVAILABLE = True
except ImportError:
    SAFETENSORS_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedModelDownloader:
    """Enhanced model downloader with advanced features."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.model_types = list(folder_paths.folder_names_and_paths.keys())
        self.supported_extensions = {'.ckpt', '.pt', '.pt2', '.bin', '.pth', '.safetensors', '.pkl', '.sft', '.yaml'}
        self.config = self._load_config(config_file)
        
        # Popular model repositories for quick access
        self.popular_models = {
            'checkpoints': {
                'stable-diffusion-v1-5': 'runwayml/stable-diffusion-v1-5',
                'stable-diffusion-v2-1': 'stabilityai/stable-diffusion-2-1',
                'stable-diffusion-xl': 'stabilityai/stable-diffusion-xl-base-1.0',
                'flux-dev': 'black-forest-labs/FLUX.1-dev',
                'flux-schnell': 'black-forest-labs/FLUX.1-schnell',
            },
            'loras': {
                'detail-tweaker': 'stabilityai/stable-diffusion-xl-base-1.0',
                'style-lora': 'stabilityai/stable-diffusion-xl-base-1.0',
            },
            'vae': {
                'vae-ft-mse': 'stabilityai/sd-vae-ft-mse',
                'vae-ft-ema': 'stabilityai/sd-vae-ft-ema',
            }
        }
    
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file."""
        default_config = {
            'download_timeout': 300,
            'max_retries': 3,
            'verify_hashes': True,
            'create_backups': False,
            'default_model_type': 'checkpoints'
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def get_model_directory(self, model_type: str) -> str:
        """Get the directory path for a specific model type."""
        if model_type not in folder_paths.folder_names_and_paths:
            raise ValueError(f"Unknown model type: {model_type}. Available types: {', '.join(self.model_types)}")
        
        paths = folder_paths.get_folder_paths(model_type)
        if not paths:
            raise ValueError(f"No directory configured for model type: {model_type}")
        
        return paths[0]
    
    def ensure_directory_exists(self, path: str) -> None:
        """Ensure the directory exists, create if it doesn't."""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    def download_file_with_progress(self, url: str, destination: str, expected_hash: Optional[str] = None) -> bool:
        """Download a file with enhanced progress tracking."""
        try:
            logger.info(f"Downloading {url} to {destination}")
            
            # Ensure destination directory exists
            self.ensure_directory_exists(os.path.dirname(destination))
            
            # Use requests if available for better error handling
            if REQUESTS_AVAILABLE:
                return self._download_with_requests(url, destination, expected_hash)
            else:
                return self._download_with_urllib(url, destination, expected_hash)
                
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def _download_with_requests(self, url: str, destination: str, expected_hash: Optional[str] = None) -> bool:
        """Download using requests library."""
        try:
            response = requests.get(url, stream=True, timeout=self.config.get('download_timeout', 300))
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                if TQDM_AVAILABLE and total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
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
            
            # Verify hash if provided
            if expected_hash and self.config.get('verify_hashes', True):
                if not self.verify_file_hash(destination, expected_hash):
                    logger.error(f"Hash verification failed for {destination}")
                    return False
            
            logger.info(f"Successfully downloaded {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download with requests: {e}")
            return False
    
    def _download_with_urllib(self, url: str, destination: str, expected_hash: Optional[str] = None) -> bool:
        """Download using urllib (fallback)."""
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) / total_size)
                sys.stdout.write(f"\rProgress: {percent:.1f}%")
                sys.stdout.flush()
        
        try:
            urllib.request.urlretrieve(url, destination, reporthook=show_progress)
            print()  # New line after progress
            
            # Verify hash if provided
            if expected_hash and self.config.get('verify_hashes', True):
                if not self.verify_file_hash(destination, expected_hash):
                    logger.error(f"Hash verification failed for {destination}")
                    return False
            
            logger.info(f"Successfully downloaded {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download with urllib: {e}")
            return False
    
    def verify_file_hash(self, file_path: str, expected_hash: str) -> bool:
        """Verify file hash (SHA-256)."""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash.lower() == expected_hash.lower()
        except Exception as e:
            logger.error(f"Error verifying hash for {file_path}: {e}")
            return False
    
    def extract_model_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from model file."""
        metadata = {
            'file_path': file_path,
            'size_bytes': os.path.getsize(file_path),
            'size_mb': os.path.getsize(file_path) / (1024 * 1024),
            'modified': os.path.getmtime(file_path)
        }
        
        # Try to extract SafeTensors metadata
        if SAFETENSORS_AVAILABLE and file_path.endswith('.safetensors'):
            try:
                with safetensors.safe_open(file_path, framework="pt") as f:
                    metadata['safetensors_keys'] = list(f.keys())
                    metadata['safetensors_metadata'] = f.metadata()
            except Exception as e:
                logger.debug(f"Could not extract SafeTensors metadata: {e}")
        
        return metadata
    
    def search_models(self, query: str, model_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search for models on Hugging Face."""
        if not HF_AVAILABLE:
            logger.error("Hugging Face Hub not available. Install with: pip install huggingface_hub")
            return []
        
        try:
            # Build search query
            search_query = query
            if model_type:
                search_query += f" {model_type}"
            
            # Search models
            models = search_models(query=search_query, limit=limit)
            
            results = []
            for model in models:
                results.append({
                    'id': model.id,
                    'author': model.author,
                    'downloads': model.downloads,
                    'tags': model.tags,
                    'created_at': model.created_at,
                    'last_modified': model.last_modified
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            return []
    
    def download_from_huggingface(self, repo_id: str, model_type: str, filename: Optional[str] = None) -> bool:
        """Download model from Hugging Face Hub with enhanced features."""
        if not HF_AVAILABLE:
            logger.error("Hugging Face Hub not available. Install with: pip install huggingface_hub")
            return False
        
        try:
            # Get model directory
            model_dir = self.get_model_directory(model_type)
            
            # List files in the repository
            api = HfApi()
            repo_files = list_repo_files(repo_id, repo_type="model")
            
            # Filter files by supported extensions
            model_files = [f for f in repo_files if any(f.endswith(ext) for ext in self.supported_extensions)]
            
            if not model_files:
                logger.error(f"No supported model files found in {repo_id}")
                return False
            
            # If filename specified, look for it
            if filename:
                if filename not in repo_files:
                    logger.error(f"File {filename} not found in {repo_id}")
                    return False
                model_files = [filename]
            
            # Download files
            success = True
            for file in model_files:
                try:
                    logger.info(f"Downloading {file} from {repo_id}")
                    downloaded_path = hf_hub_download(
                        repo_id=repo_id,
                        filename=file,
                        cache_dir=None,
                        local_dir=model_dir,
                        local_dir_use_symlinks=False
                    )
                    logger.info(f"Downloaded to: {downloaded_path}")
                    
                    # Extract metadata
                    metadata = self.extract_model_metadata(downloaded_path)
                    logger.info(f"Model metadata: {metadata}")
                    
                except Exception as e:
                    logger.error(f"Failed to download {file}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to download from Hugging Face: {e}")
            return False
    
    def batch_download(self, config_file: str) -> bool:
        """Download multiple models from a configuration file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            downloads = config.get('downloads', [])
            if not downloads:
                logger.error("No downloads specified in config file")
                return False
            
            success_count = 0
            total_count = len(downloads)
            
            for i, download in enumerate(downloads, 1):
                logger.info(f"Processing download {i}/{total_count}: {download.get('name', 'unnamed')}")
                
                model_type = download.get('model_type', self.config.get('default_model_type', 'checkpoints'))
                source = download.get('source')
                
                if source == 'huggingface':
                    repo_id = download.get('repo_id')
                    filename = download.get('filename')
                    if self.download_from_huggingface(repo_id, model_type, filename):
                        success_count += 1
                
                elif source == 'url':
                    url = download.get('url')
                    filename = download.get('filename')
                    expected_hash = download.get('hash')
                    model_dir = self.get_model_directory(model_type)
                    destination = os.path.join(model_dir, filename or os.path.basename(urlparse(url).path))
                    if self.download_file_with_progress(url, destination, expected_hash):
                        success_count += 1
                
                else:
                    logger.error(f"Unknown source: {source}")
            
            logger.info(f"Batch download completed: {success_count}/{total_count} successful")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Failed to process batch download: {e}")
            return False
    
    def list_popular_models(self, model_type: Optional[str] = None) -> None:
        """List popular models for quick download."""
        if model_type:
            if model_type not in self.popular_models:
                logger.error(f"No popular models available for type: {model_type}")
                return
            
            print(f"Popular {model_type} models:")
            print("=" * 40)
            for name, repo_id in self.popular_models[model_type].items():
                print(f"  {name}: {repo_id}")
        else:
            print("Popular models by type:")
            print("=" * 30)
            for mt, models in self.popular_models.items():
                print(f"\n{mt.upper()}:")
                for name, repo_id in models.items():
                    print(f"  {name}: {repo_id}")

def main():
    parser = argparse.ArgumentParser(
        description="ComfyUI Advanced Model Download CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for models
  python download_models_advanced.py search --query "stable diffusion" --limit 5
  
  # List popular models
  python download_models_advanced.py popular --model-type checkpoints
  
  # Download with metadata extraction
  python download_models_advanced.py download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5
  
  # Batch download from config
  python download_models_advanced.py batch-download --config models.json
        """
    )
    
    parser.add_argument('--config', help='Configuration file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for models on Hugging Face')
    search_parser.add_argument('--query', required=True, help='Search query')
    search_parser.add_argument('--model-type', help='Filter by model type')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
    
    # Popular models command
    popular_parser = subparsers.add_parser('popular', help='List popular models')
    popular_parser.add_argument('--model-type', help='Filter by model type')
    
    # Download command (same as basic version)
    download_parser = subparsers.add_parser('download', help='Download models')
    download_parser.add_argument('--model-type', required=True,
                               choices=folder_paths.folder_names_and_paths.keys(),
                               help='Type of model to download')
    download_parser.add_argument('--source', required=True, choices=['huggingface', 'url'],
                               help='Source to download from')
    download_parser.add_argument('--repo', help='Hugging Face repository ID')
    download_parser.add_argument('--url', help='Direct URL to download from')
    download_parser.add_argument('--filename', help='Specific filename to download')
    download_parser.add_argument('--hash', help='Expected SHA-256 hash for verification')
    
    # Batch download command
    batch_parser = subparsers.add_parser('batch-download', help='Download multiple models from config')
    batch_parser.add_argument('--config', required=True, help='Configuration file with download list')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    downloader = AdvancedModelDownloader(args.config)
    
    if args.command == 'search':
        results = downloader.search_models(args.query, args.model_type, args.limit)
        if results:
            print(f"Found {len(results)} models:")
            print("=" * 50)
            for i, model in enumerate(results, 1):
                print(f"{i}. {model['id']}")
                print(f"   Author: {model['author']}")
                print(f"   Downloads: {model['downloads']:,}")
                print(f"   Tags: {', '.join(model['tags'][:5])}")
                print()
        else:
            print("No models found.")
    
    elif args.command == 'popular':
        downloader.list_popular_models(args.model_type)
    
    elif args.command == 'download':
        success = False
        
        if args.source == 'huggingface':
            if not args.repo:
                logger.error("--repo is required for huggingface source")
                return
            success = downloader.download_from_huggingface(args.repo, args.model_type, args.filename)
        
        elif args.source == 'url':
            if not args.url:
                logger.error("--url is required for url source")
                return
            model_dir = downloader.get_model_directory(args.model_type)
            destination = os.path.join(model_dir, args.filename or os.path.basename(urlparse(args.url).path))
            success = downloader.download_file_with_progress(args.url, destination, args.hash)
        
        if success:
            logger.info("Download completed successfully!")
        else:
            logger.error("Download failed!")
            sys.exit(1)
    
    elif args.command == 'batch-download':
        success = downloader.batch_download(args.config)
        if not success:
            sys.exit(1)

if __name__ == '__main__':
    main()
