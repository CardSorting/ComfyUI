#!/bin/bash
# Interactive script to set up Modal secrets for ComfyUI

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Modal Secrets Setup for ComfyUI${NC}"
echo "=========================================="
echo ""

# Check if modal CLI is installed
if ! command -v modal &> /dev/null; then
    echo -e "${RED}❌ Modal CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check existing secrets
echo -e "${YELLOW}📋 Checking existing secrets...${NC}"
B2_EXISTS=$(modal secret list 2>/dev/null | grep "backblaze-b2-credentials" | wc -l | tr -d ' ')
CIVITAI_EXISTS=$(modal secret list 2>/dev/null | grep "civitai-api-key" | wc -l | tr -d ' ')

if [ "$B2_EXISTS" -gt 0 ]; then
    echo -e "${GREEN}✅ Backblaze B2 secret already exists${NC}"
    read -p "Update it? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        SKIP_B2=true
    fi
fi

if [ "$CIVITAI_EXISTS" -gt 0 ]; then
    echo -e "${GREEN}✅ Civitai API key secret already exists${NC}"
    read -p "Update it? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        SKIP_CIVITAI=true
    fi
fi

echo ""

# Setup Backblaze B2 Secret
if [ "$SKIP_B2" != "true" ]; then
    echo -e "${BLUE}📦 Setting up Backblaze B2 Secret${NC}"
    echo "----------------------------------------"
    echo ""
    echo "This secret enables automatic uploads of generated images to Backblaze B2."
    echo ""
    read -p "Do you want to set up B2 storage? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "You'll need the following from your Backblaze B2 account:"
        echo "  - Endpoint URL (e.g., https://s3.us-east-005.backblazeb2.com)"
        echo "  - Region (e.g., us-east-005)"
        echo "  - Bucket name"
        echo "  - Application Key ID"
        echo "  - Application Key (secret)"
        echo "  - Public URL (e.g., https://f005.backblazeb2.com/file/your-bucket)"
        echo ""
        read -p "Press Enter when ready to continue..."
        echo ""
        
        read -p "B2 Endpoint (e.g., https://s3.us-east-005.backblazeb2.com): " B2_ENDPOINT
        read -p "B2 Region (e.g., us-east-005): " B2_REGION
        read -p "B2 Bucket Name: " B2_BUCKET
        read -p "B2 Key ID: " B2_KEY_ID
        read -sp "B2 Application Key (hidden): " B2_APP_KEY
        echo ""
        read -p "B2 Public URL (e.g., https://f005.backblazeb2.com/file/your-bucket): " B2_PUBLIC_URL
        
        echo ""
        echo -e "${YELLOW}Creating Backblaze B2 secret...${NC}"
        
        if [ "$B2_EXISTS" -gt 0 ]; then
            # Update existing secret
            modal secret delete backblaze-b2-credentials 2>/dev/null || true
        fi
        
        modal secret create backblaze-b2-credentials \
            USE_BACKBLAZE_B2=true \
            B2_ENDPOINT="$B2_ENDPOINT" \
            B2_REGION="$B2_REGION" \
            B2_BUCKET="$B2_BUCKET" \
            B2_KEY_ID="$B2_KEY_ID" \
            B2_APP_KEY="$B2_APP_KEY" \
            B2_PUBLIC_URL="$B2_PUBLIC_URL"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Backblaze B2 secret created successfully!${NC}"
        else
            echo -e "${RED}❌ Failed to create B2 secret${NC}"
        fi
    else
        echo "Skipping B2 setup."
    fi
    echo ""
fi

# Setup Civitai Secret
if [ "$SKIP_CIVITAI" != "true" ]; then
    echo -e "${BLUE}🎨 Setting up Civitai API Key Secret${NC}"
    echo "----------------------------------------"
    echo ""
    echo "This secret enables downloading models from Civitai (especially private models)."
    echo ""
    read -p "Do you want to set up Civitai API key? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Get your API key from: https://civitai.com/settings/api-keys"
        echo ""
        read -sp "Civitai API Key (hidden): " CIVITAI_API_KEY
        echo ""
        
        if [ -z "$CIVITAI_API_KEY" ]; then
            echo -e "${YELLOW}⚠️  Empty API key, skipping...${NC}"
        else
            echo ""
            echo -e "${YELLOW}Creating Civitai API key secret...${NC}"
            
            if [ "$CIVITAI_EXISTS" -gt 0 ]; then
                # Update existing secret
                modal secret delete civitai-api-key 2>/dev/null || true
            fi
            
            modal secret create civitai-api-key \
                CIVITAI_API_KEY="$CIVITAI_API_KEY"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Civitai API key secret created successfully!${NC}"
            else
                echo -e "${RED}❌ Failed to create Civitai secret${NC}"
            fi
        fi
    else
        echo "Skipping Civitai setup."
    fi
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📋 Summary${NC}"
echo ""

modal secret list 2>/dev/null | grep -E "(backblaze-b2-credentials|civitai-api-key)" || echo "No secrets found"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Redeploy your app: modal deploy modal/apps/modal_app_fastapi.py"
echo "  2. Check logs: modal app logs comfyui-api"
echo "  3. Verify secrets are loaded in the logs"
echo ""

