#!/bin/bash
# Install Streamlit Dashboard as systemd service

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Service configuration
SERVICE_NAME="streamlit-dashboard"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SOURCE_SERVICE_FILE="$PROJECT_ROOT/systemd/$SERVICE_NAME.service"
LOG_DIR="/var/log"
SERVICE_LOG_FILE="$LOG_DIR/$SERVICE_NAME.log"
SERVICE_ERROR_LOG_FILE="$LOG_DIR/$SERVICE_NAME.error.log"

# Check if running as root
check_root_permissions() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        print_status "Example: sudo bash $0"
        return 1
    fi
}

# Backup existing service if it exists
backup_existing_service() {
    if [[ -f "$SERVICE_FILE" ]]; then
        local backup_file="${SERVICE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        print_warning "Existing service file found"
        print_status "Creating backup: $backup_file"
        cp "$SERVICE_FILE" "$backup_file" || {
            print_error "Failed to create backup"
            return 1
        }
    fi
}

# Install systemd service
install_service() {
    print_status "Installing $SERVICE_NAME systemd service..."
    print_separator
    
    # Check prerequisites
    if ! check_root_permissions; then
        return 1
    fi
    
    # Check source service file exists
    if [[ ! -f "$SOURCE_SERVICE_FILE" ]]; then
        print_error "Source service file not found: $SOURCE_SERVICE_FILE"
        return 1
    fi
    
    # Check project structure
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        print_error "Project root not found: $PROJECT_ROOT"
        return 1
    fi
    
    if [[ ! -f "$APP_FILE" ]]; then
        print_error "App file not found: $APP_FILE"
        return 1
    fi
    
    if [[ ! -d "$VENV_PATH" ]]; then
        print_error "Virtual environment not found: $VENV_PATH"
        print_error "Run 'make install' first to create it"
        return 1
    fi
    
    # Stop existing service if running
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_status "Stopping existing service..."
        systemctl stop "$SERVICE_NAME" || print_warning "Could not stop existing service"
    fi
    
    # Backup existing service
    backup_existing_service || return 1
    
    # Copy service file
    print_status "Installing service file..."
    cp "$SOURCE_SERVICE_FILE" "$SERVICE_FILE" || {
        print_error "Failed to copy service file"
        return 1
    }
    
    # Set correct permissions
    chmod 644 "$SERVICE_FILE"
    
    # Create log files with correct permissions
    print_status "Setting up log files..."
    touch "$SERVICE_LOG_FILE" "$SERVICE_ERROR_LOG_FILE"
    chown devadmin:devadmin "$SERVICE_LOG_FILE" "$SERVICE_ERROR_LOG_FILE"
    chmod 644 "$SERVICE_LOG_FILE" "$SERVICE_ERROR_LOG_FILE"
    
    # Reload systemd
    print_status "Reloading systemd daemon..."
    systemctl daemon-reload || {
        print_error "Failed to reload systemd daemon"
        return 1
    }
    
    # Enable service
    print_status "Enabling service for auto-start..."
    systemctl enable "$SERVICE_NAME" || {
        print_error "Failed to enable service"
        return 1
    }
    
    # Start service
    print_status "Starting service..."
    systemctl start "$SERVICE_NAME" || {
        print_error "Failed to start service"
        print_status "Check service status with: systemctl status $SERVICE_NAME"
        print_status "Check service logs with: journalctl -u $SERVICE_NAME"
        return 1
    }
    
    # Wait for service to start
    print_status "Waiting for service to start..."
    sleep 5
    
    # Verify service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service started successfully!"
        
        # Show service info
        print_separator
        print_status "Service Information:"
        print_status "  Name: $SERVICE_NAME"
        print_status "  Status: $(systemctl is-active "$SERVICE_NAME")"
        print_status "  Enabled: $(systemctl is-enabled "$SERVICE_NAME")"
        print_status "  Config: $SERVICE_FILE"
        print_status "  Logs: $SERVICE_LOG_FILE"
        print_status "  Error Logs: $SERVICE_ERROR_LOG_FILE"
        
        # Get service URL
        load_env
        local url=$(get_service_url)
        print_status "  URL: $url"
        
        print_separator
        print_status "Service installed and started successfully!"
        print_status "The dashboard will now start automatically on boot"
        
        # Show management commands
        print_separator
        print_status "Service Management Commands:"
        print_status "  Check status:    systemctl status $SERVICE_NAME"
        print_status "  Start service:   systemctl start $SERVICE_NAME"
        print_status "  Stop service:    systemctl stop $SERVICE_NAME"
        print_status "  Restart service: systemctl restart $SERVICE_NAME"
        print_status "  View logs:       journalctl -u $SERVICE_NAME -f"
        print_status "  Disable service: systemctl disable $SERVICE_NAME"
        
        print_separator
        print_status "Makefile Commands:"
        print_status "  Check service:   make service-status"
        print_status "  View logs:       make service-logs"
        print_status "  Disable service: make disable-service"
        print_status "  Remove service:  make uninstall-service"
        
    else
        print_error "Service failed to start!"
        print_status "Check what went wrong:"
        systemctl status "$SERVICE_NAME" --no-pager
        return 1
    fi
}

# Verify installation
verify_installation() {
    print_separator
    print_status "Verifying Installation"
    print_separator
    
    # Check service file
    if [[ -f "$SERVICE_FILE" ]]; then
        print_status "Service file: ${GREEN}INSTALLED${NC}"
    else
        print_error "Service file: NOT FOUND"
        return 1
    fi
    
    # Check service status
    local status=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || echo "inactive")
    local enabled=$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || echo "disabled")
    
    if [[ "$status" == "active" ]]; then
        print_status "Service status: ${GREEN}$status${NC}"
    else
        print_warning "Service status: ${YELLOW}$status${NC}"
    fi
    
    if [[ "$enabled" == "enabled" ]]; then
        print_status "Auto-start: ${GREEN}$enabled${NC}"
    else
        print_warning "Auto-start: ${YELLOW}$enabled${NC}"
    fi
    
    # Check logs
    if [[ -f "$SERVICE_LOG_FILE" ]]; then
        print_status "Log file: ${GREEN}EXISTS${NC}"
        local log_size=$(du -h "$SERVICE_LOG_FILE" | cut -f1)
        print_status "Log size: $log_size"
    fi
    
    # Test connectivity
    load_env
    local url=$(get_service_url)
    print_status "Testing connectivity to $url..."
    
    if curl -s --connect-timeout 5 "$url" >/dev/null 2>&1; then
        print_status "Connection test: ${GREEN}SUCCESS${NC}"
        print_status "Dashboard is accessible at: $url"
    else
        print_warning "Connection test: ${YELLOW}FAILED${NC}"
        print_warning "Service may still be starting up"
        print_status "Wait a moment and try accessing: $url"
    fi
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: sudo $0 [OPTIONS]"
        echo ""
        echo "Install Streamlit Dashboard as a systemd service"
        echo ""
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo "  -v, --verify   Verify installation after install"
        echo "  --verify-only  Only verify existing installation"
        echo ""
        echo "This script must be run as root (with sudo)"
        echo ""
        echo "Prerequisites:"
        echo "  - Virtual environment created (make install)"
        echo "  - Service file exists in systemd/ directory"
        echo "  - User 'devadmin' exists"
        echo ""
        ;;
    -v|--verify)
        install_service && verify_installation
        ;;
    --verify-only)
        verify_installation
        ;;
    "")
        install_service
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use -h or --help for usage information"
        exit 1
        ;;
esac