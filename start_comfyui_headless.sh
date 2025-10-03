#!/bin/bash

# ComfyUI Headless Startup Script
# Optimized for NVIDIA GeForce RTX 4090 with CUDA acceleration
# Based on successful testing and configuration

set -e  # Exit on any error

# Configuration
COMFYUI_DIR="/home/user/Documents/ComfyUI"
COMFYUI_PORT=8188
COMFYUI_HOST="0.0.0.0"
LOG_FILE="$COMFYUI_DIR/comfyui_headless.log"
PID_FILE="$COMFYUI_DIR/comfyui_headless.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if ComfyUI is already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PID_FILE"  # Clean up stale PID file
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Stop ComfyUI if running
stop_comfyui() {
    if check_running; then
        log "Stopping existing ComfyUI process (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        sleep 3
        
        # Force kill if still running
        if ps -p "$PID" > /dev/null 2>&1; then
            warning "Force killing ComfyUI process..."
            kill -9 "$PID" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
        success "ComfyUI stopped"
    else
        log "ComfyUI is not running"
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check if CUDA is available
    if ! command -v nvidia-smi &> /dev/null; then
        error "nvidia-smi not found. CUDA drivers may not be installed."
        exit 1
    fi
    
    # Check CUDA version
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    log "CUDA Version: $CUDA_VERSION"
    
    # Check GPU
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    log "GPU: $GPU_NAME (${GPU_MEMORY}MB)"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 not found"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version)
    log "Python: $PYTHON_VERSION"
    
    # Check PyTorch CUDA support
    log "Checking PyTorch CUDA support..."
    if ! python3 -c "import torch; print('PyTorch CUDA available:', torch.cuda.is_available())" 2>/dev/null; then
        error "PyTorch CUDA support check failed"
        exit 1
    fi
    
    success "System requirements check passed"
}

# Check if port is available
check_port() {
    if lsof -i ":$COMFYUI_PORT" > /dev/null 2>&1; then
        error "Port $COMFYUI_PORT is already in use"
        log "Processes using port $COMFYUI_PORT:"
        lsof -i ":$COMFYUI_PORT"
        exit 1
    fi
    log "Port $COMFYUI_PORT is available"
}

# Determine optimal GPU memory flags based on GPU
get_gpu_flags() {
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    
    if [ "$GPU_MEMORY" -ge 20000 ]; then
        # High VRAM GPUs (RTX 4090, A100, etc.)
        echo "--gpu-only"
    elif [ "$GPU_MEMORY" -ge 16000 ]; then
        # High VRAM GPUs (RTX 4080, etc.)
        echo "--highvram"
    elif [ "$GPU_MEMORY" -ge 8000 ]; then
        # Normal VRAM GPUs (RTX 4070, RTX 3080, etc.)
        echo "--normalvram"
    else
        # Low VRAM GPUs (RTX 4060, RTX 3070, etc.)
        echo "--lowvram"
    fi
}

# Start ComfyUI
start_comfyui() {
    log "Starting ComfyUI in headless mode..."
    
    # Change to ComfyUI directory
    cd "$COMFYUI_DIR" || {
        error "Failed to change to ComfyUI directory: $COMFYUI_DIR"
        exit 1
    }
    
    # Get optimal GPU flags
    GPU_FLAGS=$(get_gpu_flags)
    log "Using GPU flags: $GPU_FLAGS"
    
    # Set environment variables
    export CUDA_VISIBLE_DEVICES=0
    export TQDM_DISABLE=1
    export PYTHONUNBUFFERED=1
    
    # Start ComfyUI with optimal configuration
    nohup python3 main.py \
        --headless \
        --listen "$COMFYUI_HOST" \
        --port "$COMFYUI_PORT" \
        --cuda-device 0 \
        $GPU_FLAGS \
        --disable-cuda-malloc \
        --verbose INFO \
        > "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait for startup
    log "Waiting for ComfyUI to start..."
    sleep 10
    
    # Check if process is still running
    if ! check_running; then
        error "ComfyUI failed to start. Check log file: $LOG_FILE"
        exit 1
    fi
    
    # Test API endpoint
    log "Testing API endpoint..."
    for i in {1..30}; do
        if curl -s "http://localhost:$COMFYUI_PORT/api/system_stats" > /dev/null 2>&1; then
            success "ComfyUI is running and API is accessible"
            log "API available at: http://$COMFYUI_HOST:$COMFYUI_PORT/api/"
            return 0
        fi
        sleep 2
    done
    
    error "ComfyUI API is not responding after 60 seconds"
    exit 1
}

# Show status
show_status() {
    if check_running; then
        success "ComfyUI is running (PID: $PID)"
        log "API URL: http://$COMFYUI_HOST:$COMFYUI_PORT/api/"
        log "Log file: $LOG_FILE"
        
        # Show system stats
        log "System stats:"
        curl -s "http://localhost:$COMFYUI_PORT/api/system_stats" | python3 -m json.tool 2>/dev/null || log "Could not retrieve system stats"
    else
        log "ComfyUI is not running"
    fi
}

# Show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        log "Log file not found: $LOG_FILE"
    fi
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            if check_running; then
                warning "ComfyUI is already running (PID: $PID)"
                exit 0
            fi
            
            check_requirements
            check_port
            start_comfyui
            ;;
        "stop")
            stop_comfyui
            ;;
        "restart")
            stop_comfyui
            sleep 2
            check_requirements
            check_port
            start_comfyui
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            echo "ComfyUI Headless Startup Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start    Start ComfyUI in headless mode (default)"
            echo "  stop     Stop ComfyUI"
            echo "  restart  Restart ComfyUI"
            echo "  status   Show ComfyUI status"
            echo "  logs     Show and follow logs"
            echo "  help     Show this help message"
            echo ""
            echo "Configuration:"
            echo "  ComfyUI Directory: $COMFYUI_DIR"
            echo "  Port: $COMFYUI_PORT"
            echo "  Host: $COMFYUI_HOST"
            echo "  Log File: $LOG_FILE"
            echo "  PID File: $PID_FILE"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
