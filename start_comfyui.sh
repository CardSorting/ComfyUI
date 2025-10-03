#!/bin/bash

# ComfyUI Startup Script with Environment Configuration
# This script loads environment variables and starts ComfyUI in headless mode

echo "🎯 Starting ComfyUI with environment configuration..."

# Change to ComfyUI directory
cd /home/user/Documents/ComfyUI

# Load environment variables from .env file
if [ -f .env ]; then
    echo "✅ Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  No .env file found, using defaults"
fi

# Set additional environment variables for headless mode to prevent broken pipe errors
export COMFYUI_HEADLESS=1
export DISABLE_PROGRESS_BARS=true
export DISABLE_AUTO_LAUNCH=true
export DONT_PRINT_SERVER=true
export PYTHONUNBUFFERED=1
export TQDM_DISABLE=1
export TQDM_DISABLE_PROGRESS_BAR=1
export TQDM_MINITERS=0
export TQDM_MAXITERS=0
export TQDM_POSITION=0
export TQDM_LEAVE=false
export TQDM_NCOLS=0
export TQDM_DESC=""
export TQDM_UNIT=""
export TQDM_UNIT_SCALE=false
export TQDM_RATE=0
export TQDM_POSTFIX=""
export TQDM_BAR_FORMAT=""
export TQDM_SMOOTHING=0
export TQDM_DYNAMIC_NCOLS=false
export TQDM_ASCII=true
export TQDM_DISABLE_TQDM=true

echo "🚀 Starting ComfyUI in headless mode..."
echo "📁 Working directory: $(pwd)"
echo "🌐 Host: ${COMFYUI_HOST:-0.0.0.0}"
echo "🔌 Port: ${COMFYUI_PORT:-8188}"

# Start ComfyUI with headless mode
python3 main.py \
    --headless \
    --listen ${COMFYUI_HOST:-0.0.0.0} \
    --port ${COMFYUI_PORT:-8188} \
    --dont-print-server \
    --disable-auto-launch
