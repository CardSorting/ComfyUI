#!/bin/bash
# RunPod Deployment Script

set -e  # Exit on error

echo "========================================="
echo "RunPod Serverless Deployment Script"
echo "========================================="
echo ""

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-your_dockerhub_username}"
IMAGE_NAME="${IMAGE_NAME:-comfyui-runpod}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE="${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if user is logged into Docker Hub
if ! docker info | grep -q "Username"; then
    echo "You're not logged into Docker Hub"
    echo "Please run: docker login"
    exit 1
fi

# Get Docker username if not set
if [ "$DOCKER_USERNAME" = "your_dockerhub_username" ]; then
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME
    FULL_IMAGE="${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo "Docker image will be: $FULL_IMAGE"
echo ""

# Build the Docker image
echo "Step 1: Building Docker image..."
echo "This may take 10-15 minutes..."
cd "$(dirname "$0")/.."  # Go to project root

docker build \
    -f runpod/Dockerfile \
    -t "$FULL_IMAGE" \
    --platform linux/amd64 \
    .

if [ $? -ne 0 ]; then
    echo "Error: Docker build failed"
    exit 1
fi

echo ""
echo "✓ Docker image built successfully!"
echo ""

# Push to Docker Hub
echo "Step 2: Pushing to Docker Hub..."
docker push "$FULL_IMAGE"

if [ $? -ne 0 ]; then
    echo "Error: Docker push failed"
    exit 1
fi

echo ""
echo "✓ Docker image pushed successfully!"
echo ""

# Print next steps
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Your Docker image: $FULL_IMAGE"
echo ""
echo "Next Steps:"
echo ""
echo "1. Go to RunPod: https://www.runpod.io/console/serverless"
echo ""
echo "2. Click 'New Endpoint' or 'Deploy'"
echo ""
echo "3. Configure your endpoint:"
echo "   - Name: comfyui-api"
echo "   - Docker Image: $FULL_IMAGE"
echo "   - GPU Type: Select your preferred GPU (e.g., RTX 4090, A100)"
echo "   - Min Workers: 0 (for auto-scaling)"
echo "   - Max Workers: 3-5 (adjust based on your needs)"
echo "   - Idle Timeout: 60 seconds"
echo ""
echo "4. Advanced Settings (optional):"
echo "   - Container Disk: 20 GB (adjust if you need more models)"
echo "   - Volume: Attach if you want persistent model storage"
echo ""
echo "5. Click 'Deploy' and wait for deployment"
echo ""
echo "6. Test your endpoint with:"
echo "   python runpod/test_runpod.py YOUR_ENDPOINT_ID YOUR_API_KEY"
echo ""
echo "========================================="

