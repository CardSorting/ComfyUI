#!/bin/bash
# Deprecated: Use ./modal_deploy.sh instead
echo "⚠️  This script is deprecated. Please use ./modal_deploy.sh instead"
echo "Redirecting to new script..."
echo
./modal_deploy.sh
exit $?

# ComfyUI Modal Deployment Script
# This script helps you deploy ComfyUI to Modal.com

set -e

echo "🚀 ComfyUI Modal Deployment Helper"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo -e "${YELLOW}Modal CLI not found. Installing...${NC}"
    pip install modal
fi

# Check if modal is authenticated
if ! modal token show &> /dev/null; then
    echo -e "${YELLOW}Modal not authenticated. Running setup...${NC}"
    modal setup
fi

# Show menu
echo "What would you like to do?"
echo ""
echo "1) Deploy ComfyUI to Modal"
echo "2) Test deployment locally (on Modal)"
echo "3) Download models to volume"
echo "4) List volumes"
echo "5) Upload model from local file"
echo "6) View deployment logs"
echo "7) Stop deployment"
echo "8) Check deployment status"
echo "9) Exit"
echo ""

read -p "Enter choice [1-9]: " choice

case $choice in
    1)
        echo -e "${GREEN}Deploying ComfyUI to Modal...${NC}"
        modal deploy modal_app.py
        echo ""
        echo -e "${GREEN}✅ Deployment complete!${NC}"
        echo ""
        echo "Your API endpoint will be shown above."
        echo "Save it for accessing your ComfyUI instance."
        ;;
    2)
        echo -e "${GREEN}Testing deployment locally on Modal...${NC}"
        modal run modal_app.py
        ;;
    3)
        echo -e "${GREEN}Running model download function...${NC}"
        echo ""
        echo -e "${YELLOW}Note: Edit modal_app.py to add your model URLs first${NC}"
        modal run modal_app.py::download_models
        ;;
    4)
        echo -e "${GREEN}Listing volumes...${NC}"
        echo ""
        modal volume list
        echo ""
        echo "To see contents of a volume:"
        echo "  modal volume ls comfyui-models"
        echo "  modal volume ls comfyui-models /checkpoints"
        ;;
    5)
        read -p "Enter local file path: " local_file
        read -p "Enter remote path (e.g., /checkpoints/model.safetensors): " remote_path
        echo -e "${GREEN}Uploading $local_file to comfyui-models:$remote_path${NC}"
        modal volume put comfyui-models "$local_file" "$remote_path"
        echo -e "${GREEN}✅ Upload complete!${NC}"
        ;;
    6)
        echo -e "${GREEN}Showing deployment logs...${NC}"
        modal app logs comfyui --follow
        ;;
    7)
        echo -e "${RED}WARNING: Stopping deployment is irreversible!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            modal app stop comfyui
            echo -e "${GREEN}✅ Deployment stopped${NC}"
        else
            echo "Cancelled"
        fi
        ;;
    8)
        echo -e "${GREEN}Checking deployment status...${NC}"
        echo ""
        modal app list
        echo ""
        modal app show comfyui 2>/dev/null || echo "App 'comfyui' not found. Deploy first with option 1."
        ;;
    9)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"

