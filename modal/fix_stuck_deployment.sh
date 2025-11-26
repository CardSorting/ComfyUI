#!/bin/bash
# Script to diagnose and fix stuck Modal deployments

set -e

echo "🔍 Modal Deployment Diagnostic Tool"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if modal CLI is installed
if ! command -v modal &> /dev/null; then
    echo -e "${RED}❌ Modal CLI not found. Please install it first.${NC}"
    exit 1
fi

echo "📋 Checking current app status..."
echo ""

# List all apps
modal app list

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for stuck apps
echo "🔍 Analyzing app status..."
echo ""

# Get app list and check for stuck initializing apps
STUCK_APPS=$(modal app list 2>/dev/null | grep "initializing" | wc -l | tr -d ' ')

if [ "$STUCK_APPS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $STUCK_APPS app(s) stuck in 'initializing' state${NC}"
    echo ""
    echo "📊 Recommended actions:"
    echo ""
    echo "1. ⭐ CHECK MODAL DASHBOARD (Most Important):"
    echo "   → Go to: https://modal.com/apps"
    echo "   → Find your 'comfyui-api' app"
    echo "   → View build logs to see what's happening"
    echo ""
    echo "2. If build has failed or is truly stuck:"
    echo "   → Stop the app via dashboard"
    echo "   → Or try: modal app stop comfyui-api"
    echo ""
    echo "3. Redeploy with monitoring:"
    echo "   → modal deploy modal/apps/modal_app_fastapi.py"
    echo "   → Immediately check dashboard: https://modal.com/apps"
    echo ""
else
    echo -e "${GREEN}✅ No stuck apps found${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Modal connection
echo "🔌 Testing Modal connection..."
if modal token validate &>/dev/null; then
    echo -e "${GREEN}✅ Modal connection OK${NC}"
else
    echo -e "${RED}❌ Modal connection failed. Check your token.${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Provide next steps
echo "📝 Next Steps:"
echo ""
echo "1. Open Modal Dashboard:"
echo "   https://modal.com/apps"
echo ""
echo "2. Find your app and check:"
echo "   - Build logs (see where it's stuck)"
echo "   - Error messages (if any)"
echo "   - Current status"
echo ""
echo "3. If stuck > 30 minutes:"
echo "   - Stop the app via dashboard"
echo "   - Redeploy: modal deploy modal/apps/modal_app_fastapi.py"
echo "   - Monitor in dashboard (don't wait for CLI)"
echo ""
echo "4. Expected timeline:"
echo "   - First deployment: 15-25 minutes"
echo "   - PyTorch install: 10-15 minutes (normal!)"
echo "   - Subsequent builds: 2-5 minutes (with caching)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tip: Always monitor deployments via dashboard - CLI may timeout but build continues!"
echo ""

