#!/bin/bash
# Claude Process Notifier - Send alerts to user terminals
# This script monitors Claude processes and sends notifications instead of killing them

# Colors for terminal messages
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
CONFIG_FILE="/srv/projects/shared/dashboard/config/claude_limits.json"
LOG_FILE="/var/log/claude-notifier.log"
CHECK_INTERVAL=300  # Check every 5 minutes

# Load configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        # Extract values from JSON
        MEMORY_LIMIT=$(grep -oP '"memory_limit_mb":\s*\K\d+' "$CONFIG_FILE" | head -1)
        ALERT_HOURS=$(grep -oP '"alert_after_hours":\s*\K\d+' "$CONFIG_FILE" | head -1)
        ALERT_MEMORY=$(grep -oP '"alert_memory_threshold_mb":\s*\K\d+' "$CONFIG_FILE" | head -1)
    else
        # Default values
        MEMORY_LIMIT=8192
        ALERT_HOURS=4
        ALERT_MEMORY=6144
    fi
}

# Send notification to user's terminal
send_terminal_notification() {
    local user=$1
    local message=$2
    local severity=$3  # info, warning, critical
    
    # Get all terminals for the user
    local terminals=$(who | grep "^$user " | awk '{print $2}')
    
    # Prepare the message with formatting
    local formatted_msg=""
    case $severity in
        "critical")
            formatted_msg="${RED}${BOLD}⚠️  CLAUDE ALERT - CRITICAL${NC}\n${message}"
            ;;
        "warning")
            formatted_msg="${YELLOW}${BOLD}⚡ CLAUDE ALERT - WARNING${NC}\n${message}"
            ;;
        "info")
            formatted_msg="${BLUE}${BOLD}ℹ️  CLAUDE NOTICE${NC}\n${message}"
            ;;
        *)
            formatted_msg="${message}"
            ;;
    esac
    
    # Send to each terminal
    for term in $terminals; do
        echo -e "\n${formatted_msg}\n" | write "$user" "$term" 2>/dev/null || true
    done
    
    # Also log the notification
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$severity] User: $user - $message" >> "$LOG_FILE"
}

# Check Claude processes
check_claude_processes() {
    # Get all Claude processes
    ps aux | grep -E 'claude|Claude' | grep -v grep | while read line; do
        local user=$(echo $line | awk '{print $1}')
        local pid=$(echo $line | awk '{print $2}')
        local cpu=$(echo $line | awk '{print $3}')
        local mem_percent=$(echo $line | awk '{print $4}')
        local vsz=$(echo $line | awk '{print $5}')
        local rss=$(echo $line | awk '{print $6}')
        local time=$(echo $line | awk '{print $10}')
        
        # Calculate memory in MB
        local mem_mb=$((rss / 1024))
        
        # Extract hours from runtime
        local hours=0
        if [[ $time =~ ^([0-9]+)- ]]; then
            # Format: DAYS-HH:MM
            hours=$((${BASH_REMATCH[1]} * 24))
        elif [[ $time =~ ^([0-9]+): ]]; then
            # Format: HH:MM or MM:SS
            if [[ ${BASH_REMATCH[1]} -gt 60 ]]; then
                hours=$((${BASH_REMATCH[1]} / 60))
            else
                hours=${BASH_REMATCH[1]}
            fi
        fi
        
        # Check conditions and send appropriate alerts
        
        # 1. Memory Alert
        if [ $mem_mb -gt $ALERT_MEMORY ]; then
            send_terminal_notification "$user" \
                "Your Claude process (PID: $pid) is using ${mem_mb}MB of memory (threshold: ${ALERT_MEMORY}MB).\n\
Consider saving your work and restarting Claude if you experience issues.\n\
To check: ps aux | grep $pid\n\
To restart: kill $pid && claude" \
                "warning"
        fi
        
        # 2. Long-running process alert
        if [ $hours -ge $ALERT_HOURS ]; then
            send_terminal_notification "$user" \
                "Your Claude process (PID: $pid) has been running for ${hours} hours.\n\
Memory usage: ${mem_mb}MB | CPU: ${cpu}%\n\
Consider saving your work. Long-running processes may accumulate memory.\n\
To check: claude-status\n\
To clean old processes: claude-clean" \
                "warning"
        fi
        
        # 3. Critical memory alert (>90% of limit)
        local critical_threshold=$((MEMORY_LIMIT * 90 / 100))
        if [ $mem_mb -gt $critical_threshold ]; then
            send_terminal_notification "$user" \
                "⚠️ CRITICAL: Claude process (PID: $pid) is using ${mem_mb}MB (>90% of ${MEMORY_LIMIT}MB limit)!\n\
The process may crash soon due to memory limits.\n\
SAVE YOUR WORK IMMEDIATELY!\n\
Then restart Claude: kill $pid && claude" \
                "critical"
        fi
        
        # 4. High CPU alert
        if (( $(echo "$cpu > 80" | bc -l) )); then
            send_terminal_notification "$user" \
                "Claude process (PID: $pid) is using high CPU: ${cpu}%\n\
This may slow down the system for other users.\n\
Current memory: ${mem_mb}MB | Runtime: $time" \
                "info"
        fi
    done
}

# Send summary notification to admins
send_admin_summary() {
    local total_processes=$(ps aux | grep -E 'claude|Claude' | grep -v grep | wc -l)
    local total_memory=$(ps aux | grep -E 'claude|Claude' | grep -v grep | awk '{sum+=$6} END {print int(sum/1024)}')
    local users=$(ps aux | grep -E 'claude|Claude' | grep -v grep | awk '{print $1}' | sort -u | wc -l)
    
    # Send to admin users (customize as needed)
    for admin in root devadmin; do
        if who | grep -q "^$admin "; then
            send_terminal_notification "$admin" \
                "Claude System Summary:\n\
• Active processes: $total_processes\n\
• Total memory usage: ${total_memory}MB\n\
• Active users: $users\n\
• Alerts sent in last check cycle\n\
Dashboard: http://$(hostname -I | awk '{print $1}'):8081/claude-manager" \
                "info"
        fi
    done
}

# Main monitoring loop
main() {
    echo "[$(date)] Claude Notifier started" >> "$LOG_FILE"
    
    while true; do
        load_config
        check_claude_processes
        
        # Send admin summary every hour
        if [ $(($(date +%M) % 60)) -eq 0 ]; then
            send_admin_summary
        fi
        
        sleep $CHECK_INTERVAL
    done
}

# Handle script termination
trap 'echo "[$(date)] Claude Notifier stopped" >> "$LOG_FILE"; exit 0' SIGINT SIGTERM

# Check if running as service or standalone
if [ "$1" == "test" ]; then
    # Test mode - run once and exit
    echo "Running in test mode..."
    load_config
    check_claude_processes
    echo "Test complete. Check $LOG_FILE for details."
elif [ "$1" == "notify" ]; then
    # Manual notification
    if [ $# -lt 4 ]; then
        echo "Usage: $0 notify <user> <severity> <message>"
        echo "Severity: info, warning, critical"
        exit 1
    fi
    send_terminal_notification "$2" "$4" "$3"
else
    # Normal daemon mode
    main
fi