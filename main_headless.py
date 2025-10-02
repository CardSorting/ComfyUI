#!/usr/bin/env python3
"""
ComfyUI Headless Startup Script

This script starts ComfyUI in headless mode, optimized for serverless environments.
It disables the web UI and only provides API endpoints for programmatic access.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set headless mode before importing ComfyUI modules
os.environ['COMFYUI_HEADLESS'] = '1'

# Import and run ComfyUI
if __name__ == "__main__":
    # Import main ComfyUI module
    import main
    
    # The main module will automatically detect headless mode from the environment
    # and CLI arguments, so we can just run it normally
    print("Starting ComfyUI in headless mode...")
    print("Use --help to see available options")
    print("API endpoints will be available at http://localhost:8188/api/")
