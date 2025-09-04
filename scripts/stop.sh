#!/bin/bash
# Stop Streamlit Dashboard script

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Main stop function
stop_dashboard() {
    print_status "Stopping Streamlit Dashboard..."
    print_separator
    
    # Check if running
    if ! is_running; then
        print_warning "Dashboard is not running"
        # Clean up stale PID file if it exists
        [[ -f "$PID_FILE" ]] && rm -f "$PID_FILE"
        return 0
    fi
    
    local pid=$(get_pid)
    print_status "Found running dashboard (PID: $pid)"
    
    # Show process info before stopping
    print_debug "Process details:"
    get_process_info | sed 's/^/  /'
    
    # Try graceful shutdown first (SIGTERM)
    print_status "Sending SIGTERM signal..."
    kill -TERM "$pid" 2>/dev/null || {
        print_error "Failed to send SIGTERM to process $pid"
        return 1
    }
    
    # Wait for graceful shutdown
    print_status "Waiting for graceful shutdown..."
    echo -n "Checking"
    
    if wait_for_process "stop" 10; then
        echo ""
        print_status "Dashboard stopped gracefully"
    else
        echo ""
        print_warning "Graceful shutdown timed out, forcing termination..."
        
        # Force kill if still running
        if is_running; then
            print_status "Sending SIGKILL signal..."
            kill -KILL "$pid" 2>/dev/null || {
                print_error "Failed to force kill process $pid"
                return 1
            }
            
            # Final check
            sleep 2
            if is_running; then
                print_error "Process is still running after SIGKILL"
                return 1
            else
                print_warning "Dashboard forcefully terminated"
            fi
        fi
    fi
    
    # Clean up PID file
    [[ -f "$PID_FILE" ]] && rm -f "$PID_FILE"
    
    # Kill any remaining streamlit processes (cleanup)
    pkill -f "streamlit run.*app.py" 2>/dev/null || true
    
    print_separator
    print_status "Dashboard stopped successfully"
    
    # Show log file location for reference
    if [[ -f "$LOG_FILE" ]]; then
        print_status "Log file available at: $LOG_FILE"
        print_status "Use 'make logs' to view recent activity"
    fi
}

# Force stop function (immediate SIGKILL)
force_stop_dashboard() {
    print_warning "Force stopping dashboard..."
    print_separator
    
    local pid=$(get_pid)
    if [[ -n "$pid" ]]; then
        print_status "Force killing process $pid"
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    # Kill all streamlit processes
    pkill -KILL -f "streamlit run.*app.py" 2>/dev/null || true
    
    # Clean up PID file
    [[ -f "$PID_FILE" ]] && rm -f "$PID_FILE"
    
    # Wait a moment and verify
    sleep 1
    if is_running; then
        print_error "Some processes may still be running"
        return 1
    else
        print_status "All processes terminated"
    fi
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Stop the Streamlit Dashboard"
        echo ""
        echo "Options:"
        echo "  -h, --help    Show this help message"
        echo "  -f, --force   Force immediate termination (SIGKILL)"
        echo "  -v, --verbose Enable verbose output"
        echo ""
        echo "The default behavior is to try graceful shutdown first (SIGTERM)"
        echo "and then force kill if the process doesn't stop within 10 seconds."
        echo ""
        ;;
    -f|--force)
        force_stop_dashboard
        ;;
    -v|--verbose)
        set -x
        stop_dashboard
        ;;
    -fv|--force-verbose)
        set -x
        force_stop_dashboard
        ;;
    "")
        stop_dashboard
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use -h or --help for usage information"
        exit 1
        ;;
esac