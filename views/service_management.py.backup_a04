"""Service Management view - Control the dashboard service"""

import streamlit as st
import subprocess
import os
import json
import time
from datetime import datetime
from pathlib import Path

def run_command(cmd, shell=True, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            capture_output=capture_output, 
            text=True,
            cwd="/srv/projects/shared/dashboard"
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_service_status():
    """Get the current status of the dashboard service"""
    success, stdout, stderr = run_command("systemctl is-active streamlit-dashboard")
    is_active = stdout.strip() == "active"
    
    # Get detailed status
    success, stdout, stderr = run_command("systemctl status streamlit-dashboard --no-pager")
    
    # Parse status info
    status_info = {
        "active": is_active,
        "status_text": stdout if success else stderr,
        "pid": None,
        "memory": None,
        "cpu": None,
        "uptime": None
    }
    
    # Try to extract PID and other info
    if is_active:
        success, stdout, stderr = run_command("systemctl show streamlit-dashboard --property=MainPID,MemoryCurrent,CPUUsageNSec")
        for line in stdout.splitlines():
            if "MainPID=" in line:
                status_info["pid"] = line.split("=")[1]
            elif "MemoryCurrent=" in line:
                mem = line.split("=")[1]
                if mem and mem != "[not set]":
                    try:
                        status_info["memory"] = f"{int(mem) / 1024 / 1024:.1f} MB"
                    except:
                        pass
    
    return status_info

def get_logs(lines=50, service=False):
    """Get recent logs from the dashboard"""
    if service:
        cmd = f"sudo journalctl -u streamlit-dashboard -n {lines} --no-pager"
    else:
        log_file = "/srv/projects/shared/dashboard/streamlit.log"
        if os.path.exists(log_file):
            cmd = f"tail -n {lines} {log_file}"
        else:
            return False, "", "Log file not found"
    
    return run_command(cmd)

def load_env_config():
    """Load environment configuration"""
    env_file = "/srv/projects/shared/dashboard/.env"
    config = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
    
    return config

def save_env_config(config):
    """Save environment configuration"""
    env_file = "/srv/projects/shared/dashboard/.env"
    
    # Read existing file to preserve comments
    lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line_stripped = line.strip()
                if line_stripped.startswith('#') or not line_stripped:
                    lines.append(line)
                else:
                    # Check if this is a config line we're updating
                    updated = False
                    for key, value in config.items():
                        if line_stripped.startswith(f"{key}="):
                            lines.append(f"{key}={value}\n")
                            updated = True
                            break
                    if not updated:
                        lines.append(line)
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    return True

def run():
    """Main function for Service Management view"""
    st.title("🛠️ Service Management")
    st.markdown("Control and configure the dashboard service")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Status", "🎮 Control", "⚙️ Configuration", "📋 Logs"])
    
    # Tab 1: Status
    with tab1:
        st.subheader("Service Status")
        
        # Refresh button
        if st.button("🔄 Refresh Status", key="refresh_status"):
            st.rerun()
        
        # Get current status
        status = get_service_status()
        
        # Display status metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if status["active"]:
                st.metric("Status", "🟢 Active")
            else:
                st.metric("Status", "🔴 Inactive")
        
        with col2:
            st.metric("PID", status["pid"] or "N/A")
        
        with col3:
            st.metric("Memory", status["memory"] or "N/A")
        
        with col4:
            port = load_env_config().get("STREAMLIT_SERVER_PORT", "8081")
            st.metric("Port", port)
        
        # Show detailed status
        with st.expander("📝 Detailed Status"):
            st.code(status["status_text"])
        
        # Quick info
        st.info(f"""
        **Access URL:** http://{subprocess.getoutput('hostname -I').split()[0]}:{port}
        
        **Service Name:** streamlit-dashboard
        
        **Working Directory:** /srv/projects/shared/dashboard
        """)
    
    # Tab 2: Control
    with tab2:
        st.subheader("Service Control")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("▶️ Start", key="start_service", use_container_width=True):
                with st.spinner("Starting service..."):
                    success, stdout, stderr = run_command("sudo systemctl start streamlit-dashboard")
                    if success:
                        st.success("Service started successfully!")
                    else:
                        st.error(f"Failed to start service: {stderr}")
                    time.sleep(2)
                    st.rerun()
        
        with col2:
            if st.button("⏹️ Stop", key="stop_service", use_container_width=True):
                if st.checkbox("I'm sure I want to stop the service"):
                    with st.spinner("Stopping service..."):
                        success, stdout, stderr = run_command("sudo systemctl stop streamlit-dashboard")
                        if success:
                            st.success("Service stopped successfully!")
                        else:
                            st.error(f"Failed to stop service: {stderr}")
                        time.sleep(2)
                        st.rerun()
        
        with col3:
            if st.button("🔄 Restart", key="restart_service", use_container_width=True):
                with st.spinner("Restarting service..."):
                    success, stdout, stderr = run_command("sudo systemctl restart streamlit-dashboard")
                    if success:
                        st.success("Service restarted successfully!")
                    else:
                        st.error(f"Failed to restart service: {stderr}")
                    time.sleep(2)
                    st.rerun()
        
        with col4:
            if st.button("♻️ Reload", key="reload_service", use_container_width=True):
                with st.spinner("Reloading service..."):
                    success, stdout, stderr = run_command("sudo systemctl reload streamlit-dashboard")
                    if success:
                        st.success("Service reloaded successfully!")
                    else:
                        st.error(f"Failed to reload service: {stderr}")
                    time.sleep(2)
                    st.rerun()
        
        st.markdown("---")
        
        # Advanced controls
        st.subheader("Advanced Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Auto-start on Boot**")
            
            # Check if enabled
            success, stdout, stderr = run_command("systemctl is-enabled streamlit-dashboard")
            is_enabled = stdout.strip() == "enabled"
            
            if is_enabled:
                st.success("✅ Auto-start is enabled")
                if st.button("🚫 Disable Auto-start"):
                    success, stdout, stderr = run_command("sudo systemctl disable streamlit-dashboard")
                    if success:
                        st.success("Auto-start disabled")
                        st.rerun()
                    else:
                        st.error(f"Failed: {stderr}")
            else:
                st.warning("❌ Auto-start is disabled")
                if st.button("✅ Enable Auto-start"):
                    success, stdout, stderr = run_command("sudo systemctl enable streamlit-dashboard")
                    if success:
                        st.success("Auto-start enabled")
                        st.rerun()
                    else:
                        st.error(f"Failed: {stderr}")
        
        with col2:
            st.markdown("**Service Installation**")
            
            # Check if service exists
            success, stdout, stderr = run_command("systemctl list-unit-files | grep streamlit-dashboard")
            service_exists = success and "streamlit-dashboard" in stdout
            
            if service_exists:
                st.success("✅ Service is installed")
                if st.button("🗑️ Uninstall Service"):
                    if st.checkbox("I understand this will remove the service"):
                        success, stdout, stderr = run_command("cd /srv/projects/shared/dashboard && sudo make uninstall-service")
                        if success:
                            st.success("Service uninstalled")
                            st.rerun()
                        else:
                            st.error(f"Failed: {stderr}")
            else:
                st.warning("❌ Service not installed")
                if st.button("📦 Install Service"):
                    success, stdout, stderr = run_command("cd /srv/projects/shared/dashboard && sudo make install-service")
                    if success:
                        st.success("Service installed successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed: {stderr}")
    
    # Tab 3: Configuration
    with tab3:
        st.subheader("Service Configuration")
        
        # Load current config
        config = load_env_config()
        
        st.markdown("### Environment Variables")
        
        # Port configuration
        col1, col2 = st.columns(2)
        
        with col1:
            new_port = st.number_input(
                "Server Port",
                min_value=1024,
                max_value=65535,
                value=int(config.get("STREAMLIT_SERVER_PORT", "8081")),
                key="config_port"
            )
        
        with col2:
            new_address = st.text_input(
                "Server Address",
                value=config.get("STREAMLIT_SERVER_ADDRESS", "0.0.0.0"),
                key="config_address"
            )
        
        # Project paths
        st.markdown("### Project Paths")
        
        project_root = st.text_input(
            "Project Root",
            value=config.get("PROJECT_ROOT", "/srv/projects"),
            key="config_project_root"
        )
        
        docs_path = st.text_input(
            "Documentation Path",
            value=config.get("DOCS_PATH", "/srv/projects"),
            key="config_docs_path"
        )
        
        logs_path = st.text_input(
            "Logs Path",
            value=config.get("LOGS_PATH", "/var/log"),
            key="config_logs_path"
        )
        
        # Save button
        if st.button("💾 Save Configuration", type="primary"):
            # Update config
            config["STREAMLIT_SERVER_PORT"] = str(new_port)
            config["STREAMLIT_SERVER_ADDRESS"] = new_address
            config["PROJECT_ROOT"] = project_root
            config["DOCS_PATH"] = docs_path
            config["LOGS_PATH"] = logs_path
            
            # Save to file
            if save_env_config(config):
                st.success("Configuration saved successfully!")
                st.warning("⚠️ You need to restart the service for changes to take effect")
                
                # Offer to restart
                if st.button("🔄 Restart Service Now"):
                    success, stdout, stderr = run_command("sudo systemctl restart streamlit-dashboard")
                    if success:
                        st.success("Service restarted with new configuration!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Failed to restart: {stderr}")
            else:
                st.error("Failed to save configuration")
        
        # Show current config file
        with st.expander("📄 View .env File"):
            if os.path.exists("/srv/projects/shared/dashboard/.env"):
                with open("/srv/projects/shared/dashboard/.env", 'r') as f:
                    st.code(f.read())
        
        # Show service file
        with st.expander("📄 View Service File"):
            service_file = "/etc/systemd/system/streamlit-dashboard.service"
            if os.path.exists(service_file):
                success, stdout, stderr = run_command(f"cat {service_file}")
                if success:
                    st.code(stdout)
            else:
                st.warning("Service file not found. Service may not be installed.")
    
    # Tab 4: Logs
    with tab4:
        st.subheader("Service Logs")
        
        # Log source selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_source = st.selectbox(
                "Log Source",
                ["Service Logs (journalctl)", "Application Logs (streamlit.log)"],
                key="log_source"
            )
        
        with col2:
            log_lines = st.number_input(
                "Number of Lines",
                min_value=10,
                max_value=1000,
                value=100,
                step=50,
                key="log_lines"
            )
        
        with col3:
            if st.button("🔄 Refresh Logs", key="refresh_logs"):
                st.rerun()
        
        # Auto-refresh option
        auto_refresh = st.checkbox("Auto-refresh logs every 5 seconds", key="auto_refresh_logs")
        
        if auto_refresh:
            st.info("Auto-refresh is enabled. Logs will update every 5 seconds.")
            time.sleep(5)
            st.rerun()
        
        # Display logs
        st.markdown("---")
        
        use_service_logs = "Service Logs" in log_source
        success, stdout, stderr = get_logs(lines=log_lines, service=use_service_logs)
        
        if success:
            # Color code log levels
            log_container = st.container()
            with log_container:
                st.code(stdout or "No logs available", language="log")
        else:
            st.error(f"Failed to retrieve logs: {stderr}")
        
        # Log management
        st.markdown("---")
        st.markdown("### Log Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 Clear Application Logs"):
                if st.checkbox("I want to clear the logs"):
                    log_file = "/srv/projects/shared/dashboard/streamlit.log"
                    if os.path.exists(log_file):
                        with open(log_file, 'w') as f:
                            f.write(f"Logs cleared at {datetime.now()}\n")
                        st.success("Application logs cleared")
                    else:
                        st.warning("Log file not found")
        
        with col2:
            if st.button("📥 Download Logs"):
                success, stdout, stderr = get_logs(lines=1000, service=use_service_logs)
                if success:
                    st.download_button(
                        label="💾 Download",
                        data=stdout,
                        file_name=f"dashboard_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                        mime="text/plain"
                    )
        
        with col3:
            if st.button("🔍 Search in Logs"):
                search_term = st.text_input("Search term:")
                if search_term:
                    success, stdout, stderr = get_logs(lines=500, service=use_service_logs)
                    if success:
                        lines = stdout.splitlines()
                        matching_lines = [line for line in lines if search_term.lower() in line.lower()]
                        if matching_lines:
                            st.success(f"Found {len(matching_lines)} matching lines:")
                            st.code("\n".join(matching_lines))
                        else:
                            st.warning("No matching lines found")