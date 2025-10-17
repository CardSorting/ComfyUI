#!/bin/bash
# Modal Model Manager - Simple wrapper to manage models on Modal
# This runs your existing download tools inside the Modal container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function print_usage() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════════════${NC}
${GREEN}Modal Model Manager${NC}
${BLUE}═══════════════════════════════════════════════════════════════════${NC}

This tool manages models in your Modal persistent volume.

${YELLOW}Usage:${NC}
    $0 <command> [options]

${YELLOW}Commands:${NC}
    list                  List all models in Modal volume
    download-url          Download from a direct URL
    download-hf           Download from Hugging Face
    download-civitai      Download from CivitAI
    download-batch        Batch download from config file
    delete                Delete a model

${YELLOW}Examples:${NC}

  # List all models
  $0 list

  # Download from URL
  $0 download-url "https://huggingface.co/.../model.safetensors" checkpoints

  # Download from Hugging Face
  $0 download-hf "runwayml/stable-diffusion-v1-5" "v1-5-pruned-emaonly.safetensors" checkpoints

  # Download from CivitAI using your config
  $0 download-batch

  # Delete a model
  $0 delete checkpoints model.safetensors

${BLUE}═══════════════════════════════════════════════════════════════════${NC}
EOF
}

function run_list() {
    echo -e "${BLUE}📦 Listing models in Modal volume...${NC}"
    echo
    modal run modal/apps/modal_app_fastapi.py::list_models
}

function run_download_url() {
    local url="$1"
    local category="${2:-checkpoints}"
    local filename="${3:-}"
    
    if [ -z "$url" ]; then
        echo -e "${RED}Error: URL required${NC}"
        echo "Usage: $0 download-url <url> [category] [filename]"
        exit 1
    fi
    
    echo -e "${BLUE}📥 Downloading from URL via Modal...${NC}"
    echo -e "   URL: ${url}"
    echo -e "   Category: ${category}"
    [ -n "$filename" ] && echo -e "   Filename: ${filename}"
    echo
    
    if [ -n "$filename" ]; then
        modal run modal/apps/modal_app_fastapi.py::download_model --url "$url" --category "$category" --filename "$filename"
    else
        modal run modal/apps/modal_app_fastapi.py::download_model --url "$url" --category "$category"
    fi
}

function run_delete() {
    local category="$1"
    local filename="$2"
    
    if [ -z "$category" ] || [ -z "$filename" ]; then
        echo -e "${RED}Error: Category and filename required${NC}"
        echo "Usage: $0 delete <category> <filename>"
        exit 1
    fi
    
    echo -e "${YELLOW}🗑️  Deleting model from Modal...${NC}"
    echo -e "   Category: ${category}"
    echo -e "   Filename: ${filename}"
    echo
    
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        modal run modal/apps/modal_app_fastapi.py::delete_model --category "$category" --filename "$filename"
    else
        echo "Cancelled"
    fi
}

# Main command dispatcher
case "${1:-}" in
    list)
        run_list
        ;;
    download-url)
        shift
        run_download_url "$@"
        ;;
    delete)
        shift
        run_delete "$@"
        ;;
    help|--help|-h|"")
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo
        print_usage
        exit 1
        ;;
esac

