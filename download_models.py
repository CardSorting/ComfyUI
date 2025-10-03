#!/usr/bin/env python3
"""
ComfyUI Model Download CLI Tool

This script provides a command-line interface for downloading models to ComfyUI.
It supports downloading from Hugging Face Hub, direct URLs, and other sources.

Usage:
    python download_models.py --help
    python download_models.py list
    python download_models.py download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5
    python download_models.py download --model-type loras --url https://example.com/model.safetensors
"""

import argparse
import os
import sys
import logging
import hashlib
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import json
import time
from urllib.parse import urlparse

# Add ComfyUI to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import folder_paths
    from comfy.cli_args import args
except ImportError as e:
    print(f"Error importing ComfyUI modules: {e}")
    print("Make sure you're running this script from the ComfyUI directory")
    sys.exit(1)

# Try to import Civitai integration
try:
    from civitai_integration import CivitaiModelManager
    CIVITAI_AVAILABLE = True
except ImportError:
    CIVITAI_AVAILABLE = False
    print("Warning: Civitai integration not available. Install with: pip install requests")

# Try to import Hugging Face integration
try:
    from huggingface_integration import HuggingFaceModelManager
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("Warning: Hugging Face integration not available. Install with: pip install huggingface_hub")

# Note: HF_AVAILABLE is set above in the HuggingFaceModelManager import

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Handles downloading models to ComfyUI directories."""
    
    def __init__(self):
        self.model_types = list(folder_paths.folder_names_and_paths.keys())
        self.supported_extensions = {'.ckpt', '.pt', '.pt2', '.bin', '.pth', '.safetensors', '.pkl', '.sft', '.yaml'}
        
    def get_model_directory(self, model_type: str) -> str:
        """Get the directory path for a specific model type."""
        if model_type not in folder_paths.folder_names_and_paths:
            raise ValueError(f"Unknown model type: {model_type}. Available types: {', '.join(self.model_types)}")
        
        paths = folder_paths.get_folder_paths(model_type)
        if not paths:
            raise ValueError(f"No directory configured for model type: {model_type}")
        
        # Use the first (default) path
        return paths[0]
    
    def ensure_directory_exists(self, path: str) -> None:
        """Ensure the directory exists, create if it doesn't."""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, destination: str, expected_hash: Optional[str] = None) -> bool:
        """Download a file from URL to destination with optional hash verification."""
        try:
            logger.info(f"Downloading {url} to {destination}")
            
            # Ensure destination directory exists
            self.ensure_directory_exists(os.path.dirname(destination))
            
            # Download with progress
            def show_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) / total_size)
                    sys.stdout.write(f"\rProgress: {percent:.1f}%")
                    sys.stdout.flush()
            
            urllib.request.urlretrieve(url, destination, reporthook=show_progress)
            print()  # New line after progress
            
            # Verify hash if provided
            if expected_hash:
                if not self.verify_file_hash(destination, expected_hash):
                    logger.error(f"Hash verification failed for {destination}")
                    return False
            
            logger.info(f"Successfully downloaded {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
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
    
    def download_from_huggingface(self, repo_id: str, model_type: str, filename: Optional[str] = None) -> bool:
        """Download model from Hugging Face Hub."""
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
                        cache_dir=None,  # Use default cache
                        local_dir=model_dir,
                        local_dir_use_symlinks=False
                    )
                    logger.info(f"Downloaded to: {downloaded_path}")
                except Exception as e:
                    logger.error(f"Failed to download {file}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to download from Hugging Face: {e}")
            return False
    
    def download_from_url(self, url: str, model_type: Optional[str] = None, filename: Optional[str] = None) -> bool:
        """Download model from direct URL with automatic type detection."""
        try:
            # Check if this is a Civitai URL and handle it specially
            if CIVITAI_AVAILABLE:
                from civitai_integration import CivitaiURLParser
                url_parser = CivitaiURLParser()
                if url_parser.is_civitai_url(url):
                    logger.info("🔍 Detected Civitai URL, using Civitai integration with auto-detection...")
                    manager = CivitaiModelManager()
                    return manager.download_from_url(url)
            
            # Check if this is a Hugging Face URL and handle it specially
            if HF_AVAILABLE:
                from huggingface_integration import HuggingFaceURLParser
                url_parser = HuggingFaceURLParser()
                if url_parser.is_huggingface_url(url):
                    logger.info("🔍 Detected Hugging Face URL, using Hugging Face integration with auto-detection...")
                    manager = HuggingFaceModelManager()
                    return manager.download_from_url(url)
            
            # For other URLs, model_type is required
            if not model_type:
                logger.error("Model type is required for non-Civitai/Hugging Face URLs. Use --model-type or provide a supported URL for auto-detection.")
                return False
            
            # Get model directory
            model_dir = self.get_model_directory(model_type)
            
            # Determine filename
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    filename = f"downloaded_model_{int(time.time())}.safetensors"
            
            destination = os.path.join(model_dir, filename)
            
            # Download file
            return self.download_file(url, destination)
            
        except Exception as e:
            logger.error(f"Failed to download from URL: {e}")
            return False
    
    def download_from_civitai(self, model_id: Optional[int] = None, version_id: Optional[int] = None, 
                             filename: Optional[str] = None, api_key: Optional[str] = None, 
                             url: Optional[str] = None) -> bool:
        """Download model from Civitai."""
        if not CIVITAI_AVAILABLE:
            logger.error("Civitai integration not available. Install with: pip install requests")
            return False
        
        try:
            manager = CivitaiModelManager(api_key)
            
            # If URL is provided, use URL-based download
            if url:
                return manager.download_from_url(url)
            
            # Otherwise use model_id/version_id
            if not model_id:
                logger.error("Either model_id or url must be provided for Civitai download")
                return False
            
            return manager.download_model(model_id, version_id, filename)
        except Exception as e:
            logger.error(f"Failed to download from Civitai: {e}")
            return False
    
    def download_from_huggingface(self, repo_id: Optional[str] = None, branch: Optional[str] = None,
                                 api_token: Optional[str] = None, url: Optional[str] = None) -> bool:
        """Download model from Hugging Face."""
        if not HF_AVAILABLE:
            logger.error("Hugging Face integration not available. Install with: pip install huggingface_hub")
            return False
        
        try:
            manager = HuggingFaceModelManager(api_token)
            
            # If URL is provided, use URL-based download
            if url:
                return manager.download_from_url(url)
            
            # Otherwise use repo_id
            if not repo_id:
                logger.error("Either repo_id or url must be provided for Hugging Face download")
                return False
            
            return manager.download_model(repo_id, branch or 'main')
        except Exception as e:
            logger.error(f"Failed to download from Hugging Face: {e}")
            return False
    
    def search_civitai_models(self, query: str, model_type: Optional[str] = None, 
                             limit: int = 10, api_key: Optional[str] = None) -> List[Dict]:
        """Search for models on Civitai."""
        if not CIVITAI_AVAILABLE:
            logger.error("Civitai integration not available. Install with: pip install requests")
            return []
        
        try:
            manager = CivitaiModelManager(api_key)
            return manager.search_and_download(query, model_type, limit)
        except Exception as e:
            logger.error(f"Failed to search Civitai models: {e}")
            return []
    
    def search_huggingface_models(self, query: str, limit: int = 10, api_token: Optional[str] = None) -> List[Dict]:
        """Search for models on Hugging Face."""
        if not HF_AVAILABLE:
            logger.error("Hugging Face integration not available. Install with: pip install huggingface_hub")
            return []
        
        try:
            manager = HuggingFaceModelManager(api_token)
            return manager.search_models(query, limit)
        except Exception as e:
            logger.error(f"Failed to search Hugging Face models: {e}")
            return []
    
    def list_available_models(self, model_type: Optional[str] = None) -> None:
        """List available models in the specified type or all types."""
        if model_type:
            if model_type not in self.model_types:
                logger.error(f"Unknown model type: {model_type}")
                return
            
            self._list_models_in_type(model_type)
        else:
            print("Available model types and their contents:")
            print("=" * 50)
            for mt in self.model_types:
                if mt in ["configs", "custom_nodes"]:  # Skip these
                    continue
                print(f"\n{mt.upper()}:")
                self._list_models_in_type(mt)
    
    def _list_models_in_type(self, model_type: str) -> None:
        """List models in a specific type."""
        try:
            model_dir = self.get_model_directory(model_type)
            if not os.path.exists(model_dir):
                print(f"  Directory does not exist: {model_dir}")
                return
            
            files = []
            for file in os.listdir(model_dir):
                file_path = os.path.join(model_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    size_mb = size / (1024 * 1024)
                    files.append((file, size_mb))
            
            if not files:
                print(f"  No models found in {model_dir}")
                return
            
            # Sort by name
            files.sort(key=lambda x: x[0])
            
            for filename, size_mb in files:
                print(f"  {filename} ({size_mb:.1f} MB)")
                
        except Exception as e:
            logger.error(f"Error listing models in {model_type}: {e}")
    
    def get_model_info(self, model_type: str, filename: str) -> Optional[Dict]:
        """Get information about a specific model."""
        try:
            model_dir = self.get_model_directory(model_type)
            file_path = os.path.join(model_dir, filename)
            
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'filename': filename,
                'path': file_path,
                'size_bytes': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'modified': stat.st_mtime
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(
        description="ComfyUI Model Download CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available models
  python download_models.py list
  
  # List models of a specific type
  python download_models.py list --model-type checkpoints
  
  # Download from Hugging Face
  python download_models.py download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5
  
  # Download from URL
  python download_models.py download --model-type loras --source url --url https://example.com/model.safetensors
  
  # Download specific file from Hugging Face
  python download_models.py download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5 --filename v1-5-pruned-emaonly.safetensors
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available models')
    list_parser.add_argument('--model-type', choices=folder_paths.folder_names_and_paths.keys(),
                           help='Filter by model type')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download models')
    download_parser.add_argument('--model-type',
                               choices=folder_paths.folder_names_and_paths.keys(),
                               help='Type of model to download (auto-detected for Civitai URLs)')
    download_parser.add_argument('--source', required=True, choices=['huggingface', 'url', 'civitai'],
                               help='Source to download from')
    download_parser.add_argument('--repo', help='Hugging Face repository ID (for huggingface source)')
    download_parser.add_argument('--branch', help='Hugging Face branch (default: main)')
    download_parser.add_argument('--url', help='Direct URL to download from (for url source)')
    download_parser.add_argument('--model-id', type=int, help='Civitai model ID (for civitai source)')
    download_parser.add_argument('--version-id', type=int, help='Civitai version ID (for civitai source)')
    download_parser.add_argument('--civitai-url', help='Civitai URL (for civitai source) - automatically extracts model/version IDs')
    download_parser.add_argument('--huggingface-url', help='Hugging Face URL (for huggingface source) - automatically extracts repo info')
    download_parser.add_argument('--filename', help='Specific filename to download')
    download_parser.add_argument('--hash', help='Expected SHA-256 hash for verification')
    download_parser.add_argument('--api-key', help='API key for authentication (Civitai)')
    download_parser.add_argument('--hf-token', help='Hugging Face API token for authentication')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get information about a model')
    info_parser.add_argument('--model-type', required=True,
                           choices=folder_paths.folder_names_and_paths.keys(),
                           help='Type of model')
    info_parser.add_argument('--filename', required=True, help='Model filename')
    
    # Civitai search command
    if CIVITAI_AVAILABLE:
        civitai_parser = subparsers.add_parser('civitai', help='Civitai-specific commands')
        civitai_subparsers = civitai_parser.add_subparsers(dest='civitai_command', help='Civitai commands')
        
        # Search command
        search_parser = civitai_subparsers.add_parser('search', help='Search Civitai models')
        search_parser.add_argument('--query', required=True, help='Search query')
        search_parser.add_argument('--model-type', help='Filter by model type')
        search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
        search_parser.add_argument('--api-key', help='Civitai API key')
        
        # List types command
        types_parser = civitai_subparsers.add_parser('types', help='List Civitai model types')
    
    # Hugging Face commands
    if HF_AVAILABLE:
        hf_parser = subparsers.add_parser('huggingface', help='Hugging Face-specific commands')
        hf_subparsers = hf_parser.add_subparsers(dest='hf_command', help='Hugging Face commands')
        
        # Search command
        hf_search_parser = hf_subparsers.add_parser('search', help='Search Hugging Face models')
        hf_search_parser.add_argument('--query', required=True, help='Search query')
        hf_search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
        hf_search_parser.add_argument('--hf-token', help='Hugging Face API token')
        
        # List types command
        hf_types_parser = hf_subparsers.add_parser('types', help='List Hugging Face model type patterns')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    downloader = ModelDownloader()
    
    if args.command == 'list':
        downloader.list_available_models(args.model_type)
    
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
            success = downloader.download_from_url(args.url, args.model_type, args.filename)
        
        elif args.source == 'huggingface':
            if not args.repo and not args.huggingface_url:
                logger.error("Either --repo or --huggingface-url is required for huggingface source")
                return
            success = downloader.download_from_huggingface(args.repo, args.branch, args.hf_token, args.huggingface_url)
        
        elif args.source == 'civitai':
            if not args.model_id and not args.civitai_url:
                logger.error("Either --model-id or --civitai-url is required for civitai source")
                return
            success = downloader.download_from_civitai(args.model_id, args.version_id, args.filename, args.api_key, args.civitai_url)
        
        if success:
            logger.info("Download completed successfully!")
        else:
            logger.error("Download failed!")
            sys.exit(1)
    
    elif args.command == 'info':
        info = downloader.get_model_info(args.model_type, args.filename)
        if info:
            print(f"Model Information:")
            print(f"  Filename: {info['filename']}")
            print(f"  Path: {info['path']}")
            print(f"  Size: {info['size_mb']:.1f} MB")
            print(f"  Modified: {time.ctime(info['modified'])}")
        else:
            logger.error(f"Model not found: {args.filename}")
    
    elif args.command == 'civitai' and CIVITAI_AVAILABLE:
        if args.civitai_command == 'search':
            results = downloader.search_civitai_models(args.query, args.model_type, args.limit, args.api_key)
            if results:
                print(f"Found {len(results)} models on Civitai")
            else:
                print("No models found")
        
        elif args.civitai_command == 'types':
            if CIVITAI_AVAILABLE:
                manager = CivitaiModelManager()
                print("Civitai model type mappings:")
                for civitai_type, comfyui_type in manager.list_model_types().items():
                    print(f"  {civitai_type} -> {comfyui_type}")
            else:
                print("Civitai integration not available")
        
        else:
            civitai_parser.print_help()
    
    elif args.command == 'huggingface' and HF_AVAILABLE:
        if args.hf_command == 'search':
            results = downloader.search_huggingface_models(args.query, args.limit, args.hf_token)
            if results:
                print(f"Found {len(results)} models on Hugging Face")
                for model in results:
                    print(f"  {model['id']} - {model['downloads']} downloads, {model['likes']} likes")
                    print(f"    URL: {model['url']}")
                    if model['tags']:
                        print(f"    Tags: {', '.join(model['tags'][:5])}")
                    print()
            else:
                print("No models found")
        
        elif args.hf_command == 'types':
            if HF_AVAILABLE:
                manager = HuggingFaceModelManager()
                print("Hugging Face model type patterns:")
                for pattern, comfyui_type in manager.list_model_types().items():
                    print(f"  {pattern} -> {comfyui_type}")
            else:
                print("Hugging Face integration not available")
        
        else:
            hf_parser.print_help()
    
    elif args.command == 'civitai' and not CIVITAI_AVAILABLE:
        logger.error("Civitai integration not available. Install with: pip install requests")
    
    elif args.command == 'huggingface' and not HF_AVAILABLE:
        logger.error("Hugging Face integration not available. Install with: pip install huggingface_hub")

if __name__ == '__main__':
    main()
