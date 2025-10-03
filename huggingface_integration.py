#!/usr/bin/env python3
"""
Hugging Face Hub integration for ComfyUI Model Download CLI.
Handles segmented/multi-part models and automatic type detection.
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
    from huggingface_hub import HfApi, hf_hub_download, list_repo_files, repo_info
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("Warning: Hugging Face Hub not available. Install with: pip install huggingface_hub")

logger = logging.getLogger(__name__)

class HuggingFaceURLParser:
    """Parser for Hugging Face URLs to extract repository information."""
    
    @staticmethod
    def parse_hf_url(url: str) -> Optional[Dict[str, Any]]:
        """Parse a Hugging Face URL and extract repository information."""
        try:
            # Remove any trailing slashes and normalize
            url = url.strip().rstrip('/')
            
            # Pattern for Hugging Face model URLs
            # https://huggingface.co/runwayml/stable-diffusion-v1-5
            # https://huggingface.co/runwayml/stable-diffusion-v1-5/tree/main
            # https://huggingface.co/runwayml/stable-diffusion-v1-5/blob/main/model_index.json
            hf_pattern = r'huggingface\.co/([^/]+)/([^/]+)(?:/(?:tree|blob)/([^/]+)(?:/(.+))?)?'
            
            match = re.search(hf_pattern, url)
            if match:
                namespace = match.group(1)
                repo_name = match.group(2)
                branch = match.group(3) or 'main'
                file_path = match.group(4)
                
                return {
                    'repo_id': f"{namespace}/{repo_name}",
                    'namespace': namespace,
                    'repo_name': repo_name,
                    'branch': branch,
                    'file_path': file_path,
                    'url_type': 'model'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse Hugging Face URL {url}: {e}")
            return None
    
    @staticmethod
    def is_huggingface_url(url: str) -> bool:
        """Check if a URL is a Hugging Face URL."""
        return 'huggingface.co' in url.lower()

class HuggingFaceModelManager:
    """Manages Hugging Face models and their organization in ComfyUI."""
    
    # Mapping of common Hugging Face model patterns to ComfyUI directories
    MODEL_TYPE_PATTERNS = {
        # Checkpoint patterns
        'stable-diffusion': 'checkpoints',
        'sd-': 'checkpoints',
        'diffusion': 'checkpoints',
        'checkpoint': 'checkpoints',
        'model': 'checkpoints',
        
        # LoRA patterns
        'lora': 'loras',
        'lora-': 'loras',
        'loras': 'loras',
        
        # VAE patterns
        'vae': 'vae',
        'autoencoder': 'vae',
        
        # ControlNet patterns
        'controlnet': 'controlnet',
        'control': 'controlnet',
        
        # Embedding patterns
        'embedding': 'embeddings',
        'textual-inversion': 'embeddings',
        'ti-': 'embeddings',
        
        # Upscaler patterns
        'upscaler': 'upscale_models',
        'upscale': 'upscale_models',
        'esrgan': 'upscale_models',
        'real-esrgan': 'upscale_models',
        
        # Hypernetwork patterns
        'hypernetwork': 'hypernetworks',
        'hyper': 'hypernetworks',
    }
    
    def __init__(self, api_token: Optional[str] = None):
        if not HF_AVAILABLE:
            raise ImportError("Hugging Face Hub not available. Install with: pip install huggingface_hub")
        
        self.api = HfApi(token=api_token)
        self.url_parser = HuggingFaceURLParser()
        self.supported_extensions = {'.ckpt', '.pt', '.pt2', '.bin', '.pth', '.safetensors', '.pkl', '.sft', '.yaml', '.json'}
    
    def detect_model_type(self, repo_id: str, repo_info: Optional[Dict] = None) -> str:
        """Detect the model type from repository information."""
        try:
            repo_name = repo_id.split('/')[-1].lower()
            
            # Check against known patterns
            for pattern, model_type in self.MODEL_TYPE_PATTERNS.items():
                if pattern in repo_name:
                    return model_type
            
            # If we have repo info, check tags and description
            if repo_info:
                tags = repo_info.get('tags', [])
                for tag in tags:
                    tag_lower = tag.lower()
                    for pattern, model_type in self.MODEL_TYPE_PATTERNS.items():
                        if pattern in tag_lower:
                            return model_type
                
                # Check model card content
                model_card = repo_info.get('cardData', {})
                if model_card:
                    # Look for type indicators in the model card
                    card_text = str(model_card).lower()
                    for pattern, model_type in self.MODEL_TYPE_PATTERNS.items():
                        if pattern in card_text:
                            return model_type
            
            # Default to checkpoints for main models
            return 'checkpoints'
            
        except Exception as e:
            logger.error(f"Failed to detect model type for {repo_id}: {e}")
            return 'checkpoints'
    
    def get_repo_info(self, repo_id: str) -> Optional[Dict]:
        """Get repository information from Hugging Face."""
        try:
            info = repo_info(repo_id)
            return {
                'id': info.id,
                'tags': info.tags,
                'cardData': info.card_data,
                'siblings': [sibling.rfilename for sibling in info.siblings],
                'lastModified': info.last_modified,
                'downloads': info.downloads,
                'likes': info.likes,
            }
        except Exception as e:
            logger.error(f"Failed to get repo info for {repo_id}: {e}")
            return None
    
    def list_repo_files(self, repo_id: str, branch: str = 'main') -> List[str]:
        """List all files in a repository."""
        try:
            files = list_repo_files(repo_id, revision=branch)
            return files
        except Exception as e:
            logger.error(f"Failed to list files for {repo_id}: {e}")
            return []
    
    def detect_segmented_models(self, files: List[str]) -> Dict[str, List[str]]:
        """Detect segmented model files (e.g., model-00001-of-00050.safetensors)."""
        segmented_models = {}
        
        # Pattern for segmented files: filename-00001-of-00050.extension
        segment_pattern = r'(.+)-(\d{5})-of-(\d{5})\.([^.]+)$'
        
        for file in files:
            match = re.match(segment_pattern, file)
            if match:
                base_name = match.group(1)
                segment_num = int(match.group(2))
                total_segments = int(match.group(3))
                extension = match.group(4)
                
                if base_name not in segmented_models:
                    segmented_models[base_name] = {
                        'total_segments': total_segments,
                        'extension': extension,
                        'files': []
                    }
                
                segmented_models[base_name]['files'].append({
                    'file': file,
                    'segment': segment_num,
                    'total': total_segments
                })
        
        # Sort files by segment number
        for base_name in segmented_models:
            segmented_models[base_name]['files'].sort(key=lambda x: x['segment'])
        
        return segmented_models
    
    def get_model_directory(self, model_type: str) -> str:
        """Get the ComfyUI directory for a model type."""
        try:
            return folder_paths.folder_names_and_paths[model_type][0][0]
        except KeyError:
            logger.warning(f"Unknown model type: {model_type}, using checkpoints")
            return folder_paths.folder_names_and_paths['checkpoints'][0][0]
    
    def get_file_destination_directory(self, filename: str, base_model_dir: str, repo_id: str) -> str:
        """Determine the appropriate directory for a specific file based on ComfyUI's expected structure."""
        filename_lower = filename.lower()
        repo_name = repo_id.split('/')[-1]
        
        logger.info(f"🔍 Analyzing file: {filename}")
        
        # Check if this is a VAE file (including directory paths)
        if any(pattern in filename_lower for pattern in ['vae', 'autoencoder']) or '/vae/' in filename_lower:
            vae_dir = self.get_model_directory('vae')
            destination = os.path.join(vae_dir, repo_name)
            logger.info(f"📁 VAE file detected: {filename} -> {destination}")
            return destination
        
        # Check if this is a LoRA file (including directory paths)
        if any(pattern in filename_lower for pattern in ['lora', 'loras']) or '/lora/' in filename_lower:
            lora_dir = self.get_model_directory('loras')
            destination = os.path.join(lora_dir, repo_name)
            logger.info(f"📁 LoRA file detected: {filename} -> {destination}")
            return destination
        
        # Check if this is a text encoder file (including directory paths)
        if any(pattern in filename_lower for pattern in ['text_encoder', 'text_encoders']) or '/text_encoder' in filename_lower:
            text_encoder_dir = self.get_model_directory('text_encoders')
            destination = os.path.join(text_encoder_dir, repo_name)
            logger.info(f"📁 Text encoder file detected: {filename} -> {destination}")
            return destination
        
        # Check if this is a UNet/diffusion model file (including directory paths)
        if any(pattern in filename_lower for pattern in ['unet', 'diffusion_pytorch_model']) or '/unet/' in filename_lower:
            unet_dir = self.get_model_directory('diffusion_models')
            destination = os.path.join(unet_dir, repo_name)
            logger.info(f"📁 UNet/diffusion model file detected: {filename} -> {destination}")
            return destination
        
        # Check if this is a config file
        if any(pattern in filename_lower for pattern in ['config', 'preprocessor', 'tokenizer', 'scheduler', 'model_index']):
            # Keep config files with the main model
            repo_dir = os.path.join(base_model_dir, repo_name)
            logger.info(f"📁 Config file detected: {filename} -> {repo_dir}")
            return repo_dir
        
        # For main model files, use the repository subdirectory
        repo_dir = os.path.join(base_model_dir, repo_name)
        logger.info(f"📁 Main model file detected: {filename} -> {repo_dir}")
        return repo_dir
    
    def is_main_model_file(self, filename: str) -> bool:
        """Check if this is a main model file (not a component)."""
        filename_lower = filename.lower()
        
        # Main model files are typically the largest .safetensors or .ckpt files
        # that don't contain component-specific keywords
        if not any(ext in filename_lower for ext in ['.safetensors', '.ckpt', '.pt', '.pth']):
            return False
        
        # Exclude component files
        component_patterns = ['vae', 'lora', 'text_encoder', 'unet', 'config', 'preprocessor', 'tokenizer', 'scheduler']
        if any(pattern in filename_lower for pattern in component_patterns):
            return False
        
        return True
    
    def download_file(self, repo_id: str, filename: str, destination: str, branch: str = 'main') -> bool:
        """Download a single file from Hugging Face."""
        try:
            logger.info(f"Downloading {filename} from {repo_id}...")
            
            # Create a temporary directory for the download
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download to temporary directory
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=temp_dir,
                    local_files_only=False,
                    revision=branch
                )
                
                # Move the file to the final destination
                if os.path.exists(downloaded_path):
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    
                    # Move the file
                    if os.path.exists(destination):
                        os.remove(destination)
                    os.rename(downloaded_path, destination)
                    return True
                else:
                    logger.error(f"Downloaded file not found: {downloaded_path}")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return False
    
    def download_segmented_model(self, repo_id: str, base_name: str, segments_info: Dict, 
                                destination_dir: str, branch: str = 'main') -> bool:
        """Download a segmented model (multiple files)."""
        try:
            total_segments = segments_info['total_segments']
            extension = segments_info['extension']
            files = segments_info['files']
            
            logger.info(f"Downloading segmented model {base_name} ({total_segments} parts)...")
            
            # Determine the appropriate directory for this segmented model
            repo_name = repo_id.split('/')[-1]
            segmented_destination_dir = self.get_file_destination_directory(base_name, destination_dir, repo_id)
            
            # Create destination directory
            os.makedirs(segmented_destination_dir, exist_ok=True)
            
            # Download all segments
            downloaded_files = []
            for file_info in files:
                filename = file_info['file']
                segment = file_info['segment']
                
                # Create destination path
                destination = os.path.join(segmented_destination_dir, filename)
                
                # Download the file
                if self.download_file(repo_id, filename, destination, branch):
                    downloaded_files.append(destination)
                    logger.info(f"Downloaded segment {segment}/{total_segments}: {filename}")
                else:
                    logger.error(f"Failed to download segment {segment}/{total_segments}: {filename}")
                    return False
            
            # Verify all segments were downloaded
            if len(downloaded_files) == total_segments:
                logger.info(f"Successfully downloaded all {total_segments} segments of {base_name}")
                return True
            else:
                logger.error(f"Only downloaded {len(downloaded_files)}/{total_segments} segments")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download segmented model {base_name}: {e}")
            return False
    
    def download_model(self, repo_id: str, branch: str = 'main', custom_dir: Optional[str] = None) -> bool:
        """Download a model from Hugging Face with automatic type detection."""
        try:
            # Get repository information
            repo_info = self.get_repo_info(repo_id)
            if not repo_info:
                logger.error(f"Could not get repository information for {repo_id}")
                return False
            
            # Detect model type
            model_type = self.detect_model_type(repo_id, repo_info)
            
            # Get destination directory
            if custom_dir:
                model_dir = custom_dir
            else:
                model_dir = self.get_model_directory(model_type)
            
            logger.info(f"🎯 Auto-detected model type: {model_type}")
            logger.info(f"📁 Download directory: {model_dir}")
            
            # List repository files
            files = self.list_repo_files(repo_id, branch)
            if not files:
                logger.error(f"No files found in repository {repo_id}")
                return False
            
            # Detect segmented models
            segmented_models = self.detect_segmented_models(files)
            
            if segmented_models:
                # Download segmented models
                success = True
                for base_name, segments_info in segmented_models.items():
                    if not self.download_segmented_model(repo_id, base_name, segments_info, model_dir, branch):
                        success = False
                return success
            else:
                # Download single model files
                model_files = [f for f in files if any(f.lower().endswith(ext) for ext in self.supported_extensions)]
                
                if not model_files:
                    logger.error(f"No model files found in repository {repo_id}")
                    return False
                
                # Prioritize main model files (larger files, not config files)
                main_model_files = []
                config_files = []
                
                for file in model_files:
                    file_lower = file.lower()
                    if any(pattern in file_lower for pattern in ['config', 'preprocessor', 'tokenizer', 'scheduler']):
                        config_files.append(file)
                    else:
                        main_model_files.append(file)
                
                # Organize files by type and download to appropriate directories
                success = True
                downloaded_main_model = False
                
                for model_file in model_files:
                    # Determine the appropriate directory for this file
                    file_destination_dir = self.get_file_destination_directory(model_file, model_dir, repo_id)
                    
                    # Create the destination path - use just the filename, not the full path
                    destination = os.path.join(file_destination_dir, os.path.basename(model_file))
                    
                    # Create directory if it doesn't exist
                    os.makedirs(file_destination_dir, exist_ok=True)
                    
                    if self.download_file(repo_id, model_file, destination, branch):
                        logger.info(f"✅ Successfully downloaded {model_file} to {destination}")
                        
                        # Save metadata for the first main model file
                        if not downloaded_main_model and self.is_main_model_file(model_file):
                            self.save_model_metadata(repo_id, repo_info, destination)
                            downloaded_main_model = True
                    else:
                        success = False
                        logger.error(f"Failed to download {model_file}")
                
                return success
                
        except Exception as e:
            logger.error(f"Failed to download model {repo_id}: {e}")
            return False
    
    def download_from_url(self, url: str, custom_dir: Optional[str] = None) -> bool:
        """Download a model from a Hugging Face URL with automatic type detection."""
        try:
            # Parse the URL
            url_info = self.url_parser.parse_hf_url(url)
            if not url_info:
                logger.error(f"Invalid Hugging Face URL: {url}")
                return False
            
            repo_id = url_info['repo_id']
            branch = url_info['branch']
            
            # Download the model
            return self.download_model(repo_id, branch, custom_dir)
            
        except Exception as e:
            logger.error(f"Failed to download from URL {url}: {e}")
            return False
    
    def save_model_metadata(self, repo_id: str, repo_info: Dict, destination: str) -> None:
        """Save model metadata to a JSON file."""
        try:
            metadata = {
                'repo_id': repo_id,
                'source': 'huggingface',
                'tags': repo_info.get('tags', []),
                'downloads': repo_info.get('downloads', 0),
                'likes': repo_info.get('likes', 0),
                'last_modified': str(repo_info.get('lastModified', '')),
                'downloaded_at': str(Path(destination).stat().st_mtime)
            }
            
            metadata_file = f"{destination}.huggingface.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def search_models(self, query: str, limit: int = 10, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for models on Hugging Face."""
        try:
            # Use the HfApi search functionality
            models = self.api.list_models(
                search=query,
                limit=limit,
                sort="downloads",
                direction=-1
            )
            
            results = []
            for model in models:
                results.append({
                    'id': model.id,
                    'name': model.id.split('/')[-1],
                    'namespace': model.id.split('/')[0],
                    'downloads': model.downloads,
                    'likes': model.likes,
                    'tags': model.tags,
                    'last_modified': model.last_modified,
                    'url': f"https://huggingface.co/{model.id}"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            return []
    
    def list_model_types(self) -> Dict[str, str]:
        """Returns a mapping of Hugging Face model patterns to ComfyUI folder names."""
        return self.MODEL_TYPE_PATTERNS.copy()
