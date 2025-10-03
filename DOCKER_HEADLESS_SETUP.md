# ComfyUI Headless Docker Setup with Model Download CLI

## 🐳 Overview

This guide shows how to set up ComfyUI in a headless Docker environment with the Model Download CLI tool integrated for automated model management.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Git
- Basic command line knowledge
- At least 8GB RAM (16GB recommended)
- NVIDIA GPU with CUDA support (optional but recommended)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone ComfyUI repository
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Make the download script executable
chmod +x download_models.sh
```

### 2. Create Docker Configuration

Create a `Dockerfile` in the ComfyUI root directory:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
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
```

### 3. Create Docker Compose Configuration

Create a `docker-compose.yml` file:

```yaml
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
      - HUGGINGFACE_HUB_TOKEN=${HUGGINGFACE_HUB_TOKEN:-}
      - CIVITAI_API_KEY=${CIVITAI_API_KEY:-}
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8188/system_stats"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Redis for queue management
  redis:
    image: redis:7-alpine
    container_name: comfyui-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### 4. Create Environment File

Create a `.env` file for configuration:

```bash
# API Keys (optional but recommended)
HUGGINGFACE_HUB_TOKEN=your_huggingface_token_here
CIVITAI_API_KEY=your_civitai_api_key_here

# ComfyUI Configuration
COMFYUI_PORT=8188
COMFYUI_HOST=0.0.0.0

# Model Download Configuration
MODEL_DOWNLOAD_ENABLED=true
AUTO_DOWNLOAD_MODELS=false
```

## 🔧 Advanced Docker Setup

### Custom Dockerfile with Model Pre-download

Create a `Dockerfile.advanced` for pre-downloading models:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
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

# Create model download script
RUN echo '#!/bin/bash\n\
echo "Downloading essential models..."\n\
python download_models.py download --source url --url "https://huggingface.co/runwayml/stable-diffusion-v1-5"\n\
python download_models.py download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"\n\
echo "Model download complete!"' > /app/download_essential_models.sh

RUN chmod +x /app/download_essential_models.sh

# Expose port
EXPOSE 8188

# Set environment variables
ENV PYTHONPATH=/app
ENV COMFYUI_PORT=8188

# Download models and start ComfyUI
CMD ["/bin/bash", "-c", "/app/download_essential_models.sh && python main.py --listen 0.0.0.0 --port 8188"]
```

## 🚀 Running the Setup

### 1. Build and Start

```bash
# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f comfyui
```

### 2. Verify Installation

```bash
# Check if ComfyUI is running
curl http://localhost:8188/system_stats

# Check container status
docker-compose ps

# Access the container
docker-compose exec comfyui bash
```

## 📥 Model Management in Docker

### 1. Download Models via Container

```bash
# Access the container
docker-compose exec comfyui bash

# Download models using the CLI
./download_models.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"

# Search for models
./download_models.sh huggingface search --query "stable diffusion" --limit 5
```

### 2. Download Models from Host

```bash
# Copy the download script to host (if not already there)
docker cp comfyui-headless:/app/download_models.sh ./download_models.sh
docker cp comfyui-headless:/app/download_models.py ./download_models.py
docker cp comfyui-headless:/app/huggingface_integration.py ./huggingface_integration.py
docker cp comfyui-headless:/app/civitai_integration.py ./civitai_integration.py

# Make executable
chmod +x download_models.sh

# Download models (they'll be saved to the mounted volume)
./download_models.sh download --source url --url "https://civitai.com/models/257749/pony-diffusion-v6-xl"
```

### 3. Batch Model Downloads

Create a `docker_models_config.json`:

```json
{
  "models": [
    {
      "name": "Stable Diffusion XL",
      "source": "huggingface",
      "repo": "stabilityai/stable-diffusion-xl-base-1.0"
    },
    {
      "name": "Pony Diffusion",
      "source": "civitai",
      "model_id": 257749
    },
    {
      "name": "DreamShaper",
      "source": "civitai",
      "model_id": 128713
    }
  ]
}
```

Download batch:

```bash
# From host
./download_models.sh batch docker_models_config.json

# Or from container
docker-compose exec comfyui ./download_models.sh batch docker_models_config.json
```

## 🔄 Automation Scripts

### 1. Model Update Script

Create `update_models.sh`:

```bash
#!/bin/bash

echo "Updating ComfyUI models..."

# Download latest models
./download_models.sh huggingface search --query "stable diffusion" --limit 3

# Download specific models
./download_models.sh download --source url --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"

echo "Model update complete!"
```

### 2. Docker Management Script

Create `docker_management.sh`:

```bash
#!/bin/bash

case "$1" in
    "start")
        echo "Starting ComfyUI..."
        docker-compose up -d
        ;;
    "stop")
        echo "Stopping ComfyUI..."
        docker-compose down
        ;;
    "restart")
        echo "Restarting ComfyUI..."
        docker-compose restart
        ;;
    "logs")
        docker-compose logs -f comfyui
        ;;
    "shell")
        docker-compose exec comfyui bash
        ;;
    "download")
        docker-compose exec comfyui ./download_models.sh "$@"
        ;;
    "status")
        docker-compose ps
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|shell|download|status}"
        exit 1
        ;;
esac
```

