#!/bin/bash
# Status check script for Streamlit Dashboard

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Show dashboard status
show_status() {
    print_status "Streamlit Dashboard Status"
    print_separator
    
    # Load environment
    load_env
    
    # Check if running
    if is_running; then
        local pid=$(get_pid)
        print_status "Status: ${GREEN}RUNNING${NC}"
        print_status "Process ID: $pid"
        
        # Get process details
        local process_info=$(get_process_info)
        if [[ -n "$process_info" ]]; then
            echo ""
            print_status "Process Details:"
            echo "  PID    PPID   USER     %CPU %MEM     ETIME CMD"
            echo "  $process_info" | sed 's/^/  /'
        fi
        
        # Memory usage
        local memory=$(get_memory_usage)
        [[ -n "$memory" ]] && print_status "Memory Usage: $memory"
        
        # Network info
        local port="${STREAMLIT_SERVER_PORT:-8081}"
        print_status "Port: $port"
        print_status "URL: $(get_service_url)"
        
        # Check if port is actually listening
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            print_status "Port Status: ${GREEN}LISTENING${NC}"
        else
            print_warning "Port Status: ${YELLOW}NOT LISTENING${NC} (may still be starting)"
        fi
        
        # Log file info
        if [[ -f "$LOG_FILE" ]]; then
            local log_size=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
            local log_lines=$(wc -l < "$LOG_FILE" 2>/dev/null)
            print_status "Log File: $LOG_FILE ($log_size, $log_lines lines)"
            
            # Show last few log lines
            echo ""
            print_status "Recent Log Activity:"
            tail -5 "$LOG_FILE" 2>/dev/null | sed 's/^/  /' || echo "  (no recent activity)"
        fi
        
        # Uptime calculation
        if [[ -n "$process_info" ]]; then
            local etime=$(echo "$process_info" | awk '{print $6}')
            print_status "Uptime: $etime"
        fi
        
    else
        print_status "Status: ${RED}NOT RUNNING${NC}"
        
        # Check for stale PID file
        if [[ -f "$PID_FILE" ]]; then
            print_warning "Stale PID file found: $PID_FILE"
            print_warning "Use 'make start' to start the dashboard"
        fi
        
        # Check if port is in use by something else
        local port="${STREAMLIT_SERVER_PORT:-8081}"
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            print_warning "Port $port is in use by another process:"
            netstat -tuln | grep ":$port " | sed 's/^/  /'
            lsof -i ":$port" 2>/dev/null | sed 's/^/  /' || true
        else
            print_status "Port $port is available"
        fi
        
        # Check recent log activity
        if [[ -f "$LOG_FILE" ]]; then
            local log_modified=$(stat -c %Y "$LOG_FILE" 2>/dev/null)
            local current_time=$(date +%s)
            local age=$((current_time - log_modified))
            
            print_status "Last log activity: $(date -d @$log_modified 2>/dev/null || echo 'unknown')"
            
            if [[ $age -lt 300 ]]; then  # Less than 5 minutes
                print_status "Recent log entries:"
                tail -5 "$LOG_FILE" 2>/dev/null | sed 's/^/  /' || echo "  (no recent activity)"
            fi
        fi
    fi
}

# Show system information
show_system_info() {
    print_separator
    print_status "System Information"
    print_separator
    
    print_status "User: $(whoami)"
    print_status "Working Directory: $PROJECT_ROOT"
    print_status "Virtual Environment: $VENV_PATH"
    
    # Check virtual environment
    if [[ -d "$VENV_PATH" ]]; then
        print_status "Virtual Environment: ${GREEN}EXISTS${NC}"
        if [[ -x "$STREAMLIT" ]]; then
            local streamlit_version=$("$STREAMLIT" --version 2>/dev/null | head -1 || echo "unknown")
            print_status "Streamlit Version: $streamlit_version"
        fi
    else
        print_status "Virtual Environment: ${RED}NOT FOUND${NC}"
        print_warning "Run 'make install' to create it"
    fi
    
    # Check app file
    if [[ -f "$APP_FILE" ]]; then
        print_status "App File: ${GREEN}EXISTS${NC} ($APP_FILE)"
    else
        print_status "App File: ${RED}NOT FOUND${NC} ($APP_FILE)"
    fi
    
    # Check environment file
    if [[ -f "$ENV_FILE" ]]; then
        print_status "Environment File: ${GREEN}EXISTS${NC} ($ENV_FILE)"
    else
        print_status "Environment File: ${YELLOW}NOT FOUND${NC} (using defaults)"
    fi
    
    # Disk space
    local disk_usage=$(df -h "$PROJECT_ROOT" 2>/dev/null | tail -1 | awk '{print $5 " used"}' || echo "unknown")
    print_status "Disk Usage: $disk_usage"
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | xargs || echo "unknown")
    print_status "Load Average: $load_avg"
}

# Show configuration
show_config() {
    print_separator  
    print_status "Configuration"
    print_separator
    
    load_env
    
    print_status "STREAMLIT_SERVER_PORT: ${STREAMLIT_SERVER_PORT:-8081}"
    print_status "STREAMLIT_SERVER_ADDRESS: ${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}"
    print_status "STREAMLIT_BROWSER_GATHER_USAGE_STATS: ${STREAMLIT_BROWSER_GATHER_USAGE_STATS:-false}"
    
    if [[ -n "${PROJECT_ROOT:-}" ]]; then
        print_status "PROJECT_ROOT: $PROJECT_ROOT"
    fi
    if [[ -n "${LOGS_PATH:-}" ]]; then
        print_status "LOGS_PATH: $LOGS_PATH"
    fi
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Show Streamlit Dashboard status information"
        echo ""
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo "  -s, --system   Show system information"
        echo "  -c, --config   Show configuration"
        echo "  -a, --all      Show all information"
        echo "  -v, --verbose  Enable verbose output"
        echo ""
        ;;
    -s|--system)
        show_status
        show_system_info
        ;;
    -c|--config)
        show_status
        show_config
        ;;
    -a|--all)
        show_status
        show_system_info
        show_config
        ;;
    -v|--verbose)
        set -x
        show_status
        ;;
    "")
        show_status
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use -h or --help for usage information"
        exit 1
        ;;
esac