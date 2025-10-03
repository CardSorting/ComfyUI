#!/bin/bash

# ComfyUI Headless Service Installation Script
# This script installs ComfyUI as a systemd service for automatic startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="comfyui-headless"
SERVICE_FILE="comfyui-headless.service"
SYSTEMD_DIR="/etc/systemd/system"
COMFYUI_DIR="/home/user/Documents/ComfyUI"
CURRENT_USER=$(whoami)

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check if service file exists
check_service_file() {
    if [ ! -f "$COMFYUI_DIR/systemd/$SERVICE_FILE" ]; then
        error "Service file not found: $COMFYUI_DIR/systemd/$SERVICE_FILE"
        exit 1
    fi
    log "Service file found: $COMFYUI_DIR/systemd/$SERVICE_FILE"
}

# Install service
install_service() {
    log "Installing ComfyUI headless service..."
    
    # Copy service file
    cp "$COMFYUI_DIR/systemd/$SERVICE_FILE" "$SYSTEMD_DIR/"
    success "Service file copied to $SYSTEMD_DIR/$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    success "Systemd daemon reloaded"
    
    # Enable service
    systemctl enable "$SERVICE_NAME"
    success "Service enabled for automatic startup"
    
    log "Service installation completed"
}

# Uninstall service
uninstall_service() {
    log "Uninstalling ComfyUI headless service..."
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "Stopping service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Disable service
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    
    # Remove service file
    rm -f "$SYSTEMD_DIR/$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    success "Service uninstalled"
}

# Show service status
show_status() {
    log "Service status:"
    systemctl status "$SERVICE_NAME" --no-pager || true
    
    echo ""
    log "Service logs (last 20 lines):"
    journalctl -u "$SERVICE_NAME" --no-pager -n 20 || true
}

# Start service
start_service() {
    log "Starting ComfyUI headless service..."
    systemctl start "$SERVICE_NAME"
    sleep 3
    show_status
}

# Stop service
stop_service() {
    log "Stopping ComfyUI headless service..."
    systemctl stop "$SERVICE_NAME"
    success "Service stopped"
}

# Restart service
restart_service() {
    log "Restarting ComfyUI headless service..."
    systemctl restart "$SERVICE_NAME"
    sleep 3
    show_status
}

# Show logs
show_logs() {
    log "Showing ComfyUI headless service logs (press Ctrl+C to exit):"
    journalctl -u "$SERVICE_NAME" -f
}

# Main function
main() {
    case "${1:-install}" in
        "install")
            check_root
            check_service_file
            install_service
            log "To start the service, run: sudo systemctl start $SERVICE_NAME"
            log "To check status, run: sudo systemctl status $SERVICE_NAME"
            ;;
        "uninstall")
            check_root
            uninstall_service
            ;;
        "start")
            check_root
            start_service
            ;;
        "stop")
            check_root
            stop_service
            ;;
        "restart")
            check_root
            restart_service
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            echo "ComfyUI Headless Service Management"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  install    Install ComfyUI as a systemd service (default)"
            echo "  uninstall  Remove ComfyUI systemd service"
            echo "  start      Start the service"
            echo "  stop       Stop the service"
            echo "  restart    Restart the service"
            echo "  status     Show service status"
            echo "  logs       Show and follow service logs"
            echo "  help       Show this help message"
            echo ""
            echo "Note: Most commands require root privileges (use sudo)"
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
