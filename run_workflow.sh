#!/bin/bash
# Quick workflow runner for Modal ComfyUI

ENDPOINT="https://cardsorting--comfyui-api-web.modal.run"
WORKFLOW_FILE="${1:-test_workflow_sdxl_turbo.json}"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Workflow file not found: $WORKFLOW_FILE"
    echo "Usage: $0 [workflow.json]"
    exit 1
fi

echo "🚀 Running workflow: $WORKFLOW_FILE"
echo "   Endpoint: $ENDPOINT"
echo

# Wrap workflow in proper format
WRAPPED=$(python3 -c "import json; w=json.load(open('$WORKFLOW_FILE')); print(json.dumps({'prompt': w}))")

# Submit workflow
echo "📤 Submitting..."
RESPONSE=$(curl -s -X POST "$ENDPOINT/prompt" \
    -H "Content-Type: application/json" \
    -d "$WRAPPED")

# Parse response
PROMPT_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('prompt_id', 'none'))" 2>/dev/null)

if [ "$PROMPT_ID" = "none" ]; then
    echo "❌ Failed to submit:"
    echo "$RESPONSE" | python3 -m json.tool
    exit 1
fi

echo "✅ Queued! Prompt ID: $PROMPT_ID"
echo

# Monitor execution
echo "⏳ Monitoring execution..."
for i in {1..60}; do
    sleep 2
    
    # Check if completed
    HISTORY=$(curl -s "$ENDPOINT/history/$PROMPT_ID")
    COMPLETED=$(echo "$HISTORY" | python3 -c "import sys, json; h=json.load(sys.stdin); print(h.get('$PROMPT_ID', {}).get('status', {}).get('completed', False))" 2>/dev/null)
    
    if [ "$COMPLETED" = "True" ]; then
        echo -e "\n✅ Execution completed!"
        
        # Get outputs
        OUTPUTS=$(echo "$HISTORY" | python3 -c "import sys, json; h=json.load(sys.stdin); print(json.dumps(h.get('$PROMPT_ID', {}).get('outputs', {})))" 2>/dev/null)
        echo "📁 Outputs: $OUTPUTS"
        
        # Extract image filename
        IMAGE=$(echo "$OUTPUTS" | python3 -c "import sys, json; o=json.load(sys.stdin); print(list(o.values())[0]['images'][0]['filename'])" 2>/dev/null)
        
        if [ -n "$IMAGE" ]; then
            echo
            echo "📸 Downloading image: $IMAGE"
            curl -s "$ENDPOINT/outputs/$IMAGE" -o "$IMAGE"
            ls -lh "$IMAGE"
            echo
            echo "✅ Image saved as: $IMAGE"
            echo "   Open it to view your generated image!"
        fi
        
        exit 0
    fi
    
    echo -n "."
done

echo -e "\n⚠️  Timeout - check status manually:"
echo "   curl $ENDPOINT/history/$PROMPT_ID"

