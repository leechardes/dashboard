import streamlit as st
import time
import subprocess
from datetime import datetime
from pathlib import Path
from components.metrics import create_metric_card, create_alert_metric
from components.openvpn_manager import OpenVPNManager
from components.mikrotik_config import MikroTikConfig
from components.vpn_routes import VPNRoutes

def run():
    """View principal do OpenVPN Client Gateway"""
    
    # Header principal com Material Icon
    st.markdown(
        '<div class="main-header">'
        '<span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">vpn_lock</span>'
        'OpenVPN Client Gateway'
        '</div>', 
        unsafe_allow_html=True
    )
    
    # Inicializar gerenciadores
    try:
        vpn_manager = OpenVPNManager()
        mikrotik = MikroTikConfig()
        routes = VPNRoutes()
    except Exception as e:
        st.error(f"Erro ao inicializar componentes: {e}")
        return
    
    # Seção de métricas principais
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = vpn_manager.get_status()
        status_colors = {
            "connected": "var(--success-color)",
            "connecting": "var(--warning-color)", 
            "starting": "var(--info-color)",
            "stopped": "var(--error-color)",
            "error": "var(--error-color)"
        }
        status_labels = {
            "connected": "CONECTADO",
            "connecting": "CONECTANDO",
            "starting": "INICIANDO", 
            "stopped": "PARADO",
            "error": "ERRO"
        }
        icon_color = status_colors.get(status, "var(--text-color)")
        status_label = status_labels.get(status, status.upper())
        create_metric_card("Status VPN", status_label, "vpn_lock", icon_color)
    
    with col2:
        vpn_ip = vpn_manager.get_vpn_ip()
        create_metric_card("IP Local VPN", vpn_ip, "lan")
    
    with col3:
        active_routes = routes.get_active_routes()
        route_count = len(active_routes)
        create_metric_card("Rotas Ativas", str(route_count), "route")
    
    with col4:
        uptime = vpn_manager.get_uptime()
        create_metric_card("Tempo Online", uptime, "schedule")
    
    # Linha adicional de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        public_ip = vpn_manager.get_public_ip()
        create_metric_card("IP Público", public_ip, "public")
    
    with col2:
        mikrotik_stats = mikrotik.get_statistics()
        online_devices = mikrotik_stats.get('online_devices', 0)
        total_devices = mikrotik_stats.get('enabled_devices', 0)
        device_status = f"{online_devices}/{total_devices}"
        create_metric_card("Dispositivos", device_status, "router")
    
    with col3:
        route_stats = routes.get_statistics()
        system_routes = route_stats.get('system_routes', 0)
        create_metric_card("Rotas Sistema", str(system_routes), "timeline")
    
    with col4:
        autostart = vpn_manager.is_autostart_enabled()
        autostart_label = "ATIVO" if autostart else "INATIVO"
        autostart_color = "var(--success-color)" if autostart else "var(--warning-color)"
        create_metric_card("Auto-Início", autostart_label, "power_settings_new", autostart_color)
    
    # Criar abas para organizar a interface
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Controle",
        "Configuração", 
        "Rotas",
        "MikroTik",
        "Monitoramento",
        "Teste de Ping"
    ])
    
    # Tab 1 - Controle do Serviço
    with tab1:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>settings</span>Controle do Serviço", unsafe_allow_html=True)
        
        # Verificar se arquivo de autenticação existe
        auth_file_path = Path("/etc/openvpn/client-auth.txt")
        config_file_path = Path("/etc/openvpn/client.conf")
        
        if not auth_file_path.exists():
            st.error("**ATENÇÃO:** Arquivo de credenciais não encontrado! Configure na aba 'Configuração'")
        
        if not config_file_path.exists() or config_file_path.stat().st_size == 0:
            st.error("**ATENÇÃO:** Arquivo de configuração não encontrado ou vazio! Faça upload na aba 'Configuração'")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(":material/play_arrow: Iniciar VPN", use_container_width=True, key="start_vpn_tab"):
                with st.spinner("Iniciando VPN..."):
                    if vpn_manager.start():
                        st.success("VPN iniciada com sucesso")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Erro ao iniciar VPN")
        
        with col2:
            if st.button(":material/stop: Parar VPN", use_container_width=True, key="stop_vpn_tab"):
                if vpn_manager.stop():
                    st.warning("VPN parada")
                    st.rerun()
                else:
                    st.error("Erro ao parar VPN")
        
        with col3:
            if st.button(":material/restart_alt: Reiniciar VPN", use_container_width=True, key="restart_vpn_tab"):
                with st.spinner("Reiniciando VPN..."):
                    if vpn_manager.restart():
                        st.markdown("<div style='color: green; background-color: #d4edda; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #c3e6cb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>VPN reiniciada</div>", unsafe_allow_html=True)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.markdown("<div style='color: #721c24; background-color: #f8d7da; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #f5c6cb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Erro ao reiniciar VPN</div>", unsafe_allow_html=True)
        
        with col4:
            if st.button(":material/description: Ver Logs", use_container_width=True, key="view_logs_tab"):
                st.session_state['show_logs'] = True
        
        # Mostrar logs se o botão foi clicado
        if st.session_state.get('show_logs', False):
            st.markdown("---")
            st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>description</span>Logs do Sistema", unsafe_allow_html=True)
            
            # Opções de visualização de logs
            col1, col2 = st.columns([3, 1])
            with col1:
                log_lines = st.slider("Número de linhas", 10, 100, 50, step=10)
            with col2:
                if st.button(":material/refresh: Atualizar Logs"):
                    st.rerun()
            
            # Buscar e exibir logs
            logs = vpn_manager.get_logs(lines=log_lines)
            st.code(logs, language="bash")
            
            # Botão para ocultar logs
            if st.button(":material/close: Fechar Logs"):
                st.session_state['show_logs'] = False
                st.rerun()
        
        # Auto-início
        st.markdown("---")
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>power_settings_new</span>Configuração de Auto-Início", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            autostart = vpn_manager.is_autostart_enabled()
            if autostart:
                st.success("✓ Auto-início está ATIVO")
                if st.button(":material/power_settings_new: Desabilitar Auto-Início", use_container_width=True):
                    if vpn_manager.disable_autostart():
                        st.success("Auto-início desabilitado")
                        st.rerun()
            else:
                st.markdown("<div style='color: #856404; background-color: #fff3cd; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #ffeaa7;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>warning</span>Auto-início está INATIVO</div>", unsafe_allow_html=True)
                if st.button(":material/power_settings_new: Habilitar Auto-Início", use_container_width=True):
                    if vpn_manager.enable_autostart():
                        st.success("Auto-início habilitado")
                        st.rerun()
    
    # Tab 2 - Configuração
    with tab2:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>vpn_key</span>Configuração OpenVPN", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Credenciais de Autenticação")
            vpn_username = st.text_input("Usuário VPN", key="vpn_username", help="Usuário para autenticação no servidor VPN")
            vpn_password = st.text_input("Senha VPN", type="password", key="vpn_password", help="Senha para autenticação no servidor VPN")
            
            if st.button(":material/save: Salvar Credenciais", use_container_width=True):
                if vpn_username and vpn_password:
                    # Criar diretório /etc/openvpn se não existir
                    subprocess.run(['sudo', 'mkdir', '-p', '/etc/openvpn'], check=True)
                    
                    # Salvar credenciais em arquivo seguro
                    auth_file = Path("/etc/openvpn/client-auth.txt")
                    try:
                        # Criar conteúdo do arquivo auth
                        auth_content = f"{vpn_username}\n{vpn_password}\n"
                        
                        # Salvar usando subprocess com sudo
                        process = subprocess.Popen(
                            ['sudo', 'tee', str(auth_file)],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(auth_content)
                        
                        if process.returncode == 0:
                            # Definir permissões seguras
                            subprocess.run(['sudo', 'chmod', '600', str(auth_file)], check=True)
                            subprocess.run(['sudo', 'chown', 'root:root', str(auth_file)], check=True)
                            st.markdown("<div style='color: green; background-color: #d4edda; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #c3e6cb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Credenciais salvas com sucesso!</div>", unsafe_allow_html=True)
                            
                            # Atualizar configuração para usar o arquivo de auth
                            vpn_manager.update_auth_config(str(auth_file))
                        else:
                            st.error(f"Erro ao salvar credenciais: {stderr}")
                    except Exception as e:
                        st.error(f"Erro ao salvar credenciais: {str(e)}")
                else:
                    st.warning("Por favor, preencha usuário e senha")
        
        with col2:
            st.markdown("### Arquivo de Configuração")
            
            # Mostrar arquivo atual
            current_config = vpn_manager.get_config_file()
            st.info(f"**Arquivo atual:** {current_config}")
            
            # Upload de novo arquivo .ovpn
            uploaded_file = st.file_uploader(
                "Fazer upload de arquivo .ovpn",
                type=['ovpn'],
                help="Selecione um arquivo de configuração OpenVPN (.ovpn)"
            )
            
            if uploaded_file is not None:
                if st.button(":material/upload: Aplicar Configuração", use_container_width=True):
                    try:
                        # Criar diretório /etc/openvpn se não existir
                        subprocess.run(['sudo', 'mkdir', '-p', '/etc/openvpn'], check=True)
                        
                        # Ler conteúdo do arquivo
                        ovpn_content = uploaded_file.read().decode('utf-8')
                        
                        # Adicionar linha para usar arquivo de autenticação
                        if 'auth-user-pass' in ovpn_content and 'auth-user-pass ' not in ovpn_content:
                            ovpn_content = ovpn_content.replace('auth-user-pass', 'auth-user-pass /etc/openvpn/client-auth.txt')
                        
                        # Salvar arquivo de configuração
                        config_path = Path("/etc/openvpn/client.conf")
                        process = subprocess.Popen(
                            ['sudo', 'tee', str(config_path)],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(ovpn_content)
                        
                        if process.returncode == 0:
                            subprocess.run(['sudo', 'chmod', '644', str(config_path)], check=True)
                            st.markdown(f"<div style='color: green; background-color: #d4edda; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #c3e6cb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Configuração '{uploaded_file.name}' aplicada com sucesso!</div>", unsafe_allow_html=True)
                            st.info("Reinicie o serviço VPN para aplicar as mudanças")
                        else:
                            st.error(f"Erro ao salvar configuração: {stderr}")
                    except Exception as e:
                        st.error(f"Erro ao processar arquivo: {str(e)}")
    
    
    # Tab 3 - Gerenciamento de Rotas
    with tab3:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>route</span>Gerenciamento de Rotas", unsafe_allow_html=True)
        
        # Adicionar nova rota
        with st.expander("Adicionar Nova Rota", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                new_network = st.text_input(
                    "Rede/CIDR", 
                    placeholder="Ex: 192.168.100.0/24",
                    help="Digite a rede no formato CIDR (ex: 192.168.1.0/24)"
                )
                new_description = st.text_input(
                    "Descrição", 
                    placeholder="Ex: Rede do escritório remoto"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento
                if st.button(":material/add: Adicionar Rota", use_container_width=True):
                    if new_network:
                        with st.spinner("Adicionando rota..."):
                            success, message = routes.add_route(new_network, new_description)
                            if success:
                                st.success(f"{message}")
                                # Sincronizar com MikroTiks
                                sync_results = mikrotik.sync_routes(routes.get_active_routes())
                                for device, (sync_success, sync_msg) in sync_results.items():
                                    if sync_success:
                                        st.info(f"{device}: {sync_msg}")
                                    else:
                                        st.warning(f"{device}: {sync_msg}")
                                st.rerun()
                            else:
                                st.error(f"{message}")
                    else:
                        st.error("Digite uma rede válida")
        
        # Listar rotas ativas
        all_routes = routes.get_all_routes()
        if all_routes:
            st.markdown("### Rotas Configuradas")
            
            for i, route in enumerate(all_routes):
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        if route.get('enabled', True):
                            st.markdown(f"**{route['network']}** :material/check_circle:")
                        else:
                            st.markdown(f"**{route['network']}** :material/cancel:")
                        if route.get('description'):
                            st.caption(route['description'])
                    
                    with col2:
                        gateway = route.get('gateway', 'N/A')
                        st.text(f"Gateway: {gateway}")
                    
                    created = route.get('created', '')
                    if created:
                        try:
                            created_dt = datetime.fromisoformat(created)
                            st.caption(f"Criada: {created_dt.strftime('%d/%m/%Y %H:%M')}")
                        except:
                            pass
                
                with col3:
                    # Botão toggle
                    current_status = route.get('enabled', True)
                    toggle_label = ":material/toggle_off: Desativar" if current_status else ":material/toggle_on: Ativar"
                    if st.button(toggle_label, key=f"toggle_{route['network']}_{i}"):
                        success, message = routes.toggle_route(route['network'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col4:
                    # Botão remover
                    if st.button(":material/delete: Remover", key=f"del_{route['network']}_{i}"):
                        with st.spinner("Removendo rota..."):
                            success, message = routes.remove_route(route['network'])
                            if success:
                                st.success(message)
                                # Sincronizar com MikroTiks após remover
                                mikrotik.sync_routes(routes.get_active_routes())
                                st.rerun()
                            else:
                                st.error(message)
                    
                    st.markdown("---")
        else:
            st.info("Nenhuma rota configurada. Adicione a primeira rota acima.")
    
    # Tab 4 - Dispositivos MikroTik
    with tab4:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>Dispositivos MikroTik", unsafe_allow_html=True)
        
        # Configurar dispositivos
        with st.expander("Configurar Dispositivo MikroTik"):
            device_name = st.selectbox("Nome do Dispositivo", ["Casa", "Escritório", "Filial", "Outro"])
            
            if device_name == "Outro":
                device_name = st.text_input("Nome Personalizado")
        
        col1, col2 = st.columns(2)
        with col1:
            ip = st.text_input("IP do Dispositivo", placeholder="Ex: 192.168.1.1")
            user = st.text_input("Usuário SSH", value="admin")
        
        with col2:
            port = st.number_input("Porta SSH", value=22, min_value=1, max_value=65535)
            password = st.text_input("Senha SSH", type="password")
        
        description = st.text_area("Descrição", placeholder="Ex: MikroTik da matriz - RB4011")
        
        if st.button(":material/save: Salvar Configuração"):
            if device_name and ip and user and password:
                if mikrotik.save_device(device_name, ip, port, user, password, description):
                    st.markdown(f"<div style='color: green; background-color: #d4edda; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #c3e6cb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Configuração de '{device_name}' salva</div>", unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Erro ao salvar configuração")
            else:
                st.error("Preencha todos os campos obrigatórios")
    
    # Status dos dispositivos
    devices = mikrotik.get_devices()
    if devices:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>computer</span>Status dos Dispositivos", unsafe_allow_html=True)
        
        cols = st.columns(min(len(devices), 3))  # Máximo 3 colunas
        for idx, (name, config) in enumerate(devices.items()):
            with cols[idx % 3]:
                with st.container():
                    # Testar conectividade
                    is_online, status_msg = mikrotik.test_connection(config)
                    
                    # Status visual
                    if is_online:
                        st.success(f"✓ {name} - {status_msg}")
                        st.markdown(f"<span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>place</span>{config['ip']}:{config['port']}", unsafe_allow_html=True)
                        st.caption(f"Status: {status_msg}")
                        
                        # Botões de ação
                        if st.button(f":material/sync: Sincronizar", key=f"sync_{name}"):
                            with st.spinner(f"Sincronizando {name}..."):
                                sync_success, sync_msg = mikrotik.sync_device(name, routes.get_active_routes())
                                if sync_success:
                                    st.success(sync_msg)
                                else:
                                    st.error(sync_msg)
                        
                        if st.button(f":material/backup: Backup", key=f"backup_{name}"):
                            with st.spinner(f"Criando backup de {name}..."):
                                backup_success, backup_msg = mikrotik.backup_config(name)
                                if backup_success:
                                    st.success(backup_msg)
                                else:
                                    st.error(backup_msg)
                    else:
                        st.error(f"✗ {name} - {status_msg}")
                        st.markdown(f"<span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>place</span>{config['ip']}:{config['port']}", unsafe_allow_html=True)
                        st.caption(f"Erro: {status_msg}")
                    
                    # Botão de remover
                    if st.button(f":material/delete: Remover", key=f"remove_{name}"):
                        if mikrotik.delete_device(name):
                            st.success(f"Dispositivo {name} removido")
                            st.rerun()
                        else:
                            st.error("Erro ao remover dispositivo")
    else:
        st.info("Nenhum dispositivo MikroTik configurado. Configure o primeiro dispositivo acima.")
    
    # Sincronizar todos
    if devices:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>sync</span>Sincronização em Lote", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(":material/sync_alt: Sincronizar Todos os Dispositivos", use_container_width=True):
                active_routes = routes.get_active_routes()
                if active_routes:
                    with st.spinner("Sincronizando todos os dispositivos..."):
                        sync_results = mikrotik.sync_routes(active_routes)
                        
                        for device, (success, message) in sync_results.items():
                            if success:
                                st.markdown(f"<div style='color: green; background-color: #d4edda; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #c3e6cb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>{device}: {message}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='color: #721c24; background-color: #f8d7da; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #f5c6cb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>cancel</span>{device}: {message}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='color: #856404; background-color: #fff3cd; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #ffeaa7;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>warning</span>Nenhuma rota ativa para sincronizar</div>", unsafe_allow_html=True)
        
        with col2:
            if st.button(":material/cloud_sync: Backup Todos os Dispositivos", use_container_width=True):
                with st.spinner("Criando backup de todos os dispositivos..."):
                    for name in devices.keys():
                        success, message = mikrotik.backup_config(name)
                        if success:
                            st.markdown(f"<div style='color: #0c5460; background-color: #d1ecf1; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #bee5eb;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>folder</span>{name}: {message}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='color: #856404; background-color: #fff3cd; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #ffeaa7;'><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>warning</span>{name}: {message}</div>", unsafe_allow_html=True)
    
    # Monitoramento e estatísticas
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>monitoring</span>Monitoramento", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>analytics</span>Estatísticas de Rede", unsafe_allow_html=True)
        
        try:
            stats = vpn_manager.get_statistics()
            st.markdown(f"""
            <div style="padding: 0.5rem; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 0.25rem; color: var(--text-color);">
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>Dados Transmitidos:</strong> {stats['tx_bytes']}<br>
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>Dados Recebidos:</strong> {stats['rx_bytes']}<br>
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>inventory_2</span>Pacotes Enviados:</strong> {stats['tx_packets']}<br>
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>inventory_2</span>Pacotes Recebidos:</strong> {stats['rx_packets']}
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao obter estatísticas: {e}")
    
    with col2:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>speed</span>Conectividade", unsafe_allow_html=True)
        
        try:
            speed = vpn_manager.get_speed()
            st.markdown(f"""
            <div style="padding: 0.5rem; background-color: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 0.25rem; color: var(--text-color);">
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>language</span>Latência:</strong> {speed['latency']} ms<br>
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>analytics</span>Perda de Pacotes:</strong> {speed['loss']}%<br>
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>bolt</span>Download:</strong> {speed['download']} Mbps<br>
            <strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>bolt</span>Upload:</strong> {speed['upload']} Mbps
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao obter velocidade: {e}")
    
    # Informações detalhadas
    with st.expander("Informações Detalhadas do Sistema"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<strong><span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>build</span> Configurações VPN:</strong>", unsafe_allow_html=True)
            vpn_info = vpn_manager.get_connection_info()
            for key, value in vpn_info.items():
                st.text(f"{key.replace('_', ' ').title()}: {value}")
        
        with col2:
            st.markdown("**Estatísticas de Rotas:**")
            route_stats = routes.get_statistics()
            for key, value in route_stats.items():
                if key != 'config_file':  # Não mostrar caminho do arquivo
                    st.text(f"{key.replace('_', ' ').title()}: {value}")
    
    # Logs do sistema
    with st.expander("Ver Logs do OpenVPN"):
        log_lines = st.selectbox("Número de linhas", [20, 50, 100, 200], index=1)
        
        if st.button(":material/refresh: Carregar Logs"):
            with st.spinner("Carregando logs..."):
                try:
                    logs = vpn_manager.get_logs(lines=log_lines)
                    st.code(logs, language="text")
                except Exception as e:
                    st.error(f"Erro ao carregar logs: {e}")
    
    # Tab 5 - Monitoramento
    with tab5:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>monitoring</span>Monitoramento", unsafe_allow_html=True)
        
        # Estatísticas em tempo real
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Estatísticas da Interface")
            stats = vpn_manager.get_statistics()
            for key, value in stats.items():
                st.text(f"{key}: {value}")
        
        with col2:
            st.markdown("#### Informações da Conexão")
            conn_info = vpn_manager.get_connection_info()
            for key, value in conn_info.items():
                st.text(f"{key}: {value}")
        
        # Logs
        with st.expander("Ver Logs do Sistema"):
            log_lines = st.slider("Linhas de log", 10, 200, 50)
            if st.button(":material/refresh: Atualizar Logs", key="refresh_logs_monitoring"):
                logs = vpn_manager.get_logs(log_lines)
                st.code(logs, language="bash")
    
    # Tab 6 - Teste de Ping
    with tab6:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>network_check</span>Teste de Conectividade", unsafe_allow_html=True)
        
        # Teste rápido de conectividade
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Campo para digitar IP ou hostname
            target_host = st.text_input(
                "Endereço para teste (IP ou hostname)",
                placeholder="Ex: 8.8.8.8 ou google.com",
                help="Digite um endereço IP ou hostname para testar conectividade"
            )
        
        with col2:
            # Número de pacotes
            packet_count = st.number_input(
                "Pacotes",
                min_value=1,
                max_value=20,
                value=4,
                help="Número de pacotes ICMP a enviar"
            )
        
        # Hosts predefinidos para teste rápido
        st.markdown("#### Testes Rápidos")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(":material/public: Google DNS", use_container_width=True):
                target_host = "8.8.8.8"
                st.session_state['ping_target'] = target_host
        
        with col2:
            if st.button(":material/dns: Cloudflare", use_container_width=True):
                target_host = "1.1.1.1"
                st.session_state['ping_target'] = target_host
        
        with col3:
            if st.button(":material/router: Gateway VPN", use_container_width=True):
                # Obter gateway da VPN
                gateway = subprocess.run(
                    ['ip', 'route', 'show', 'dev', 'tun0'],
                    capture_output=True, text=True
                ).stdout.split()[2] if vpn_manager.get_status() == "connected" else "10.8.0.1"
                target_host = gateway
                st.session_state['ping_target'] = target_host
        
        with col4:
            if st.button(":material/home: Gateway Local", use_container_width=True):
                # Obter gateway padrão
                gateway = subprocess.run(
                    ['ip', 'route', 'show', 'default'],
                    capture_output=True, text=True
                ).stdout.split()[2] if subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True).returncode == 0 else "192.168.1.1"
                target_host = gateway
                st.session_state['ping_target'] = target_host
        
        # Usar target do session_state se existir
        if 'ping_target' in st.session_state:
            target_host = st.session_state['ping_target']
        
        # Botão de executar ping
        if st.button(":material/send: Executar Teste", type="primary", use_container_width=True):
            if target_host:
                with st.spinner(f"Testando conectividade com {target_host}..."):
                    try:
                        # Executar ping
                        result = subprocess.run(
                            ['ping', '-c', str(packet_count), '-W', '2', target_host],
                            capture_output=True,
                            text=True,
                            timeout=packet_count * 3 + 2
                        )
                        
                        # Processar resultado
                        if result.returncode == 0:
                            st.success(f"Conectividade OK com {target_host}")
                            
                            # Extrair estatísticas do ping
                            output_lines = result.stdout.split('\n')
                            
                            # Mostrar resultado completo
                            with st.expander("Detalhes do Ping", expanded=True):
                                st.code(result.stdout, language="bash")
                            
                            # Extrair e mostrar estatísticas
                            for line in output_lines:
                                if 'packet loss' in line:
                                    st.info(f"Estatística: {line}")
                                if 'rtt min/avg/max' in line or 'round-trip' in line:
                                    st.info(f"Latência: {line}")
                        else:
                            st.error(f"Falha na conectividade com {target_host}")
                            if result.stdout:
                                with st.expander("Detalhes do erro"):
                                    st.code(result.stdout, language="bash")
                            
                    except subprocess.TimeoutExpired:
                        st.error(f"Timeout ao tentar alcançar {target_host}")
                    except Exception as e:
                        st.error(f"Erro ao executar ping: {str(e)}")
            else:
                st.warning("Por favor, digite um endereço para testar")
        
        # Teste de conectividade através da VPN
        st.markdown("---")
        st.markdown("#### Teste de Rota pela VPN")
        
        if st.button(":material/route: Testar Rota Completa", use_container_width=True):
            if vpn_manager.get_status() == "connected":
                with st.spinner("Testando rota através da VPN..."):
                    # Testar conectividade local
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Interface VPN (tun0):**")
                        vpn_ip = vpn_manager.get_vpn_ip()
                        if vpn_ip:
                            st.success(f"IP: {vpn_ip}")
                        else:
                            st.error("Interface não encontrada")
                    
                    with col2:
                        st.markdown("**IP Público via VPN:**")
                        try:
                            public_ip = subprocess.run(
                                ['curl', '-s', '--max-time', '5', 'ifconfig.me'],
                                capture_output=True, text=True
                            ).stdout.strip()
                            if public_ip:
                                st.success(f"IP: {public_ip}")
                            else:
                                st.warning("Não foi possível obter IP público")
                        except:
                            st.error("Erro ao verificar IP público")
                    
                    # Traceroute simplificado
                    if target_host:
                        with st.expander("Traçar Rota"):
                            try:
                                trace_result = subprocess.run(
                                    ['traceroute', '-n', '-m', '10', '-w', '2', target_host],
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                st.code(trace_result.stdout, language="bash")
                            except subprocess.TimeoutExpired:
                                st.warning("Traceroute timeout")
                            except FileNotFoundError:
                                st.info("Traceroute não instalado. Use: sudo apt install traceroute")
            else:
                st.warning("VPN não está conectada")
    
    # Auto-refresh
    st.sidebar.markdown("---")
    auto_refresh = st.sidebar.checkbox("Auto-atualização (30s)", value=False)
    
    if auto_refresh:
        st.sidebar.markdown("Próxima atualização em 30s")
        time.sleep(30)
        st.rerun()
    
    # Status footer
    st.sidebar.markdown("---")
    current_status = vpn_manager.get_status()
    if current_status == "connected":
        st.sidebar.success("VPN Gateway Online")
    elif current_status in ["connecting", "starting"]:
        st.sidebar.warning("VPN Gateway Iniciando")
    else:
        st.sidebar.error("VPN Gateway Offline")
    
    st.sidebar.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")