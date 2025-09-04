#!/bin/bash
# Logs viewer script for Streamlit Dashboard

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Show logs
show_logs() {
    local lines="${1:-50}"
    local follow="${2:-false}"
    local filter="${3:-}"
    
    print_status "Streamlit Dashboard Logs"
    print_separator
    
    if [[ ! -f "$LOG_FILE" ]]; then
        print_warning "Log file not found: $LOG_FILE"
        print_status "Dashboard might not be running or hasn't been started yet"
        print_status "Use 'make start' to start the dashboard"
        return 1
    fi
    
    # Show log file info
    local log_size=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
    local log_lines=$(wc -l < "$LOG_FILE" 2>/dev/null)
    local log_modified=$(stat -c %Y "$LOG_FILE" 2>/dev/null)
    
    print_status "Log file: $LOG_FILE"
    print_status "Size: $log_size ($log_lines lines)"
    print_status "Modified: $(date -d @$log_modified 2>/dev/null || echo 'unknown')"
    
    if [[ -n "$filter" ]]; then
        print_status "Filter: $filter"
    fi
    
    print_separator
    
    # Show logs
    if [[ "$follow" == true ]]; then
        print_status "Following logs (Ctrl+C to exit)..."
        echo ""
        
        if [[ -n "$filter" ]]; then
            tail -f "$LOG_FILE" | grep --line-buffered "$filter"
        else
            tail -f "$LOG_FILE"
        fi
    else
        if [[ -n "$filter" ]]; then
            if [[ "$lines" == "all" ]]; then
                grep "$filter" "$LOG_FILE"
            else
                grep "$filter" "$LOG_FILE" | tail -n "$lines"
            fi
        else
            if [[ "$lines" == "all" ]]; then
                cat "$LOG_FILE"
            else
                tail -n "$lines" "$LOG_FILE"
            fi
        fi
    fi
}

# Show error logs only
show_error_logs() {
    local lines="${1:-20}"
    
    print_status "Error Logs Only"
    print_separator
    
    if [[ ! -f "$LOG_FILE" ]]; then
        print_warning "Log file not found: $LOG_FILE"
        return 1
    fi
    
    # Common error patterns
    local error_patterns="ERROR|Error|Exception|Traceback|CRITICAL|FATAL|Failed|failed"
    
    print_status "Showing last $lines error entries..."
    print_separator
    
    grep -E "$error_patterns" "$LOG_FILE" | tail -n "$lines" || {
        print_status "No error entries found in logs"
    }
}

# Show logs with timestamps
show_timestamped_logs() {
    local lines="${1:-50}"
    local follow="${2:-false}"
    
    print_status "Timestamped Logs"
    print_separator
    
    if [[ ! -f "$LOG_FILE" ]]; then
        print_warning "Log file not found: $LOG_FILE"
        return 1
    fi
    
    if [[ "$follow" == true ]]; then
        print_status "Following timestamped logs (Ctrl+C to exit)..."
        echo ""
        tail -f "$LOG_FILE" | while read -r line; do
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line"
        done
    else
        tail -n "$lines" "$LOG_FILE" | while read -r line; do
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line"
        done
    fi
}

# Analyze logs for common issues
analyze_logs() {
    print_status "Log Analysis"
    print_separator
    
    if [[ ! -f "$LOG_FILE" ]]; then
        print_warning "Log file not found: $LOG_FILE"
        return 1
    fi
    
    local total_lines=$(wc -l < "$LOG_FILE")
    local error_count=$(grep -c -E "ERROR|Error|Exception|CRITICAL|FATAL" "$LOG_FILE" 2>/dev/null || echo "0")
    local warning_count=$(grep -c -E "WARNING|Warning|WARN" "$LOG_FILE" 2>/dev/null || echo "0")
    
    print_status "Total log entries: $total_lines"
    print_status "Error entries: $error_count"
    print_status "Warning entries: $warning_count"
    
    if [[ $error_count -gt 0 ]]; then
        echo ""
        print_warning "Recent errors found:"
        print_separator
        grep -E "ERROR|Error|Exception|CRITICAL|FATAL" "$LOG_FILE" | tail -5 | sed 's/^/  /'
    fi
    
    if [[ $warning_count -gt 0 ]]; then
        echo ""
        print_warning "Recent warnings found:"
        print_separator
        grep -E "WARNING|Warning|WARN" "$LOG_FILE" | tail -3 | sed 's/^/  /'
    fi
    
    # Check for startup messages
    echo ""
    print_status "Startup information:"
    print_separator
    grep -E "You can now view|Network URL|External URL|server.port" "$LOG_FILE" | tail -3 | sed 's/^/  /' || {
        echo "  No startup messages found"
    }
}

