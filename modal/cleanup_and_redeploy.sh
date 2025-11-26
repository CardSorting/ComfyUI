#!/bin/bash
# Cleanup old stopped apps and redeploy

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Cleanup and Redeploy ComfyUI${NC}"
echo "=========================================="
echo ""

# Check Modal CLI
if ! command -v modal &> /dev/null; then
    echo -e "${RED}❌ Modal CLI not found${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Current app status:${NC}"
echo ""
modal app list | grep -E "(comfyui-api|comfyui-base)" | head -10
echo ""

echo -e "${YELLOW}ℹ️  Note:${NC}"
echo "   - Stopped apps don't block new deployments"
echo "   - They will auto-cleanup after some time"
echo "   - You can deploy now without cleaning up"
echo ""

# Ask about cleanup
read -p "Do you want to see deployment logs from recent stopped apps? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}📊 Recent app IDs (for dashboard inspection):${NC}"
    modal app list | grep "comfyui-api" | head -3 | awk '{print "   App ID: " $1 " - Status: " $3}'
    echo ""
    echo "   View in dashboard: https://modal.com/apps"
    echo "   Click on any app to see build logs and errors"
    echo ""
fi

echo ""
echo -e "${BLUE}🚀 Ready to deploy${NC}"
echo ""
echo "The code has been fixed to avoid recursive loops."
echo "This deployment should work successfully."
echo ""
read -p "Deploy now? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}🚀 Deploying comfyui-api...${NC}"
echo "   This will take ~15-20 minutes (first time)"
echo "   Monitor at: https://modal.com/apps"
echo ""
echo "   ⚠️  CLI may timeout - this is normal!"
echo "   Build continues on Modal servers even if CLI disconnects"
echo ""

# Deploy
modal deploy modal/apps/modal_app_fastapi.py

DEPLOY_EXIT_CODE=$?

echo ""
if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment command completed!${NC}"
else
    echo -e "${YELLOW}⚠️  Deployment command exited with code $DEPLOY_EXIT_CODE${NC}"
    echo "   This might be a timeout (normal for long builds)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📊 Next Steps:${NC}"
echo ""
echo "1. ⭐ CHECK MODAL DASHBOARD (Most Important):"
echo "   → https://modal.com/apps"
echo "   → Find the newest 'comfyui-api' app"
echo "   → View build logs to see progress"
echo ""
echo "2. Monitor build progress:"
echo "   → PyTorch installation: ~10-15 minutes"
echo "   → Other dependencies: ~2-3 minutes"
echo "   → Total: ~15-20 minutes"
echo ""
echo "3. Check status:"
echo "   → modal app list"
echo "   → Look for 'running' status"
echo ""
echo "4. If build fails:"
echo "   → Check dashboard logs for errors"
echo "   → Common issues: GPU quota, network timeout, missing dependencies"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

