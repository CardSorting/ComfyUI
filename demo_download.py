#!/usr/bin/env python3
"""
Demo script showing how to use the ComfyUI Model Download CLI Tool
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and display the result."""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.returncode != 0:
            print(f"Command failed with return code: {result.returncode}")
    except Exception as e:
        print(f"Error running command: {e}")

def main():
    print("ComfyUI Model Download CLI Tool - Demo")
    print("This demo shows the basic functionality of the model download tool.")
    
    # Change to ComfyUI directory
    os.chdir('/home/user/Documents/ComfyUI')
    
    # Demo 1: List available models
    run_command("python3 download_models.py list", "List all available model types")
    
    # Demo 2: List specific model type
    run_command("python3 download_models.py list --model-type checkpoints", "List checkpoints models")
    
    # Demo 3: Show help
    run_command("python3 download_models.py download --help", "Show download command help")
    
    # Demo 4: Show wrapper script help
    run_command("./download_models.sh help", "Show wrapper script help")
    
    # Demo 5: Test advanced features (if available)
    if os.path.exists('download_models_advanced.py'):
        run_command("python3 download_models_advanced.py popular --model-type checkpoints", "Show popular checkpoint models")
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")
    print("\nTo actually download models, you would run commands like:")
    print("  ./download_models.sh download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5")
    print("  ./download_models.sh search \"stable diffusion\" --limit 5")
    print("  ./download_models.sh batch models_config.json")
    print("\nSee MODEL_DOWNLOAD_README.md for complete documentation.")

if __name__ == '__main__':
    main()
