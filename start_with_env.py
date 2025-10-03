#!/usr/bin/env python3
"""
ComfyUI Startup Script with Environment Configuration
This script loads environment variables from .env file and starts ComfyUI
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, continuing without .env support")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

# Set environment variables for headless mode to prevent broken pipe errors
env_vars = {
    'COMFYUI_HEADLESS': '1',
    'DISABLE_PROGRESS_BARS': 'true',
    'DISABLE_AUTO_LAUNCH': 'true', 
    'DONT_PRINT_SERVER': 'true',
    'PYTHONUNBUFFERED': '1',
    'TQDM_DISABLE': '1',
    'TQDM_DISABLE_PROGRESS_BAR': '1',
    'TQDM_MINITERS': '0',
    'TQDM_MAXITERS': '0',
    'TQDM_POSITION': '0',
    'TQDM_LEAVE': 'false',
    'TQDM_NCOLS': '0',
    'TQDM_DESC': '',
    'TQDM_UNIT': '',
    'TQDM_UNIT_SCALE': 'false',
    'TQDM_RATE': '0',
    'TQDM_POSTFIX': '',
    'TQDM_BAR_FORMAT': '',
    'TQDM_SMOOTHING': '0',
    'TQDM_DYNAMIC_NCOLS': 'false',
    'TQDM_ASCII': 'true',
    'TQDM_DISABLE_TQDM': '1'
}

# Apply environment variables
for key, value in env_vars.items():
    if key not in os.environ:
        os.environ[key] = value

print("🎯 Starting ComfyUI with environment configuration...")
print(f"📁 Working directory: {os.getcwd()}")
print(f"🌐 Host: {os.getenv('COMFYUI_HOST', '0.0.0.0')}")
print(f"🔌 Port: {os.getenv('COMFYUI_PORT', '8188')}")
print(f"🚫 Progress bars disabled: {os.getenv('DISABLE_PROGRESS_BARS', 'false')}")

# Import and run ComfyUI main
if __name__ == "__main__":
    try:
        import main
    except Exception as e:
        print(f"❌ Error starting ComfyUI: {e}")
        sys.exit(1)
