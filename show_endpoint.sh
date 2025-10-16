#!/bin/bash
#
# Show your ComfyUI Modal endpoint URL
# This script finds and displays your deployed endpoint
#

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        Finding Your ComfyUI Endpoint URL                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI not found"
    echo ""
    echo "Install it with: pip install modal"
    exit 1
fi

# Check if authenticated (try a simple command that requires auth)
if ! modal app list &> /dev/null 2>&1; then
    echo "❌ Could not connect to Modal"
    echo ""
    echo "This might mean:"
    echo "  • You're not authenticated (run: modal setup)"
    echo "  • Modal is having issues"
    echo ""
    echo "Try running: modal app list"
    echo ""
    echo "If that works, try this script again."
    exit 1
fi

# Get app info
echo "🔍 Checking Modal deployment..."
echo ""

# Check if app exists in list
if modal app list 2>/dev/null | grep -q "comfyui"; then
    echo "✓ Found deployment: comfyui"
    echo ""
    
    # For Modal 1.x, endpoint URL format is:
    # https://{workspace}--{app-name}-{function-name}.modal.run
    echo "📋 Deployment Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    modal app list | grep -A 1 comfyui
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "📍 FINDING YOUR ENDPOINT URL:"
    echo ""
    echo "Your endpoint URL format is:"
    echo "   https://{workspace}--comfyui-fastapi-app.modal.run"
    echo ""
    echo "Where {workspace} is your Modal workspace name."
    echo ""
    
    # Try to get it from deployment logs or output
    echo "🔍 Trying to find your endpoint..."
    echo ""
    
    # Check if there's a cached endpoint
    if [ -f ".modal_endpoint_cache.json" ]; then
        CACHED_ENDPOINT=$(python3 -c "import json; print(json.load(open('.modal_endpoint_cache.json'))['endpoint'])" 2>/dev/null)
        if [ -n "$CACHED_ENDPOINT" ]; then
            echo "✓ Found cached endpoint from previous deployment:"
            echo ""
            echo "   $CACHED_ENDPOINT"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "💡 To verify this is correct, test it:"
            echo "   curl $CACHED_ENDPOINT/system_stats"
            echo ""
            echo "📝 Quick test commands:"
            echo "   ./test_endpoint_simple.sh $CACHED_ENDPOINT"
            echo "   python modal_test_endpoints.py $CACHED_ENDPOINT"
        fi
    else
        echo "⚠️  No cached endpoint found."
        echo ""
        echo "To find your endpoint URL:"
        echo ""
        echo "  Option 1: Check deployment output"
        echo "    When you ran: modal deploy modal_app.py"
        echo "    It showed: Web endpoint: https://..."
        echo ""
        echo "  Option 2: Use Python tester (auto-detects)"
        echo "    Run: python modal_test_endpoints.py"
        echo ""
        echo "  Option 3: Redeploy to see the URL"
        echo "    Run: modal deploy modal_app.py"
        echo "    (Zero-downtime, safe to run)"
    fi
else
    echo "❌ ComfyUI app not found"
    echo ""
    echo "Have you deployed yet?"
    echo "   Run: modal deploy modal_app.py"
    echo ""
    echo "Or check your deployments:"
    echo "   Run: modal app list"
fi

echo ""
echo "╚══════════════════════════════════════════════════════════════╝"

