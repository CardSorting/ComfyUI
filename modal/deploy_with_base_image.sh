#!/bin/bash
# Automated deployment script that handles base image setup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ComfyUI Modal Deployment (Optimized)${NC}"
echo "=========================================="
echo ""

# Check if base image exists
echo -e "${YELLOW}📋 Checking for base image...${NC}"
BASE_IMAGE_EXISTS=$(modal app list 2>/dev/null | grep "comfyui-base-image" | grep -v "stopped" | wc -l | tr -d ' ')

if [ "$BASE_IMAGE_EXISTS" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Base image not found${NC}"
    echo ""
    echo "Building base image with PyTorch (one-time, ~15-20 minutes)..."
    echo "This will be cached and reused for future deployments."
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}📦 Deploying base image...${NC}"
    echo "   This will take ~15-20 minutes. Monitor progress at:"
    echo "   https://modal.com/apps"
    echo ""
    
    modal deploy modal/apps/base_image.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Base image deployed successfully!${NC}"
        echo ""
    else
        echo ""
        echo -e "${YELLOW}⚠️  Base image deployment may have timed out${NC}"
        echo "   Check dashboard: https://modal.com/apps"
        echo "   Build continues on Modal servers even if CLI times out"
        echo ""
        read -p "Wait for base image to finish, then press Enter to continue..."
    fi
else
    echo -e "${GREEN}✅ Base image found - using cached version${NC}"
    echo "   Fast deployment (~2-5 minutes)"
    echo ""
fi

# Deploy main app
echo -e "${BLUE}🚀 Deploying main ComfyUI app...${NC}"
echo "   Using cached base image (fast!)"
echo "   Monitor at: https://modal.com/apps"
echo ""

modal deploy modal/apps/modal_app_fastapi.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Deployment complete!${NC}"
    echo ""
    echo "Check your endpoint:"
    echo "  modal app list"
    echo ""
    echo "Or visit: https://modal.com/apps"
else
    echo ""
    echo -e "${YELLOW}⚠️  Deployment may have timed out${NC}"
    echo "   Check dashboard: https://modal.com/apps"
    echo "   Build continues on Modal servers"
    echo ""
fi

