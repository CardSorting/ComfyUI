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

if modal app show comfyui &> /dev/null; then
    echo "✓ Found deployment: comfyui"
    echo ""
    echo "📋 Deployment Information:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show app info
    modal app show comfyui
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📍 YOUR ENDPOINT URL:"
    echo ""
    
    # Try to extract the endpoint URL
    ENDPOINT=$(modal app show comfyui 2>/dev/null | grep -o 'https://[^[:space:]]*\.modal\.run[^[:space:]]*' | head -1)
    
    if [ -n "$ENDPOINT" ]; then
        echo "   $ENDPOINT"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "💡 Save this URL! You'll need it to use your ComfyUI API."
        echo ""
        echo "📝 Quick Commands:"
        echo "   Test it:     ./test_endpoint_simple.sh $ENDPOINT"
        echo "   Full test:   python modal_test_endpoints.py $ENDPOINT"
        echo "   Check stats: curl $ENDPOINT/system_stats"
        
        # Save to cache
        echo "{\"endpoint\": \"$ENDPOINT\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S)\"}" > .modal_endpoint_cache.json
        echo ""
        echo "✓ Endpoint cached for future use"
    else
        echo "   ⚠️  Could not auto-extract endpoint URL"
        echo "   Look for the 'web_url' or URL in the output above"
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

