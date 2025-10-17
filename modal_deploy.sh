#!/bin/bash
# Quick deployment wrapper for Modal ComfyUI app

cd "$(dirname "$0")"

echo "🚀 Deploying ComfyUI to Modal..."
modal deploy modal/apps/modal_app_fastapi.py

