#!/bin/bash
# Backblaze B2 Setup Script for ComfyUI Modal

set -e

echo "🚀 Backblaze B2 Setup for ComfyUI Modal"
echo "========================================"
echo ""

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI not found. Please install it first:"
    echo "   pip install modal"
    exit 1
fi

echo "✅ Modal CLI found"
echo ""

# Check if user is logged in
if ! modal token verify &> /dev/null; then
    echo "⚠️  Not logged in to Modal. Logging in..."
    modal token new
fi

echo "✅ Modal authentication verified"
echo ""

# Get B2 credentials
echo "📝 Please enter your Backblaze B2 credentials"
echo "   (You can get these from https://www.backblaze.com/b2)"
echo ""

read -p "Enable Backblaze B2? (true/false) [true]: " USE_B2
USE_B2=${USE_B2:-true}

if [ "$USE_B2" == "true" ]; then
    read -p "B2 Endpoint (e.g., https://s3.us-east-005.backblazeb2.com): " B2_ENDPOINT
    read -p "B2 Region (e.g., us-east-005): " B2_REGION
    read -p "B2 Bucket Name: " B2_BUCKET
    read -p "B2 Key ID: " B2_KEY_ID
    read -s -p "B2 Application Key: " B2_APP_KEY
    echo ""
    read -p "B2 Public URL (e.g., https://f005.backblazeb2.com/file/your-bucket): " B2_PUBLIC_URL
    
    echo ""
    echo "📋 Configuration Summary:"
    echo "   Endpoint: $B2_ENDPOINT"
    echo "   Region: $B2_REGION"
    echo "   Bucket: $B2_BUCKET"
    echo "   Key ID: $B2_KEY_ID"
    echo "   Public URL: $B2_PUBLIC_URL"
    echo ""
    
    read -p "Create Modal secret with this configuration? (y/n): " CONFIRM
    
    if [ "$CONFIRM" == "y" ] || [ "$CONFIRM" == "Y" ]; then
        echo ""
        echo "📦 Creating Modal secret 'backblaze-b2-credentials'..."
        
        # Check if secret already exists
        if modal secret list | grep -q "backblaze-b2-credentials"; then
            echo "⚠️  Secret 'backblaze-b2-credentials' already exists"
            read -p "Delete and recreate? (y/n): " DELETE_CONFIRM
            
            if [ "$DELETE_CONFIRM" == "y" ] || [ "$DELETE_CONFIRM" == "Y" ]; then
                modal secret delete backblaze-b2-credentials
                echo "🗑️  Deleted existing secret"
            else
                echo "❌ Aborted. Please delete the secret manually or use a different name."
                exit 1
            fi
        fi
        
        # Create the secret
        modal secret create backblaze-b2-credentials \
            USE_BACKBLAZE_B2="$USE_B2" \
            B2_ENDPOINT="$B2_ENDPOINT" \
            B2_REGION="$B2_REGION" \
            B2_BUCKET="$B2_BUCKET" \
            B2_KEY_ID="$B2_KEY_ID" \
            B2_APP_KEY="$B2_APP_KEY" \
            B2_PUBLIC_URL="$B2_PUBLIC_URL"
        
        echo "✅ Modal secret created successfully!"
        echo ""
    else
        echo "❌ Aborted"
        exit 0
    fi
else
    echo "⚠️  B2 disabled. Creating secret with B2 disabled..."
    
    if modal secret list | grep -q "backblaze-b2-credentials"; then
        echo "⚠️  Secret 'backblaze-b2-credentials' already exists"
        read -p "Delete and recreate? (y/n): " DELETE_CONFIRM
        
        if [ "$DELETE_CONFIRM" == "y" ] || [ "$DELETE_CONFIRM" == "Y" ]; then
            modal secret delete backblaze-b2-credentials
            echo "🗑️  Deleted existing secret"
        else
            echo "❌ Aborted"
            exit 1
        fi
    fi
    
    modal secret create backblaze-b2-credentials \
        USE_BACKBLAZE_B2="false"
    
    echo "✅ Modal secret created (B2 disabled)"
    echo ""
fi

# Deploy the app
echo "🚀 Deploying ComfyUI Modal app..."
echo ""

read -p "Deploy now? (y/n): " DEPLOY_CONFIRM

if [ "$DEPLOY_CONFIRM" == "y" ] || [ "$DEPLOY_CONFIRM" == "Y" ]; then
    modal deploy modal_app_fastapi.py
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Get your endpoint URL:"
    echo "      modal app list"
    echo ""
    echo "   2. Test B2 status:"
    echo "      curl https://YOUR-WORKSPACE--comfyui-api-web.modal.run/b2/status"
    echo ""
    echo "   3. Update your backend with the endpoint URL"
    echo ""
    echo "   4. See BACKEND_INTEGRATION_GUIDE.md for backend integration"
    echo ""
else
    echo ""
    echo "⚠️  Skipped deployment. Deploy manually with:"
    echo "   modal deploy modal_app_fastapi.py"
    echo ""
fi

echo "📚 Documentation:"
echo "   - BACKBLAZE_B2_INTEGRATION.md - Complete technical guide"
echo "   - BACKEND_INTEGRATION_GUIDE.md - Backend integration"
echo "   - example_b2_client.py - Example Python client"
echo ""
echo "✅ Setup complete!"

