#!/bin/bash

# ComfyUI Docker Management Script
# This script provides easy management of ComfyUI in Docker with model download integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} ComfyUI Docker Management${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install docker-compose and try again."
        exit 1
    fi
}

# Function to show help
show_help() {
    print_header
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup                 Setup ComfyUI Docker environment"
    echo "  start                 Start ComfyUI container"
    echo "  stop                  Stop ComfyUI container"
    echo "  restart               Restart ComfyUI container"
    echo "  status                Show container status"
    echo "  logs                  Show container logs"
    echo "  shell                 Access container shell"
    echo "  download [ARGS]       Download models using the CLI"
    echo "  search [ARGS]         Search for models"
    echo "  list                  List downloaded models"
    echo "  update                Update models"
    echo "  clean                 Clean up unused Docker resources"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start"
    echo "  $0 download --source url --url 'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0'"
    echo "  $0 search --query 'stable diffusion' --limit 5"
    echo "  $0 logs"
    echo "  $0 shell"
}

# Function to setup Docker environment
setup() {
    print_header
    print_status "Setting up ComfyUI Docker environment..."
    
    check_docker
    check_docker_compose
    
    # Create necessary directories
    print_status "Creating directories..."
    mkdir -p models/{checkpoints,loras,vae,text_encoders,unet,controlnet,embeddings,upscale_models}
    mkdir -p output input custom_nodes
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# API Keys (optional but recommended)
HUGGINGFACE_HUB_TOKEN=
CIVITAI_API_KEY=

# ComfyUI Configuration
COMFYUI_PORT=8188
COMFYUI_HOST=0.0.0.0

# Model Download Configuration
MODEL_DOWNLOAD_ENABLED=true
AUTO_DOWNLOAD_MODELS=false
EOF
        print_warning "Please edit .env file and add your API keys if needed."
    fi
    
    # Create docker-compose.yml if it doesn't exist
    if [ ! -f docker-compose.yml ]; then
        print_status "Creating docker-compose.yml..."
        cat > docker-compose.yml << EOF
version: '3.8'

services:
  comfyui:
    build: .
    container_name: comfyui-headless
    ports:
      - "8188:8188"
    volumes:
      - ./models:/app/models
      - ./output:/app/output
      - ./input:/app/input
      - ./custom_nodes:/app/custom_nodes
    environment:
      - COMFYUI_PORT=8188
      - HUGGINGFACE_HUB_TOKEN=\${HUGGINGFACE_HUB_TOKEN:-}
      - CIVITAI_API_KEY=\${CIVITAI_API_KEY:-}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8188/system_stats"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF
    fi
    
    # Create Dockerfile if it doesn't exist
    if [ ! -f Dockerfile ]; then
        print_status "Creating Dockerfile..."
        cat > Dockerfile << EOF
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    wget \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy ComfyUI files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-download.txt

# Create models directory structure
RUN mkdir -p models/{checkpoints,loras,vae,text_encoders,unet,controlnet,embeddings,upscale_models}

# Make scripts executable
RUN chmod +x download_models.sh

# Expose port
EXPOSE 8188

# Set environment variables
ENV PYTHONPATH=/app
ENV COMFYUI_PORT=8188

# Default command
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
EOF
    fi
    
    print_status "Setup complete! You can now run: $0 start"
}

# Function to start ComfyUI
start() {
    print_header
    print_status "Starting ComfyUI..."
    
    check_docker
    check_docker_compose
    
    # Build if needed
    if [ ! -f docker-compose.yml ]; then
        print_error "Docker setup not found. Run '$0 setup' first."
        exit 1
    fi
    
    docker-compose up -d
    print_status "ComfyUI started! Access it at http://localhost:8188"
    print_status "Use '$0 logs' to view logs or '$0 status' to check status."
}

# Function to stop ComfyUI
stop() {
    print_header
    print_status "Stopping ComfyUI..."
    docker-compose down
    print_status "ComfyUI stopped."
}

# Function to restart ComfyUI
restart() {
    print_header
    print_status "Restarting ComfyUI..."
    docker-compose restart
    print_status "ComfyUI restarted!"
}

# Function to show status
status() {
    print_header
    print_status "ComfyUI Container Status:"
    docker-compose ps
    
    echo ""
    print_status "System Stats:"
    if curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
        curl -s http://localhost:8188/system_stats | python3 -m json.tool 2>/dev/null || echo "API responding but JSON parsing failed"
    else
        print_warning "ComfyUI API not responding"
    fi
}

# Function to show logs
logs() {
    print_header
    print_status "Showing ComfyUI logs (Ctrl+C to exit):"
    docker-compose logs -f comfyui
}

# Function to access shell
shell() {
    print_header
    print_status "Accessing ComfyUI container shell..."
    docker-compose exec comfyui bash
}

# Function to download models
download() {
    print_header
    print_status "Downloading models..."
    docker-compose exec comfyui ./download_models.sh download "$@"
}

# Function to search models
search() {
    print_header
    print_status "Searching models..."
    docker-compose exec comfyui ./download_models.sh "$@"
}

# Function to list models
list() {
    print_header
    print_status "Listing downloaded models..."
    docker-compose exec comfyui ./download_models.sh list "$@"
}

# Function to update models
update() {
    print_header
    print_status "Updating models..."
    
    # Download some popular models
    docker-compose exec comfyui ./download_models.sh download --source url --url "https://huggingface.co/runwayml/stable-diffusion-v1-5"
    docker-compose exec comfyui ./download_models.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"
    
    print_status "Model update complete!"
}

# Function to clean up
clean() {
    print_header
    print_status "Cleaning up unused Docker resources..."
    docker system prune -f
    print_status "Cleanup complete!"
}

# Main script logic
case "$1" in
    "setup")
        setup
        ;;
    "start")
        start
        ;;
    "stop")
        stop
        ;;
    "restart")
        restart
        ;;
    "status")
        status
        ;;
    "logs")
        logs
        ;;
    "shell")
        shell
        ;;
    "download")
        shift
        download "$@"
        ;;
    "search")
        shift
        search "$@"
        ;;
    "list")
        shift
        list "$@"
        ;;
    "update")
        update
        ;;
    "clean")
        clean
        ;;
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
