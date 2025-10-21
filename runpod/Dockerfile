# RunPod Serverless Dockerfile for ComfyUI
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV COMFYUI_HEADLESS=1
ENV DISABLE_PROGRESS_BARS=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Install RunPod SDK
RUN pip3 install runpod

# Copy ComfyUI files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/models/checkpoints \
    /app/models/vae \
    /app/models/loras \
    /app/models/embeddings \
    /app/models/upscale_models \
    /app/models/controlnet \
    /app/input \
    /app/output \
    /app/temp

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# RunPod handler
CMD ["python3", "runpod/runpod_handler.py"]

