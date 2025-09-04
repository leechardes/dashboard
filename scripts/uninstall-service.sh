#!/bin/bash
# Uninstall Streamlit Dashboard systemd service

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Service configuration
SERVICE_NAME="streamlit-dashboard"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
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

# Backup service logs before removal
backup_service_logs() {
    local backup_dir="$PROJECT_ROOT/logs/service-backup-$(date +%Y%m%d_%H%M%S)"
    
    if [[ -f "$SERVICE_LOG_FILE" ]] || [[ -f "$SERVICE_ERROR_LOG_FILE" ]]; then
        print_status "Backing up service logs to $backup_dir"
        
        mkdir -p "$backup_dir" || {
            print_warning "Could not create backup directory"
            return 1
        }
        
        [[ -f "$SERVICE_LOG_FILE" ]] && cp "$SERVICE_LOG_FILE" "$backup_dir/"
        [[ -f "$SERVICE_ERROR_LOG_FILE" ]] && cp "$SERVICE_ERROR_LOG_FILE" "$backup_dir/"
        
        # Change ownership to devadmin
        chown -R devadmin:devadmin "$backup_dir"
        
        print_status "Logs backed up successfully"
    fi
}

# Uninstall systemd service
uninstall_service() {
    print_status "Uninstalling $SERVICE_NAME systemd service..."
    print_separator
    
    # Check prerequisites
    if ! check_root_permissions; then
        return 1
    fi
    
    # Check if service exists
    if [[ ! -f "$SERVICE_FILE" ]]; then
        print_warning "Service file not found: $SERVICE_FILE"
        print_status "Service may not be installed"
    else
        print_status "Found service file: $SERVICE_FILE"
    fi
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_status "Stopping service..."
        systemctl stop "$SERVICE_NAME" || print_warning "Could not stop service"
        
        # Wait for service to stop
        local count=0
        while systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null && [[ $count -lt 10 ]]; do
            sleep 1
            ((count++))
            echo -n "."
        done
        echo ""
        
        if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
            print_warning "Service did not stop gracefully"
            print_status "Forcing service to stop..."
            systemctl kill --signal=SIGKILL "$SERVICE_NAME" 2>/dev/null || true
        else
            print_status "Service stopped successfully"
        fi
    else
        print_status "Service is not running"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_status "Disabling service..."
        systemctl disable "$SERVICE_NAME" || print_warning "Could not disable service"
    else
        print_status "Service is not enabled"
    fi
    
    # Backup logs before removing
    backup_service_logs
    
    # Remove service file
    if [[ -f "$SERVICE_FILE" ]]; then
        print_status "Removing service file..."
        rm -f "$SERVICE_FILE" || {
            print_error "Failed to remove service file"
            return 1
        }
        print_status "Service file removed"
    fi
    
    # Reload systemd
    print_status "Reloading systemd daemon..."
    systemctl daemon-reload || print_warning "Failed to reload systemd daemon"
    
    # Reset failed state if any
    systemctl reset-failed "$SERVICE_NAME" 2>/dev/null || true
    
    print_separator
    print_status "Service uninstalled successfully!"
    
    # Ask about log file removal
    echo ""
    print_status "Service log files still exist:"
    [[ -f "$SERVICE_LOG_FILE" ]] && print_status "  $SERVICE_LOG_FILE"
    [[ -f "$SERVICE_ERROR_LOG_FILE" ]] && print_status "  $SERVICE_ERROR_LOG_FILE"
    
    # Show cleanup commands
    print_separator
    print_status "Manual cleanup (optional):"
    print_status "  Remove service logs: sudo rm -f $SERVICE_LOG_FILE $SERVICE_ERROR_LOG_FILE"
    print_status "  Remove project logs: rm -rf $PROJECT_ROOT/logs/"
    print_status "  Remove virtual env:  rm -rf $PROJECT_ROOT/.venv/"
}

# Clean removal (remove logs too)
clean_uninstall_service() {
    print_status "Clean uninstall (removing logs)..."
    print_separator
    
    # First do normal uninstall
    uninstall_service || return 1
    
    # Remove service logs
    print_status "Removing service log files..."
    [[ -f "$SERVICE_LOG_FILE" ]] && rm -f "$SERVICE_LOG_FILE"
    [[ -f "$SERVICE_ERROR_LOG_FILE" ]] && rm -f "$SERVICE_ERROR_LOG_FILE"
    
    print_status "Clean uninstall completed!"
}

