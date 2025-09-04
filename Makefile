# Makefile for Streamlit Dashboard

# Variables
VENV_PATH = .venv
PYTHON = $(VENV_PATH)/bin/python
PIP = $(VENV_PATH)/bin/pip
STREAMLIT = $(VENV_PATH)/bin/streamlit
APP_FILE = app.py
PORT = 8081

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help install clean start stop restart dev status logs test update backup
.PHONY: install-service uninstall-service enable-service disable-service service-status service-logs
.PHONY: install-notifier uninstall-notifier notifier-status notifier-test

# Default target
help:
	@echo "$(GREEN)Streamlit Dashboard - Makefile Help$(NC)"
	@echo "======================================"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "$(YELLOW)Basic Management:$(NC)"
	@echo "  $(YELLOW)install$(NC)   - Create virtual environment and install dependencies"
	@echo "  $(YELLOW)clean$(NC)     - Remove virtual environment and cache files"
	@echo "  $(YELLOW)start$(NC)     - Start the dashboard in background"
	@echo "  $(YELLOW)stop$(NC)      - Stop the running dashboard"
	@echo "  $(YELLOW)restart$(NC)   - Restart the dashboard"
	@echo "  $(YELLOW)dev$(NC)       - Run dashboard in development mode"
	@echo "  $(YELLOW)status$(NC)    - Check if dashboard is running"
	@echo "  $(YELLOW)logs$(NC)      - Show dashboard logs"
	@echo ""
	@echo "$(YELLOW)System Service:$(NC)"
	@echo "  $(YELLOW)install-service$(NC) - Install as systemd service"
	@echo "  $(YELLOW)uninstall-service$(NC) - Remove systemd service"
	@echo "  $(YELLOW)enable-service$(NC) - Enable auto-start on boot"
	@echo "  $(YELLOW)disable-service$(NC) - Disable auto-start"
	@echo "  $(YELLOW)service-status$(NC) - Check service status"
	@echo "  $(YELLOW)service-logs$(NC) - View service logs"
	@echo "  $(YELLOW)service-start$(NC) - Start service"
	@echo "  $(YELLOW)service-stop$(NC) - Stop service"
	@echo "  $(YELLOW)service-restart$(NC) - Restart service"
	@echo ""
	@echo "$(YELLOW)Claude Notifier:$(NC)"
	@echo "  $(YELLOW)install-notifier$(NC) - Install alert notification service"
	@echo "  $(YELLOW)uninstall-notifier$(NC) - Remove notification service"
	@echo "  $(YELLOW)notifier-status$(NC) - Check notifier status"
	@echo "  $(YELLOW)notifier-test$(NC) - Test notifications"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  $(YELLOW)test$(NC)      - Run basic tests"
	@echo "  $(YELLOW)update$(NC)    - Update dependencies"
	@echo "  $(YELLOW)backup$(NC)    - Create backup of the project"
	@echo ""

# Install dependencies
install:
	@echo "$(GREEN)Installing Streamlit Dashboard...$(NC)"
	@if [ -d "$(VENV_PATH)" ]; then \
		echo "$(YELLOW)Virtual environment already exists. Removing...$(NC)"; \
		rm -rf $(VENV_PATH); \
	fi
	@echo "$(YELLOW)Creating virtual environment...$(NC)"
	python3 -m venv $(VENV_PATH)
	@echo "$(YELLOW)Upgrading pip...$(NC)"
	$(PIP) install --upgrade pip
	@echo "$(YELLOW)Installing requirements...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Installation completed!$(NC)"
	@echo "$(GREEN)You can now run: make start$(NC)"

# Clean up
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf $(VENV_PATH)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "$(GREEN)Cleanup completed!$(NC)"

# Start in background
start:
	@echo "🚀 Starting dashboard..."
	@bash scripts/start.sh

# Stop dashboard
stop:
	@echo "⏹️ Stopping dashboard..."
	@bash scripts/stop.sh

# Restart dashboard
restart:
	@echo "🔄 Restarting dashboard..."
	@bash scripts/restart.sh

# Development mode (foreground)
dev:
	@echo "$(GREEN)Starting Streamlit Dashboard in development mode...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make install' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Access at: http://localhost:$(PORT)$(NC)"
	$(STREAMLIT) run $(APP_FILE) --server.port=$(PORT) --server.address=0.0.0.0

# Check status
status:
	@echo "📊 Dashboard status..."
	@bash scripts/status.sh

# Show logs
logs:
	@echo "📋 Showing logs..."
	@bash scripts/logs.sh

