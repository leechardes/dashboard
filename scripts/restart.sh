#!/bin/bash
# Restart Streamlit Dashboard script

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Main restart function
restart_dashboard() {
    print_status "Restarting Streamlit Dashboard..."
    print_separator
    
    local was_running=false
    if is_running; then
        was_running=true
        print_status "Dashboard is currently running"
    else
        print_status "Dashboard is not running"
    fi
    
    # Stop the dashboard
    print_status "Step 1/3: Stopping dashboard..."
    "$SCRIPT_DIR/stop.sh" || {
        print_error "Failed to stop dashboard"
        return 1
    }
    
    # Wait a moment for cleanup
    print_status "Step 2/3: Waiting for cleanup..."
    sleep 2
    
    # Start the dashboard
    print_status "Step 3/3: Starting dashboard..."
    "$SCRIPT_DIR/start.sh" || {
        print_error "Failed to start dashboard"
        return 1
    }
    
    print_separator
    if [[ "$was_running" == true ]]; then
        print_status "Dashboard restarted successfully!"
    else
        print_status "Dashboard started successfully!"
    fi
    
    # Show final status
    if is_running; then
        local pid=$(get_pid)
        print_status "Process ID: $pid"
        print_status "URL: $(get_service_url)"
        print_status "Memory usage: $(get_memory_usage)"
    fi
}

# Quick restart function (for faster restarts)
quick_restart_dashboard() {
    print_status "Quick restarting Streamlit Dashboard..."
    print_separator
    
    # Force stop without waiting
    local pid=$(get_pid)
    if [[ -n "$pid" ]]; then
        print_status "Force stopping process $pid"
        kill -KILL "$pid" 2>/dev/null || true
        pkill -KILL -f "streamlit run.*app.py" 2>/dev/null || true
        [[ -f "$PID_FILE" ]] && rm -f "$PID_FILE"
    fi
    
    # Start immediately
    print_status "Starting dashboard..."
    "$SCRIPT_DIR/start.sh" || {
        print_error "Failed to start dashboard"
        return 1
    }
    
    print_separator
    print_status "Quick restart completed!"
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Restart the Streamlit Dashboard"
        echo ""
        echo "Options:"
        echo "  -h, --help    Show this help message"
        echo "  -q, --quick   Quick restart (force kill + immediate start)"
        echo "  -v, --verbose Enable verbose output"
        echo ""
        echo "The default behavior is to gracefully stop and then start."
        echo "Quick restart forces immediate termination for faster restart."
        echo ""
        ;;
    -q|--quick)
        quick_restart_dashboard
        ;;
    -v|--verbose)
        set -x
        restart_dashboard
        ;;
    -qv|--quick-verbose)
        set -x
        quick_restart_dashboard
        ;;
    "")
        restart_dashboard
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use -h or --help for usage information"
        exit 1
        ;;
esac