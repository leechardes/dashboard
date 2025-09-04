#!/bin/bash

# Streamlit Dashboard Runner Script
# This script provides an alternative way to run the dashboard

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"
APP_FILE="$SCRIPT_DIR/app.py"
PORT=${STREAMLIT_SERVER_PORT:-8082}

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_status "Checking requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check virtual environment
    if [[ ! -d "$VENV_PATH" ]]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_error "Please run: make install"
        exit 1
    fi
    
    # Check app file
    if [[ ! -f "$APP_FILE" ]]; then
        print_error "App file not found at $APP_FILE"
        exit 1
    fi
    
    print_status "Requirements check passed!"
}

check_port() {
    if netstat -tuln 2>/dev/null | grep ":$PORT " > /dev/null; then
        print_warning "Port $PORT is already in use!"
        print_warning "Use a different port or stop the existing service"
        
        # Try to identify what's using the port
        if command -v lsof &> /dev/null; then
            print_status "Process using port $PORT:"
            lsof -i :$PORT 2>/dev/null || echo "Unable to identify process"
        fi
        
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

start_dashboard() {
    print_status "Starting Streamlit Dashboard..."
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Load environment variables
    if [[ -f ".env" ]]; then
        print_status "Loading environment variables from .env"
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Start Streamlit
    print_status "Starting on port $PORT..."
    print_status "Access the dashboard at: http://localhost:$PORT"
    print_status "Press Ctrl+C to stop"
    
    exec "$VENV_PATH/bin/streamlit" run "$APP_FILE" \
        --server.port="$PORT" \
        --server.address="0.0.0.0" \
        --browser.gatherUsageStats=false
}

start_background() {
    print_status "Starting Streamlit Dashboard in background..."
    
    # Check if already running
    if pgrep -f "streamlit run app.py" > /dev/null; then
        print_warning "Dashboard appears to be already running!"
        print_status "Use './run.sh status' to check or './run.sh stop' to stop"
        exit 1
    fi
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Load environment variables
    if [[ -f ".env" ]]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Start in background
    nohup "$VENV_PATH/bin/streamlit" run "$APP_FILE" \
        --server.port="$PORT" \
        --server.address="0.0.0.0" \
        --browser.gatherUsageStats=false \
        > streamlit.log 2>&1 &
    
    STREAMLIT_PID=$!
    sleep 3
    
    # Check if it started successfully
    if kill -0 $STREAMLIT_PID 2>/dev/null; then
        print_status "Dashboard started successfully in background!"
        print_status "PID: $STREAMLIT_PID"
        print_status "Access at: http://localhost:$PORT"
        print_status "Logs: tail -f $SCRIPT_DIR/streamlit.log"
        echo $STREAMLIT_PID > .streamlit_pid
    else
        print_error "Failed to start dashboard. Check logs:"
        print_error "tail $SCRIPT_DIR/streamlit.log"
        exit 1
    fi
}

stop_dashboard() {
    print_status "Stopping Streamlit Dashboard..."
    
    if pgrep -f "streamlit run app.py" > /dev/null; then
        pkill -f "streamlit run app.py"
        print_status "Dashboard stopped successfully!"
        
        # Remove PID file if exists
        if [[ -f ".streamlit_pid" ]]; then
            rm .streamlit_pid
        fi
    else
        print_warning "Dashboard is not running"
    fi
}

show_status() {
    print_status "Streamlit Dashboard Status"
    echo "=========================="
    
    if pgrep -f "streamlit run app.py" > /dev/null; then
        echo -e "${GREEN}Status: RUNNING${NC}"
        echo -e "${GREEN}PID: $(pgrep -f 'streamlit run app.py')${NC}"
        echo -e "${GREEN}Port: $PORT${NC}"
        echo -e "${GREEN}URL: http://localhost:$PORT${NC}"
        echo ""
        echo "Process details:"
        ps aux | grep "streamlit run app.py" | grep -v grep
    else
        echo -e "${RED}Status: NOT RUNNING${NC}"
        echo "Use './run.sh start' or './run.sh background' to start"
    fi
}

show_logs() {
    if [[ -f "$SCRIPT_DIR/streamlit.log" ]]; then
        print_status "Showing dashboard logs (Ctrl+C to exit):"
        tail -f "$SCRIPT_DIR/streamlit.log"
    else
        print_warning "No log file found."
        print_warning "Dashboard might not be running in background mode."
    fi
}

show_help() {
    echo "Streamlit Dashboard Runner"
    echo "========================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start dashboard in foreground (default)"
    echo "  background  Start dashboard in background"
    echo "  stop        Stop the dashboard"
    echo "  restart     Restart the dashboard"
    echo "  status      Show dashboard status"
    echo "  logs        Show dashboard logs (background mode only)"
    echo "  help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  STREAMLIT_SERVER_PORT  Port number (default: 8082)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start in foreground"
    echo "  $0 background         # Start in background"
    echo "  $0 status             # Check if running"
    echo "  PORT=8083 $0 start   # Use custom port"
    echo ""
}

# Main script logic
case "${1:-start}" in
    "start")
        check_requirements
        check_port
        start_dashboard
        ;;
    "background"|"bg")
        check_requirements
        check_port
        start_background
        ;;
    "stop")
        stop_dashboard
        ;;
    "restart")
        stop_dashboard
        sleep 2
        check_requirements
        check_port
        start_background
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac