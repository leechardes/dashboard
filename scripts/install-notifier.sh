#!/bin/bash
# Install Claude Notifier Service

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}📦 Installing Claude Notifier Service${NC}"
echo "This service sends alerts instead of killing processes"
echo

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run with sudo: sudo $0${NC}"
    exit 1
fi

# Copy service file
echo "1. Installing service file..."
cp /srv/projects/shared/dashboard/systemd/claude-notifier.service /etc/systemd/system/
chmod 644 /etc/systemd/system/claude-notifier.service

# Create log file
echo "2. Creating log file..."
touch /var/log/claude-notifier.log
touch /var/log/claude-notifier.error.log
chmod 666 /var/log/claude-notifier.log
chmod 666 /var/log/claude-notifier.error.log

# Reload systemd
echo "3. Reloading systemd..."
systemctl daemon-reload

# Enable service
echo "4. Enabling service..."
systemctl enable claude-notifier.service

# Start service
echo "5. Starting service..."
systemctl start claude-notifier.service

# Check status
echo "6. Checking status..."
if systemctl is-active --quiet claude-notifier.service; then
    echo -e "${GREEN}✅ Claude Notifier is running!${NC}"
else
    echo -e "${RED}❌ Failed to start Claude Notifier${NC}"
    systemctl status claude-notifier.service
    exit 1
fi

echo
echo -e "${GREEN}✨ Installation Complete!${NC}"
echo
echo "📋 Useful commands:"
echo "  systemctl status claude-notifier    # Check status"
echo "  systemctl stop claude-notifier      # Stop notifier"
echo "  systemctl start claude-notifier     # Start notifier"
echo "  journalctl -u claude-notifier -f    # View logs"
echo "  tail -f /var/log/claude-notifier.log # View notification log"
echo
echo "🔧 Test notification:"
echo "  /srv/projects/shared/dashboard/scripts/claude-notifier.sh test"
echo
echo "📨 Send manual notification:"
echo "  /srv/projects/shared/dashboard/scripts/claude-notifier.sh notify <user> <severity> <message>"
echo
echo -e "${YELLOW}⚠️  Note: Alerts will be sent to user terminals instead of killing processes${NC}"