Make executable and use:

```bash
chmod +x docker_management.sh

# Start ComfyUI
./docker_management.sh start

# Download a model
./docker_management.sh download --source url --url "https://huggingface.co/runwayml/stable-diffusion-v1-5"

# View logs
./docker_management.sh logs
```

## 🌐 API Integration

### 1. Basic API Usage

```bash
# Start ComfyUI with API enabled
docker-compose up -d

# Test API
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": {"1": {"inputs": {"text": "a beautiful landscape"}, "class_type": "CLIPTextEncode"}}}'
```

### 2. Python API Client

Create `api_client.py`:

```python
import requests
import json

class ComfyUIAPI:
    def __init__(self, host="localhost", port=8188):
        self.base_url = f"http://{host}:{port}"
    
    def queue_prompt(self, prompt):
        response = requests.post(
            f"{self.base_url}/prompt",
            json={"prompt": prompt}
        )
        return response.json()
    
    def get_history(self, prompt_id):
        response = requests.get(f"{self.base_url}/history/{prompt_id}")
        return response.json()
    
    def get_system_stats(self):
        response = requests.get(f"{self.base_url}/system_stats")
        return response.json()

# Usage
api = ComfyUIAPI()
stats = api.get_system_stats()
print(f"ComfyUI Status: {stats}")
```

## 🔧 Configuration Options

### 1. Custom Model Paths

Create `extra_model_paths.yaml`:

```yaml
checkpoints:
  - /app/models/checkpoints
  - /app/custom_models/checkpoints

loras:
  - /app/models/loras
  - /app/custom_models/loras

vae:
  - /app/models/vae
  - /app/custom_models/vae
```

### 2. Environment Variables

```bash
# ComfyUI Configuration
COMFYUI_PORT=8188
COMFYUI_HOST=0.0.0.0
COMFYUI_EXTRA_MODEL_PATHS=/app/extra_model_paths.yaml

# Model Download Configuration
MODEL_DOWNLOAD_ENABLED=true
AUTO_DOWNLOAD_MODELS=false
MODEL_CACHE_DIR=/app/models

# API Keys
HUGGINGFACE_HUB_TOKEN=your_token
CIVITAI_API_KEY=your_key
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs
docker-compose logs comfyui

# Check if port is in use
netstat -tulpn | grep 8188

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 2. Model Download Issues
```bash
# Check network connectivity
docker-compose exec comfyui ping huggingface.co

# Check API keys
docker-compose exec comfyui env | grep -E "(HUGGINGFACE|CIVITAI)"

# Test download manually
docker-compose exec comfyui ./download_models.sh huggingface search --query "test"
```

#### 3. GPU Issues
```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check container GPU access
docker-compose exec comfyui nvidia-smi
```

### Performance Optimization

#### 1. Resource Limits

Update `docker-compose.yml`:

```yaml
services:
  comfyui:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '8.0'
        reservations:
          memory: 8G
          cpus: '4.0'
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### 2. Volume Optimization

```yaml
volumes:
  - ./models:/app/models:rw
  - ./output:/app/output:rw
  - model_cache:/app/.cache:rw

volumes:
  model_cache:
    driver: local
```

## 📊 Monitoring

### 1. Health Checks

```bash
# Check container health
docker-compose ps

# Check ComfyUI API
curl http://localhost:8188/system_stats

# Check model directories
docker-compose exec comfyui ls -la /app/models/
```

### 2. Log Monitoring

```bash
# Follow logs
docker-compose logs -f comfyui

# Check specific log patterns
docker-compose logs comfyui | grep -i error
docker-compose logs comfyui | grep -i "model download"
```

## 🚀 Production Deployment

### 1. Security Considerations

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  comfyui:
    build: .
    container_name: comfyui-prod
    ports:
      - "127.0.0.1:8188:8188"  # Bind to localhost only
    environment:
      - COMFYUI_PORT=8188
      - HUGGINGFACE_HUB_TOKEN=${HUGGINGFACE_HUB_TOKEN}
      - CIVITAI_API_KEY=${CIVITAI_API_KEY}
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/output
```

### 2. Reverse Proxy Setup

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8188;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🎯 Best Practices

### 1. Model Management
- Use version control for model configurations
- Regularly update models
- Monitor disk usage
- Use batch downloads for efficiency

### 2. Container Management
- Use specific image tags
- Regular security updates
- Monitor resource usage
- Backup important data

### 3. API Usage
- Implement rate limiting
- Use authentication for production
- Monitor API usage
- Implement proper error handling

## 📚 Additional Resources

- [ComfyUI Documentation](https://docs.comfy.org)
- [Docker Documentation](https://docs.docker.com)
- [Hugging Face Hub](https://huggingface.co/docs/hub)
- [Civitai API](https://civitai.com/api-docs)

## 🎉 Conclusion

This setup provides a robust, scalable solution for running ComfyUI headless with Docker and integrated model management. The Model Download CLI tool makes it easy to manage models in a containerized environment, while Docker provides isolation, portability, and easy deployment.

Happy creating! 🎨
