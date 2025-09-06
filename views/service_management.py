"""Service Management view - Control the dashboard service"""

import streamlit as st
import subprocess
import os
import json
import time
from datetime import datetime
from pathlib import Path
from components.metrics import create_metric_card

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
    st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">settings</span>Gerenciamento de Serviços</div>', unsafe_allow_html=True)
    st.markdown("Controle e configure o serviço do dashboard")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Status", "Controle", "Configuração", "Logs"])
    
    # Tab 1: Status
    with tab1:
        st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>info</span>Status do Serviço", unsafe_allow_html=True)
        
        # Refresh button
        if st.button(":material/refresh: Atualizar Status", key="refresh_status"):
            st.rerun()
        
        # Get current status
        status = get_service_status()
        
        # Display status metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if status["active"]:
                create_metric_card("Status", "Ativo", "check_circle")
            else:
                create_metric_card("Status", "Inativo", "cancel")
        
        with col2:
            create_metric_card("PID", status["pid"] or "N/A", "tag")
        
        with col3:
            create_metric_card("Memória", status["memory"] or "N/A", "memory")
        
        with col4:
            port = load_env_config().get("STREAMLIT_SERVER_PORT", "8081")
            create_metric_card("Porta", port, "lan")
        
        # Show detailed status
        with st.expander("Status Detalhado"):
            st.code(status["status_text"])
        
        # Quick info
        st.info(f"""
        **Access URL:** http://{subprocess.getoutput('hostname -I').split()[0]}:{port}
        
        **Service Name:** streamlit-dashboard
        
        **Working Directory:** /srv/projects/shared/dashboard
        """)
    
    # Tab 2: Control
    with tab2:
        st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>tune</span>Controle do Serviço", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(":material/play_arrow: Iniciar", key="start_service", width='stretch'):
                with st.spinner("Iniciando serviço..."):
                    success, stdout, stderr = run_command("sudo systemctl start streamlit-dashboard")
                    if success:
                        st.success("Serviço iniciado com sucesso!")
                    else:
                        st.error(f"Falha ao iniciar serviço: {stderr}")
                    time.sleep(2)
                    st.rerun()
        
        with col2:
            if st.button(":material/stop: Parar", key="stop_service", width='stretch'):
                if st.checkbox("Tenho certeza que quero parar o serviço"):
                    with st.spinner("Parando serviço..."):
                        success, stdout, stderr = run_command("sudo systemctl stop streamlit-dashboard")
                        if success:
                            st.success("Serviço parado com sucesso!")
                        else:
                            st.error(f"Falha ao parar serviço: {stderr}")
                        time.sleep(2)
                        st.rerun()
        
        with col3:
            if st.button(":material/restart_alt: Reiniciar", key="restart_service", width='stretch'):
                with st.spinner("Reiniciando serviço..."):
                    success, stdout, stderr = run_command("sudo systemctl restart streamlit-dashboard")
                    if success:
                        st.success("Serviço reiniciado com sucesso!")
                    else:
                        st.error(f"Falha ao reiniciar serviço: {stderr}")
                    time.sleep(2)
                    st.rerun()
        
        with col4:
            if st.button(":material/cached: Recarregar", key="reload_service", width='stretch'):
                with st.spinner("Recarregando serviço..."):
                    success, stdout, stderr = run_command("sudo systemctl reload streamlit-dashboard")
                    if success:
                        st.success("Serviço recarregado com sucesso!")
                    else:
                        st.error(f"Falha ao recarregar serviço: {stderr}")
                    time.sleep(2)
                    st.rerun()
        
        st.markdown("---")
        
        # Advanced controls
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>settings_applications</span>Controles Avançados", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**<span class='material-icons' style='font-size: 1rem; vertical-align: middle;'>power_settings_new</span> Início Automático na Inicialização**", unsafe_allow_html=True)
            
            # Check if enabled
            success, stdout, stderr = run_command("systemctl is-enabled streamlit-dashboard")
            is_enabled = stdout.strip() == "enabled"
            
            if is_enabled:
                st.success("Início automático ativado")
                if st.button(":material/block: Desabilitar Início Automático"):
                    success, stdout, stderr = run_command("sudo systemctl disable streamlit-dashboard")
                    if success:
                        st.success("Início automático desabilitado")
                        st.rerun()
                    else:
                        st.error(f"Falhou: {stderr}")
            else:
                st.warning("Início automático está desabilitado")
                if st.button(":material/power_settings_new: Habilitar Início Automático"):
                    success, stdout, stderr = run_command("sudo systemctl enable streamlit-dashboard")
                    if success:
                        st.success("Início automático habilitado")
                        st.rerun()
                    else:
                        st.error(f"Falhou: {stderr}")
        
        with col2:
            st.markdown("**<span class='material-icons' style='font-size: 1rem; vertical-align: middle;'>inventory_2</span> Instalação do Serviço**", unsafe_allow_html=True)
            
            # Check if service exists
            success, stdout, stderr = run_command("systemctl list-unit-files | grep streamlit-dashboard")
            service_exists = success and "streamlit-dashboard" in stdout
            
            if service_exists:
                st.success("Serviço está instalado")
                if st.button(":material/delete: Desinstalar Serviço"):
                    if st.checkbox("Entendo que isso removerá o serviço"):
                        success, stdout, stderr = run_command("cd /srv/projects/shared/dashboard && sudo make uninstall-service")
                        if success:
                            st.success("Serviço desinstalado")
                            st.rerun()
                        else:
                            st.error(f"Falhou: {stderr}")
            else:
                st.warning("Serviço não instalado")
                if st.button(":material/inventory_2: Install Service"):
                    success, stdout, stderr = run_command("cd /srv/projects/shared/dashboard && sudo make install-service")
                    if success:
                        st.success("Serviço instalado com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"Falhou: {stderr}")
    
    # Tab 3: Configuration
    with tab3:
        st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>tune</span>Configuração do Serviço", unsafe_allow_html=True)
        
        # Load current config
        config = load_env_config()
        
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>code</span>Variáveis de Ambiente", unsafe_allow_html=True)
        
        # Port configuration
        col1, col2 = st.columns(2)
        
        with col1:
            new_port = st.number_input(
                "Porta do Servidor",
                min_value=1024,
                max_value=65535,
                value=int(config.get("STREAMLIT_SERVER_PORT", "8081")),
                key="config_port"
            )
        
        with col2:
            new_address = st.text_input(
                "Endereço do Servidor",
                value=config.get("STREAMLIT_SERVER_ADDRESS", "0.0.0.0"),
                key="config_address"
            )
        
        # Project paths
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>folder</span>Caminhos do Projeto", unsafe_allow_html=True)
        
        project_root = st.text_input(
            "Raiz do Projeto",
            value=config.get("PROJECT_ROOT", "/srv/projects"),
            key="config_project_root"
        )
        
        docs_path = st.text_input(
            "Caminho da Documentação",
            value=config.get("DOCS_PATH", "/srv/projects"),
            key="config_docs_path"
        )
        
        logs_path = st.text_input(
            "Caminho dos Logs",
            value=config.get("LOGS_PATH", "/var/log"),
            key="config_logs_path"
        )
        
        # Save button
        if st.button(":material/save: Salvar Configuração", type="primary"):
            # Update config
            config["STREAMLIT_SERVER_PORT"] = str(new_port)
            config["STREAMLIT_SERVER_ADDRESS"] = new_address
            config["PROJECT_ROOT"] = project_root
            config["DOCS_PATH"] = docs_path
            config["LOGS_PATH"] = logs_path
            
            # Save to file
            if save_env_config(config):
                st.success("Configuração salva com sucesso!")
                st.warning("Você precisa reiniciar o serviço para que as mudanças tenham efeito")
                
                # Offer to restart
                if st.button(":material/refresh: Restart Service Now"):
                    success, stdout, stderr = run_command("sudo systemctl restart streamlit-dashboard")
                    if success:
                        st.success("Serviço reiniciado com a nova configuração!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Falha ao reiniciar: {stderr}")
            else:
                st.error("Falha ao salvar configuração")
        
        # Show current config file
        with st.expander("Visualizar arquivo .env"):
            if os.path.exists("/srv/projects/shared/dashboard/.env"):
                with open("/srv/projects/shared/dashboard/.env", 'r') as f:
                    st.code(f.read())
        
        # Show service file
        with st.expander("Visualizar arquivo do Serviço"):
            service_file = "/etc/systemd/system/streamlit-dashboard.service"
            if os.path.exists(service_file):
                success, stdout, stderr = run_command(f"cat {service_file}")
                if success:
                    st.code(stdout)
            else:
                st.warning("Arquivo do serviço não encontrado. O serviço pode não estar instalado.")
    
    # Tab 4: Logs
    with tab4:
        st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>description</span>Logs do Serviço", unsafe_allow_html=True)
        
        # Log source selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_source = st.selectbox(
                "Fonte dos Logs",
                ["Logs do Serviço (journalctl)", "Logs da Aplicação (streamlit.log)"],
                key="log_source"
            )
        
        with col2:
            log_lines = st.number_input(
                "Número de Linhas",
                min_value=10,
                max_value=1000,
                value=100,
                step=50,
                key="log_lines"
            )
        
        with col3:
            if st.button(":material/refresh: Refresh Logs", key="refresh_logs"):
                st.rerun()
        
        # Auto-refresh option
        auto_refresh = st.checkbox("Atualizar logs automaticamente a cada 5 segundos", key="auto_refresh_logs")
        
        if auto_refresh:
            st.info("Atualização automática ativada. Os logs serão atualizados a cada 5 segundos.")
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
                st.code(stdout or "Nenhum log disponível", language="log")
        else:
            st.error(f"Falha ao obter logs: {stderr}")
        
        # Log management
        st.markdown("---")
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>manage_history</span>Gerenciamento de Logs", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(":material/cleaning_services: Clear Application Logs"):
                if st.checkbox("Quero limpar os logs"):
                    log_file = "/srv/projects/shared/dashboard/streamlit.log"
                    if os.path.exists(log_file):
                        with open(log_file, 'w') as f:
                            f.write(f"Logs cleared at {datetime.now()}\n")
                        st.success("Logs da aplicação limpos")
                    else:
                        st.warning("Arquivo de log não encontrado")
        
        with col2:
            if st.button(":material/download: Baixar Logs"):
                success, stdout, stderr = get_logs(lines=1000, service=use_service_logs)
                if success:
                    st.download_button(
                        label=":material/download: Baixar",
                        data=stdout,
                        file_name=f"dashboard_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                        mime="text/plain"
                    )
        
        with col3:
            if st.button(":material/search: Buscar nos Logs"):
                search_term = st.text_input("Termo de busca:")
                if search_term:
                    success, stdout, stderr = get_logs(lines=500, service=use_service_logs)
                    if success:
                        lines = stdout.splitlines()
                        matching_lines = [line for line in lines if search_term.lower() in line.lower()]
                        if matching_lines:
                            st.success(f"Encontradas {len(matching_lines)} linhas correspondentes:")
                            st.code("\n".join(matching_lines))
                        else:
                            st.warning("Nenhuma linha correspondente encontrada")