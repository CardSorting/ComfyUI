#!/bin/bash
# ComfyUI Model Download Wrapper Script
# This script provides a convenient way to use the model download tools

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/download_models.py"
ADVANCED_SCRIPT="$SCRIPT_DIR/download_models_advanced.py"

# Function to show usage
show_usage() {
    echo "ComfyUI Model Download Tool"
    echo ""
    echo "Usage: $0 [OPTIONS] COMMAND [ARGS...]"
    echo ""
echo "Commands:"
echo "  list [--model-type TYPE]              List available models"
echo "  download [OPTIONS]                    Download a model"
echo "  search QUERY [--model-type TYPE]      Search for models on Hugging Face"
echo "  popular [--model-type TYPE]           List popular models"
echo "  batch [CONFIG_FILE]                   Batch download from config file"
echo "  civitai [COMMAND]                     Civitai-specific commands"
echo "  install-deps                          Install required dependencies"
    echo ""
echo "Download Options:"
echo "  --model-type TYPE                     Model type (checkpoints, loras, vae, etc.)"
echo "  --source SOURCE                       Source (huggingface, url, civitai)"
echo "  --repo REPO_ID                        Hugging Face repository ID"
echo "  --url URL                             Direct download URL"
echo "  --model-id ID                         Civitai model ID"
echo "  --version-id ID                       Civitai version ID"
echo "  --civitai-url URL                     Civitai URL (auto-extracts IDs)"
echo "  --filename FILENAME                   Specific filename to download"
echo "  --api-key KEY                         API key for authentication"
    echo ""
echo "Examples:"
echo "  $0 list"
echo "  $0 list --model-type checkpoints"
echo "  $0 download --model-type checkpoints --source huggingface --repo runwayml/stable-diffusion-v1-5"
echo "  $0 download --model-type checkpoints --source civitai --model-id 12345"
echo "  $0 download --model-type checkpoints --source civitai --civitai-url \"https://civitai.com/models/12345/model-name\""
echo "  $0 search \"stable diffusion\" --limit 5"
echo "  $0 popular --model-type checkpoints"
echo "  $0 civitai search \"anime\" --limit 5"
echo "  $0 civitai types"
echo "  $0 batch models_config.json"
    echo ""
}

# Function to install dependencies
install_deps() {
    echo "Installing dependencies for ComfyUI Model Download Tool..."
    
    if [ -f "$SCRIPT_DIR/requirements-download.txt" ]; then
        pip install -r "$SCRIPT_DIR/requirements-download.txt"
    else
        echo "Installing basic dependencies..."
        pip install huggingface_hub tqdm requests safetensors
    fi
    
    echo "Dependencies installed successfully!"
}

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: download_models.py not found in $SCRIPT_DIR"
    exit 1
fi

# Parse command
case "${1:-}" in
    "list")
        shift
        python "$PYTHON_SCRIPT" list "$@"
        ;;
    "download")
        shift
        python "$PYTHON_SCRIPT" download "$@"
        ;;
    "search")
        if [ -f "$ADVANCED_SCRIPT" ]; then
            shift
            python "$ADVANCED_SCRIPT" search "$@"
        else
            echo "Error: Advanced features require download_models_advanced.py"
            exit 1
        fi
        ;;
    "popular")
        if [ -f "$ADVANCED_SCRIPT" ]; then
            shift
            python "$ADVANCED_SCRIPT" popular "$@"
        else
            echo "Error: Advanced features require download_models_advanced.py"
            exit 1
        fi
        ;;
    "batch")
        if [ -f "$ADVANCED_SCRIPT" ]; then
            shift
            if [ $# -eq 0 ]; then
                echo "Error: Config file required for batch download"
                echo "Usage: $0 batch CONFIG_FILE"
                exit 1
            fi
            python "$ADVANCED_SCRIPT" batch-download --config "$1"
        else
            echo "Error: Advanced features require download_models_advanced.py"
            exit 1
        fi
        ;;
    "civitai")
        shift
        python "$PYTHON_SCRIPT" civitai "$@"
        ;;
    "install-deps")
        install_deps
        ;;
    "help"|"-h"|"--help"|"")
        show_usage
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_usage
        exit 1
        ;;
esac
