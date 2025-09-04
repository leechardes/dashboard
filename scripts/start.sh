#!/bin/bash
# Start Streamlit Dashboard script

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Main start function
start_dashboard() {
    print_status "Starting Streamlit Dashboard..."
    print_separator
    
    # Load environment variables
    load_env
    
    # Check if already running
    if is_running; then
        print_warning "Dashboard is already running!"
        local pid=$(get_pid)
        print_status "PID: $pid"
        print_status "URL: $(get_service_url)"
        print_status "Use 'make stop' to stop or 'make restart' to restart"
        return 0
    fi
    
    # Check prerequisites
    if ! check_venv; then
        print_error "Virtual environment check failed"
        return 1
    fi
    
    if ! check_app_file; then
        print_error "App file check failed"
        return 1
    fi
    
    # Check if port is available
    local port="${STREAMLIT_SERVER_PORT:-8081}"
    if ! check_port "$port"; then
        print_error "Port $port is already in use"
        print_status "Check what's using the port:"
        netstat -tuln | grep ":$port " || true
        lsof -i ":$port" 2>/dev/null || true
        return 1
    fi
    
    # Ensure log directory exists
    ensure_log_dir
    
    # Clean old logs
    cleanup_logs 7
    
    # Start streamlit in background
    print_status "Starting in background mode..."
    print_debug "Command: $STREAMLIT run $APP_FILE --server.port=$port --server.address=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}"
    
    cd "$PROJECT_ROOT"
    nohup "$STREAMLIT" run "$APP_FILE" \
        --server.port="$port" \
        --server.address="${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}" \
        --browser.gatherUsageStats="${STREAMLIT_BROWSER_GATHER_USAGE_STATS:-false}" \
        > "$LOG_FILE" 2>&1 &
    
    local streamlit_pid=$!
    echo "$streamlit_pid" > "$PID_FILE"
    
    print_status "Waiting for dashboard to start..."
    echo -n "Checking"
    
    if wait_for_process "start" 15; then
        echo ""
        print_status "Dashboard started successfully!"
        print_separator
        
        # Show process info
        local pid=$(get_pid)
        print_status "Process ID: $pid"
        print_status "Port: $port"
        print_status "URL: $(get_service_url)"
        print_status "Log file: $LOG_FILE"
        print_status "Memory usage: $(get_memory_usage)"
        
        print_separator
        print_status "Dashboard is ready!"
        print_status "Access at: $(get_service_url)"
        print_status "Use 'make logs' to view output"
        print_status "Use 'make status' to check status"
        
    else
        echo ""
        print_error "Failed to start dashboard within timeout"
        print_error "Check the log file for details: $LOG_FILE"
        
        # Clean up PID file if process didn't start
        [[ -f "$PID_FILE" ]] && rm -f "$PID_FILE"
        
        # Show recent log entries if available
        if [[ -f "$LOG_FILE" ]]; then
            print_status "Recent log entries:"
            tail -20 "$LOG_FILE" | sed 's/^/  /'
        fi
        
        return 1
    fi
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Start the Streamlit Dashboard in background mode"
        echo ""
        echo "Options:"
        echo "  -h, --help    Show this help message"
        echo "  -v, --verbose Enable verbose output"
        echo ""
        echo "Environment variables:"
        echo "  STREAMLIT_SERVER_PORT     Port to run on (default: 8081)"
        echo "  STREAMLIT_SERVER_ADDRESS  Address to bind to (default: 0.0.0.0)"
        echo ""
        echo "Files:"
        echo "  Config: $ENV_FILE"
        echo "  Logs:   $LOG_FILE"
        echo ""
        ;;
    -v|--verbose)
        set -x
        start_dashboard
        ;;
    "")
        start_dashboard
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use -h or --help for usage information"
        exit 1
        ;;
esac