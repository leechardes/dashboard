#!/bin/bash
# Common functions for Streamlit Dashboard scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="/srv/projects/shared/dashboard"
VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON="$VENV_PATH/bin/python"
PIP="$VENV_PATH/bin/pip"
STREAMLIT="$VENV_PATH/bin/streamlit"
APP_FILE="$PROJECT_ROOT/app.py"
ENV_FILE="$PROJECT_ROOT/.env"
LOG_FILE="$PROJECT_ROOT/streamlit.log"
PID_FILE="$PROJECT_ROOT/streamlit.pid"

# Print functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

print_separator() {
    echo "=================================================="
}

# Check if running as correct user
check_permissions() {
    local required_user="${1:-devadmin}"
    if [[ "$(whoami)" != "$required_user" ]]; then
        print_error "This script should be run as user: $required_user"
        print_error "Current user: $(whoami)"
        return 1
    fi
    return 0
}

# Get PID of running streamlit process
get_pid() {
    pgrep -f "streamlit run.*app.py" | head -1
}

# Check if streamlit is running
is_running() {
    local pid=$(get_pid)
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

# Load environment variables
load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        # Export variables from .env file, ignoring comments and empty lines
        set -a
        source "$ENV_FILE"
        set +a
        print_debug "Environment loaded from $ENV_FILE"
    else
        print_warning "Environment file not found: $ENV_FILE"
        # Set default values
        export STREAMLIT_SERVER_PORT=8081
        export STREAMLIT_SERVER_ADDRESS=0.0.0.0
        export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    fi
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -d "$VENV_PATH" ]]; then
        print_error "Virtual environment not found: $VENV_PATH"
        print_error "Run 'make install' first to create it"
        return 1
    fi
    
    if [[ ! -x "$STREAMLIT" ]]; then
        print_error "Streamlit not found in virtual environment"
        print_error "Run 'make install' to reinstall dependencies"
        return 1
    fi
    
    return 0
}

# Wait for process to start/stop
wait_for_process() {
    local action="$1"  # "start" or "stop"
    local timeout="${2:-10}"
    local count=0
    
    while [[ $count -lt $timeout ]]; do
        if [[ "$action" == "start" ]]; then
            if is_running; then
                return 0
            fi
        else
            if ! is_running; then
                return 0
            fi
        fi
        
        sleep 1
        ((count++))
        echo -n "."
    done
    
    echo ""
    return 1
}

# Get process info
get_process_info() {
    local pid=$(get_pid)
    if [[ -n "$pid" ]]; then
        ps -p "$pid" -o pid,ppid,user,cpu,pmem,etime,cmd --no-headers 2>/dev/null
    fi
}

# Get memory usage
get_memory_usage() {
    local pid=$(get_pid)
    if [[ -n "$pid" ]]; then
        ps -p "$pid" -o rss --no-headers 2>/dev/null | awk '{printf "%.1f MB\n", $1/1024}'
    fi
}

# Check port availability
check_port() {
    local port="${1:-$STREAMLIT_SERVER_PORT}"
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 1  # Port is in use
    fi
    return 0  # Port is available
}

# Get service URL
get_service_url() {
    local port="${STREAMLIT_SERVER_PORT:-8081}"
    local address="${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}"
    
    if [[ "$address" == "0.0.0.0" ]]; then
        echo "http://localhost:$port"
    else
        echo "http://$address:$port"
    fi
}

# Validate app file exists
check_app_file() {
    if [[ ! -f "$APP_FILE" ]]; then
        print_error "App file not found: $APP_FILE"
        return 1
    fi
    return 0
}

# Create log directory if needed
ensure_log_dir() {
    local log_dir=$(dirname "$LOG_FILE")
    if [[ ! -d "$log_dir" ]]; then
        mkdir -p "$log_dir" 2>/dev/null || {
            print_warning "Could not create log directory: $log_dir"
            LOG_FILE="/tmp/streamlit-dashboard.log"
            print_warning "Using temporary log file: $LOG_FILE"
        }
    fi
}

# Clean old log files
cleanup_logs() {
    local max_age_days="${1:-7}"
    find "$(dirname "$LOG_FILE")" -name "streamlit*.log*" -mtime +$max_age_days -delete 2>/dev/null || true
}

# Show help for common functions
show_help() {
    cat << 'EOF'
Common functions available:
  print_status()    - Print green info message
  print_error()     - Print red error message  
  print_warning()   - Print yellow warning message
  print_debug()     - Print blue debug message
  check_permissions() - Verify correct user
  get_pid()         - Get streamlit process PID
  is_running()      - Check if streamlit is running
  load_env()        - Load environment variables
  check_venv()      - Verify virtual environment
  wait_for_process() - Wait for start/stop
  get_process_info() - Get process details
  get_memory_usage() - Get memory usage
  check_port()      - Check if port is available
  get_service_url() - Get service URL
  check_app_file()  - Verify app file exists
  ensure_log_dir()  - Create log directory
  cleanup_logs()    - Remove old log files
EOF
}

# Export functions for use in other scripts
export -f print_status print_error print_warning print_debug print_separator
export -f check_permissions get_pid is_running load_env check_venv
export -f wait_for_process get_process_info get_memory_usage check_port
export -f get_service_url check_app_file ensure_log_dir cleanup_logs show_help