#!/bin/bash
# Force redeploy script - cleans up and redeploys

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Force Redeploy ComfyUI${NC}"
echo "=========================================="
echo ""

# Check Modal CLI
if ! command -v modal &> /dev/null; then
    echo -e "${RED}❌ Modal CLI not found${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Current app status:${NC}"
modal app list | grep "comfyui-api" || echo "No comfyui-api apps found"
echo ""

echo -e "${YELLOW}⚠️  Note:${NC}"
echo "   - Stopped apps don't block new deployments"
echo "   - You can deploy now, or clean up old apps first"
echo "   - Old apps will auto-cleanup after some time"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}🚀 Deploying comfyui-api...${NC}"
echo "   Monitor at: https://modal.com/apps"
echo ""

# Deploy
modal deploy modal/apps/modal_app_fastapi.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Deployment initiated!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Check dashboard: https://modal.com/apps"
    echo "  2. Monitor build progress"
    echo "  3. Wait for 'running' status (~15-20 min first time)"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  Deployment may have timed out${NC}"
    echo "   This is normal - build continues on Modal servers"
    echo "   Check dashboard: https://modal.com/apps"
    echo ""
fi