# Force removal (ignore errors)
force_uninstall_service() {
    print_warning "Force uninstalling service (ignoring errors)..."
    print_separator
    
    # Check root
    if ! check_root_permissions; then
        return 1
    fi
    
    # Force stop all related processes
    print_status "Killing all related processes..."
    pkill -KILL -f "streamlit.*dashboard" 2>/dev/null || true
    pkill -KILL -f "$SERVICE_NAME" 2>/dev/null || true
    
    # Force disable and stop
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    systemctl kill --signal=SIGKILL "$SERVICE_NAME" 2>/dev/null || true
    
    # Remove service file forcefully
    rm -f "$SERVICE_FILE" 2>/dev/null || true
    
    # Remove logs
    rm -f "$SERVICE_LOG_FILE" "$SERVICE_ERROR_LOG_FILE" 2>/dev/null || true
    
    # Reload systemd
    systemctl daemon-reload 2>/dev/null || true
    systemctl reset-failed "$SERVICE_NAME" 2>/dev/null || true
    
    print_status "Force uninstall completed!"
}

# Check installation status
check_service_status() {
    print_status "Service Installation Status"
    print_separator
    
    # Check service file
    if [[ -f "$SERVICE_FILE" ]]; then
        print_status "Service file: ${GREEN}INSTALLED${NC}"
        print_status "  Location: $SERVICE_FILE"
    else
        print_status "Service file: ${RED}NOT INSTALLED${NC}"
    fi
    
    # Check service status
    if systemctl list-unit-files | grep -q "^$SERVICE_NAME.service"; then
        local status=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || echo "inactive")
        local enabled=$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || echo "disabled")
        
        print_status "Service exists in systemd"
        print_status "  Status: $status"
        print_status "  Enabled: $enabled"
        
        if [[ "$status" == "active" ]]; then
            local main_pid=$(systemctl show --property MainPID --value "$SERVICE_NAME" 2>/dev/null)
            [[ -n "$main_pid" && "$main_pid" != "0" ]] && print_status "  PID: $main_pid"
        fi
    else
        print_status "Service: ${RED}NOT REGISTERED${NC} with systemd"
    fi
    
    # Check log files
    echo ""
    print_status "Log files:"
    if [[ -f "$SERVICE_LOG_FILE" ]]; then
        local size=$(du -h "$SERVICE_LOG_FILE" | cut -f1)
        print_status "  Main log: $SERVICE_LOG_FILE ($size)"
    else
        print_status "  Main log: NOT FOUND"
    fi
    
    if [[ -f "$SERVICE_ERROR_LOG_FILE" ]]; then
        local size=$(du -h "$SERVICE_ERROR_LOG_FILE" | cut -f1)
        print_status "  Error log: $SERVICE_ERROR_LOG_FILE ($size)"
    else
        print_status "  Error log: NOT FOUND"
    fi
    
    # Check backup logs
    if [[ -d "$PROJECT_ROOT/logs" ]]; then
        local backup_count=$(find "$PROJECT_ROOT/logs" -name "service-backup-*" -type d 2>/dev/null | wc -l)
        if [[ $backup_count -gt 0 ]]; then
            print_status "  Backup logs: $backup_count backup directories found"
        fi
    fi
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: sudo $0 [OPTIONS]"
        echo ""
        echo "Uninstall Streamlit Dashboard systemd service"
        echo ""
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo "  -c, --clean    Clean uninstall (remove logs too)"
        echo "  -f, --force    Force uninstall (ignore errors)"
        echo "  -s, --status   Check service installation status"
        echo ""
        echo "This script must be run as root (with sudo)"
        echo ""
        echo "The default uninstall preserves service logs in a backup directory."
        echo "Use --clean to remove all logs, or --force for error-free removal."
        echo ""
        ;;
    -c|--clean)
        clean_uninstall_service
        ;;
    -f|--force)
        force_uninstall_service
        ;;
    -s|--status)
        check_service_status
        ;;
    "")
        uninstall_service
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use -h or --help for usage information"
        exit 1
        ;;
esac