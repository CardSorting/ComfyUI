#!/bin/bash
# Setup Civitai API Key and Download Animagine XL V3.1

set -e

echo "════════════════════════════════════════════════════════════"
echo "🎨 Animagine XL V3.1 Setup Script"
echo "════════════════════════════════════════════════════════════"
echo ""

# Step 1: Check if secret already exists
echo "📋 Step 1: Checking for existing Civitai secret..."
if modal secret list 2>/dev/null | grep -q "civitai-api-key"; then
    echo "   ✅ Secret 'civitai-api-key' already exists!"
else
    echo "   ⚠️  Secret 'civitai-api-key' not found."
    echo ""
    echo "   To create it, visit: https://civitai.com/user/account"
    echo "   Then run:"
    echo "   modal secret create civitai-api-key CIVITAI_API_KEY=YOUR_KEY_HERE"
    echo ""
    read -p "   Have you created the secret? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Please create the secret first, then run this script again."
        exit 1
    fi
fi

echo ""
echo "📦 Step 2: Deploying updated Modal app with Civitai support..."
modal deploy modal/apps/modal_app_fastapi.py

echo ""
echo "✅ Step 3: Downloading Animagine XL V3.1 (6.46 GB)..."
echo "   This will take several minutes..."
modal/scripts/modal_model_manager.sh download-url \
    "https://civitai.com/api/download/models/403131" \
    checkpoints \
    "animagineXLV31_v31.safetensors"

echo ""
echo "📥 Step 4: Downloading recommended VAE (319 MB)..."
# The VAE is in the files array on the same model version
modal/scripts/modal_model_manager.sh download-url \
    "https://civitai.com/api/download/models/403131?type=VAE" \
    vae \
    "sdxl_vae.safetensors"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Setup Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Your Animagine XL V3.1 model is ready to use!"
echo ""
echo "Recommended settings for Animagine XL V3.1:"
echo "  • Resolution: 1024x1024 (or other SDXL resolutions)"
echo "  • Steps: 20-30"
echo "  • CFG Scale: 5-7"
echo "  • Sampler: Euler Ancestral (euler_a)"
echo "  • Clip Skip: 2"
echo ""
echo "Prompt format: masterpiece, best quality, very aesthetic, absurdres, [your prompt]"
echo "Negative: nsfw, lowres, bad, text, error, fewer, extra, missing, worst quality"
echo ""