# Show log statistics by time
show_log_stats() {
    print_status "Log Statistics"
    print_separator
    
    if [[ ! -f "$LOG_FILE" ]]; then
        print_warning "Log file not found: $LOG_FILE"
        return 1
    fi
    
    # Basic stats
    local file_size=$(du -h "$LOG_FILE" | cut -f1)
    local line_count=$(wc -l < "$LOG_FILE")
    local word_count=$(wc -w < "$LOG_FILE")
    
    print_status "File size: $file_size"
    print_status "Lines: $line_count"
    print_status "Words: $word_count"
    
    # Error/warning counts
    local errors=$(grep -c -E "ERROR|Error|Exception|CRITICAL|FATAL" "$LOG_FILE" 2>/dev/null || echo "0")
    local warnings=$(grep -c -E "WARNING|Warning|WARN" "$LOG_FILE" 2>/dev/null || echo "0")
    local info=$(grep -c -E "INFO|Info" "$LOG_FILE" 2>/dev/null || echo "0")
    
    echo ""
    print_status "Message levels:"
    print_status "  Errors: $errors"
    print_status "  Warnings: $warnings"
    print_status "  Info: $info"
    
    # File timestamps
    local created=$(stat -c %W "$LOG_FILE" 2>/dev/null || stat -c %Y "$LOG_FILE" 2>/dev/null)
    local modified=$(stat -c %Y "$LOG_FILE" 2>/dev/null)
    
    echo ""
    print_status "Timestamps:"
    print_status "  Created: $(date -d @$created 2>/dev/null || echo 'unknown')"
    print_status "  Modified: $(date -d @$modified 2>/dev/null || echo 'unknown')"
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [OPTIONS] [LINES]"
        echo ""
        echo "View Streamlit Dashboard logs"
        echo ""
        echo "Options:"
        echo "  -h, --help         Show this help message"
        echo "  -f, --follow       Follow logs in real-time"
        echo "  -e, --errors       Show only error messages"
        echo "  -t, --timestamp    Add timestamps to output"
        echo "  -a, --analyze      Analyze logs for issues"
        echo "  -s, --stats        Show log statistics"
        echo "  --filter PATTERN   Filter logs by pattern"
        echo ""
        echo "Examples:"
        echo "  $0                 Show last 50 lines"
        echo "  $0 100             Show last 100 lines"
        echo "  $0 -f              Follow logs"
        echo "  $0 -e              Show errors only"
        echo "  $0 --filter ERROR  Show lines containing 'ERROR'"
        echo ""
        ;;
    -f|--follow)
        show_logs 50 true
        ;;
    -e|--errors)
        show_error_logs "${2:-20}"
        ;;
    -t|--timestamp)
        show_timestamped_logs "${2:-50}"
        ;;
    -tf|--timestamp-follow)
        show_timestamped_logs 50 true
        ;;
    -a|--analyze)
        analyze_logs
        ;;
    -s|--stats)
        show_log_stats
        ;;
    --filter)
        if [[ -z "${2:-}" ]]; then
            print_error "Filter pattern required"
            exit 1
        fi
        show_logs "${3:-50}" false "$2"
        ;;
    --filter-follow)
        if [[ -z "${2:-}" ]]; then
            print_error "Filter pattern required"
            exit 1
        fi
        show_logs 50 true "$2"
        ;;
    "")
        show_logs 50
        ;;
    [0-9]*)
        show_logs "$1"
        ;;
    all)
        show_logs all
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use -h or --help for usage information"
        exit 1
        ;;
esac