# Basic tests
test:
	@echo "$(GREEN)Running basic tests...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make install' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Testing Python syntax...$(NC)"
	$(PYTHON) -m py_compile $(APP_FILE)
	$(PYTHON) -m py_compile views/*.py
	$(PYTHON) -m py_compile components/*.py
	$(PYTHON) -m py_compile utils/*.py
	@echo "$(YELLOW)Testing imports...$(NC)"
	$(PYTHON) -c "import streamlit; print('✓ Streamlit OK')"
	$(PYTHON) -c "import pandas; print('✓ Pandas OK')"
	$(PYTHON) -c "import plotly; print('✓ Plotly OK')"
	$(PYTHON) -c "import psutil; print('✓ psutil OK')"
	@echo "$(GREEN)All tests passed!$(NC)"

# Update dependencies
update:
	@echo "$(GREEN)Updating dependencies...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make install' first.$(NC)"; \
		exit 1; \
	fi
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements.txt
	@echo "$(GREEN)Dependencies updated!$(NC)"

# Create backup
backup:
	@echo "$(GREEN)Creating backup...$(NC)"
	@BACKUP_NAME="streamlit-dashboard-backup-$$(date +%Y%m%d_%H%M%S).tar.gz"; \
	tar --exclude=$(VENV_PATH) --exclude="*.log" --exclude="__pycache__" \
		-czf "$$BACKUP_NAME" .; \
	echo "$(GREEN)Backup created: $$BACKUP_NAME$(NC)"

# Show port usage
port-check:
	@echo "$(GREEN)Checking port $(PORT) usage...$(NC)"
	@if netstat -tuln 2>/dev/null | grep ":$(PORT) " > /dev/null; then \
		echo "$(YELLOW)Port $(PORT) is in use:$(NC)"; \
		netstat -tuln | grep ":$(PORT) "; \
		lsof -i :$(PORT) 2>/dev/null || echo "Use 'sudo lsof -i :$(PORT)' for process details"; \
	else \
		echo "$(GREEN)Port $(PORT) is available$(NC)"; \
	fi

# Quick setup (install + start)
setup: install start
	@echo "$(GREEN)Setup completed! Dashboard is running at http://localhost:$(PORT)$(NC)"

# Show system info
info:
	@echo "$(GREEN)System Information$(NC)"
	@echo "=================="
	@echo "Python: $$(python3 --version)"
	@echo "pip: $$(python3 -m pip --version)"
	@echo "Virtual env: $(VENV_PATH)"
	@echo "Port: $(PORT)"
	@echo "Working directory: $$(pwd)"
	@echo "User: $$(whoami)"
	@echo "Host: $$(hostname)"

# Development dependencies (optional)
dev-install: install
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	$(PIP) install flake8 black isort pytest
	@echo "$(GREEN)Development environment ready!$(NC)"

# Format code (requires dev-install)
format:
	@echo "$(YELLOW)Formatting code...$(NC)"
	@if [ -d "$(VENV_PATH)" ] && [ -f "$(VENV_PATH)/bin/black" ]; then \
		$(VENV_PATH)/bin/black .; \
		$(VENV_PATH)/bin/isort .; \
		echo "$(GREEN)Code formatted!$(NC)"; \
	else \
		echo "$(RED)Development tools not installed. Run 'make dev-install' first.$(NC)"; \
	fi

# Lint code (requires dev-install)
lint:
	@echo "$(YELLOW)Linting code...$(NC)"
	@if [ -d "$(VENV_PATH)" ] && [ -f "$(VENV_PATH)/bin/flake8" ]; then \
		$(VENV_PATH)/bin/flake8 --max-line-length=100 .; \
		echo "$(GREEN)Linting completed!$(NC)"; \
	else \
		echo "$(RED)Development tools not installed. Run 'make dev-install' first.$(NC)"; \
	fi

# ============================================================================
# SYSTEMD SERVICE MANAGEMENT
# ============================================================================

# Install and configure systemd service
install-service:
	@echo "📦 Installing systemd service..."
	@sudo bash scripts/install-service.sh

# Uninstall systemd service
uninstall-service:
	@echo "🗑️ Removing systemd service..."
	@sudo bash scripts/uninstall-service.sh

# Enable auto-start on boot
enable-service:
	@echo "✅ Enabling auto-start..."
	@sudo systemctl enable streamlit-dashboard

# Disable auto-start on boot
disable-service:
	@echo "❌ Disabling auto-start..."
	@sudo systemctl disable streamlit-dashboard

# Check systemd service status
service-status:
	@echo "📊 Service status..."
	@sudo systemctl status streamlit-dashboard --no-pager

# View systemd service logs
service-logs:
	@echo "📋 Service logs..."
	@sudo journalctl -u streamlit-dashboard -f

# Start systemd service
service-start:
	@echo "🚀 Starting service..."
	@sudo systemctl start streamlit-dashboard

# Stop systemd service
service-stop:
	@echo "⏹️ Stopping service..."
	@sudo systemctl stop streamlit-dashboard

# Restart systemd service
service-restart:
	@echo "🔄 Restarting service..."
	@sudo systemctl restart streamlit-dashboard

# ============================================================================
# CLAUDE NOTIFIER SERVICE
# ============================================================================

# Install Claude Notifier service
install-notifier:
	@echo "📦 Installing Claude Notifier service..."
	@echo "This will send alerts to terminals instead of killing processes"
	@sudo bash scripts/install-notifier.sh

# Uninstall Claude Notifier service
uninstall-notifier:
	@echo "🗑️ Removing Claude Notifier service..."
	@sudo systemctl stop claude-notifier 2>/dev/null || true
	@sudo systemctl disable claude-notifier 2>/dev/null || true
	@sudo rm -f /etc/systemd/system/claude-notifier.service
	@sudo systemctl daemon-reload
	@echo "✅ Claude Notifier service removed"

# Check notifier status
notifier-status:
	@echo "📊 Claude Notifier status..."
	@sudo systemctl status claude-notifier --no-pager || echo "Service not installed"

# Test notifications
notifier-test:
	@echo "🔔 Testing Claude Notifier..."
	@echo "This will check for Claude processes and send test alerts"
	@bash scripts/claude-notifier.sh test

# View notifier logs
notifier-logs:
	@echo "📋 Claude Notifier logs..."
	@tail -f /var/log/claude-notifier.log

# Send manual notification
notify:
	@echo "📨 Send manual notification"
	@echo "Usage: make notify USER=username LEVEL=warning MSG='Your message'"
	@if [ -z "$(USER)" ] || [ -z "$(LEVEL)" ] || [ -z "$(MSG)" ]; then \
		echo "❌ Missing parameters. Use: make notify USER=username LEVEL=warning MSG='message'"; \
		exit 1; \
	fi
	@bash scripts/claude-notifier.sh notify $(USER) $(LEVEL) "$(MSG)"

# ============================================================================
# HELP UPDATES
# ============================================================================