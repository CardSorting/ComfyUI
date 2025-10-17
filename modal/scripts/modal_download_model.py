#!/usr/bin/env python3
"""
ComfyUI Modal Model Downloader
Convenient CLI tool to download and manage models in your Modal persistent volume
"""

import sys
import argparse
from modal import App

def download_model_cli(url: str, category: str = "checkpoints", filename: str = None):
    """Download a model via Modal"""
    print(f"🚀 Starting download via Modal...")
    print(f"   URL: {url}")
    print(f"   Category: {category}")
    if filename:
        print(f"   Filename: {filename}")
    print()
    
    # Import the Modal app and function
    import sys
    sys.path.insert(0, '/Users/bozoegg/ComfyUI')
    from modal.apps.modal_app_fastapi import download_model
    result = download_model.remote(url, category, filename)
    
    print()
    if result["status"] == "success":
        print("✅ Download complete!")
        print(f"   Path: {result['path']}")
        print(f"   Size: {result['size'] / 1024 / 1024:.1f} MB")
    elif result["status"] == "skipped":
        print("⚠️  File already exists, skipped")
    
    return result

def list_models_cli():
    """List all models via Modal"""
    print("📦 Fetching model list from Modal...")
    print()
    
    import sys
    sys.path.insert(0, '/Users/bozoegg/ComfyUI')
    from modal.apps.modal_app_fastapi import list_models
    result = list_models.remote()
    
    print()
    print(f"Summary: {result['total_files']} files, {result['total_size_gb']:.2f} GB total")
    
    return result

def delete_model_cli(category: str, filename: str):
    """Delete a model via Modal"""
    print(f"🗑️  Deleting model from Modal...")
    print(f"   Category: {category}")
    print(f"   Filename: {filename}")
    print()
    
    import sys
    sys.path.insert(0, '/Users/bozoegg/ComfyUI')
    from modal.apps.modal_app_fastapi import delete_model
    result = delete_model.remote(category, filename)
    
    if result["status"] == "deleted":
        print("✅ Model deleted successfully!")
    elif result["status"] == "not_found":
        print("❌ Model not found")
    
    return result

def main():
    parser = argparse.ArgumentParser(
        description="Download and manage ComfyUI models in Modal persistent volume",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a checkpoint
  %(prog)s download "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"
  
  # Download a LoRA
  %(prog)s download "https://civitai.com/api/download/models/123456" --category loras --filename "my_lora.safetensors"
  
  # Download a VAE
  %(prog)s download "https://example.com/vae.safetensors" --category vae
  
  # List all models
  %(prog)s list
  
  # Delete a model
  %(prog)s delete checkpoints sd_xl_base_1.0.safetensors

Common Model Categories:
  - checkpoints (SD models, SDXL, etc.)
  - vae (VAE models)
  - loras (LoRA models)
  - controlnet (ControlNet models)
  - clip_vision (CLIP vision models)
  - upscale_models (Upscaler models)
  - embeddings (Textual inversions)
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download a model")
    download_parser.add_argument("url", help="Direct download URL for the model")
    download_parser.add_argument(
        "--category", "-c",
        default="checkpoints",
        help="Model category (default: checkpoints)"
    )
    download_parser.add_argument(
        "--filename", "-f",
        help="Custom filename (optional, auto-detected from URL if not provided)"
    )
    
    # List command
    subparsers.add_parser("list", help="List all models in the volume")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a model")
    delete_parser.add_argument("category", help="Model category")
    delete_parser.add_argument("filename", help="Model filename to delete")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "download":
            download_model_cli(args.url, args.category, args.filename)
        elif args.command == "list":
            list_models_cli()
        elif args.command == "delete":
            delete_model_cli(args.category, args.filename)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

