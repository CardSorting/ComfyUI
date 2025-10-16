#!/bin/bash
#
# Simple endpoint tester - just checks if ComfyUI is responding
# Usage: ./test_endpoint_simple.sh <endpoint-url>
#

if [ -z "$1" ]; then
    echo "Usage: $0 <endpoint-url>"
    echo "Example: $0 https://workspace--comfyui-fastapi-app.modal.run"
    exit 1
fi

ENDPOINT="${1%/}"  # Remove trailing slash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        Quick ComfyUI Endpoint Test                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing: $ENDPOINT"
echo ""

# Test 1: Basic connectivity
echo "1️⃣  Testing basic connectivity..."
if curl -s -f -m 10 "$ENDPOINT" > /dev/null 2>&1 || \
   curl -s -m 10 "$ENDPOINT" 2>&1 | grep -q "HTTP"; then
    echo "   ✓ Server is reachable"
else
    echo "   ✗ Cannot reach server"
    echo ""
    echo "Troubleshooting:"
    echo "  • Check if URL is correct"
    echo "  • Check if deployment is running: modal app list"
    echo "  • Wait a minute if just deployed (cold start)"
    exit 1
fi

# Test 2: System stats
echo ""
echo "2️⃣  Testing /system_stats endpoint..."
if curl -s -f -m 30 "$ENDPOINT/system_stats" > /dev/null 2>&1; then
    echo "   ✓ API is responding"
    echo ""
    echo "   System info:"
    curl -s -m 30 "$ENDPOINT/system_stats" | python3 -m json.tool 2>/dev/null | head -20
else
    echo "   ✗ API not responding properly"
fi

# Test 3: Object info (check for nodes)
echo ""
echo "3️⃣  Checking available nodes..."
NODE_COUNT=$(curl -s -m 30 "$ENDPOINT/object_info" 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$NODE_COUNT" -gt "0" ]; then
    echo "   ✓ Found $NODE_COUNT node types available"
else
    echo "   ⚠ Could not get node information"
fi

# Test 4: Queue
echo ""
echo "4️⃣  Checking queue system..."
if curl -s -f -m 30 "$ENDPOINT/queue" > /dev/null 2>&1; then
    echo "   ✓ Queue is accessible"
else
    echo "   ✗ Queue not accessible"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Test Complete                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ Your ComfyUI endpoint appears to be working!"
echo ""
echo "Next steps:"
echo "  • Add models: modal volume put comfyui-models model.safetensors /checkpoints/model.safetensors"
echo "  • Run full test: python modal_test_endpoints.py $ENDPOINT"
echo "  • Submit workflows to: $ENDPOINT/prompt"
echo ""

