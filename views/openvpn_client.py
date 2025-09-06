import streamlit as st
import time
from datetime import datetime
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
    
    # Seção de controle do serviço
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>settings</span>Controle do Serviço", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(":material/play_arrow: Iniciar VPN", use_container_width=True):
            with st.spinner("Iniciando VPN..."):
                if vpn_manager.start():
                    st.success("✅ VPN iniciada com sucesso")
                    time.sleep(2)  # Aguardar inicialização
                    st.rerun()
                else:
                    st.error("❌ Erro ao iniciar VPN")
    
    with col2:
        if st.button(":material/stop: Parar VPN", use_container_width=True):
            with st.spinner("Parando VPN..."):
                if vpn_manager.stop():
                    st.warning("⚠️ VPN parada")
                    st.rerun()
                else:
                    st.error("❌ Erro ao parar VPN")
    
    with col3:
        if st.button(":material/restart_alt: Reiniciar VPN", use_container_width=True):
            with st.spinner("Reiniciando VPN..."):
                if vpn_manager.restart():
                    st.success("✅ VPN reiniciada")
                    time.sleep(3)  # Aguardar reinicialização
                    st.rerun()
                else:
                    st.error("❌ Erro ao reiniciar VPN")
    
    with col4:
        if st.button(":material/refresh: Atualizar Status", use_container_width=True):
            st.rerun()
    
    # Controles adicionais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_autostart = vpn_manager.is_autostart_enabled()
        if current_autostart:
            if st.button(":material/power_off: Desabilitar Auto-Início", use_container_width=True):
                if vpn_manager.disable_autostart():
                    st.success("Auto-início desabilitado")
                    st.rerun()
                else:
                    st.error("Erro ao desabilitar auto-início")
        else:
            if st.button(":material/power: Habilitar Auto-Início", use_container_width=True):
                if vpn_manager.enable_autostart():
                    st.success("Auto-início habilitado")
                    st.rerun()
                else:
                    st.error("Erro ao habilitar auto-início")
    
    with col2:
        if st.button(":material/security: Aplicar Regras Firewall", use_container_width=True):
            with st.spinner("Aplicando regras de firewall..."):
                success, message = routes.apply_firewall_base_rules()
                if success:
                    st.success("✅ Regras aplicadas")
                    st.code(message)
                else:
                    st.error(f"❌ {message}")
    
    with col3:
        if st.button(":material/sync: Sincronizar Sistema", use_container_width=True):
            with st.spinner("Sincronizando rotas..."):
                success, message = routes.sync_with_system()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.warning(f"⚠️ {message}")
                st.rerun()
    
    # Gerenciamento de rotas
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>route</span>Gerenciamento de Rotas", unsafe_allow_html=True)
    
    # Adicionar nova rota
    with st.expander("➕ Adicionar Nova Rota"):
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
                            st.success(f"✅ {message}")
                            # Sincronizar com MikroTiks
                            sync_results = mikrotik.sync_routes(routes.get_active_routes())
                            for device, (sync_success, sync_msg) in sync_results.items():
                                if sync_success:
                                    st.info(f"📡 {device}: {sync_msg}")
                                else:
                                    st.warning(f"⚠️ {device}: {sync_msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("Digite uma rede válida")
    
    # Listar rotas ativas
    all_routes = routes.get_all_routes()
    if all_routes:
        st.markdown("### 📋 Rotas Configuradas")
        
        for i, route in enumerate(all_routes):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    status_icon = "✅" if route.get('enabled', True) else "❌"
                    st.markdown(f"**{status_icon} {route['network']}**")
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
    
    # Dispositivos MikroTik
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>Dispositivos MikroTik", unsafe_allow_html=True)
    
    # Configurar dispositivos
    with st.expander("⚙️ Configurar Dispositivo MikroTik"):
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
                    st.success(f"✅ Configuração de '{device_name}' salva")
                    st.rerun()
                else:
                    st.error("Erro ao salvar configuração")
            else:
                st.error("Preencha todos os campos obrigatórios")
    
    # Status dos dispositivos
    devices = mikrotik.get_devices()
    if devices:
        st.markdown("### 🖥️ Status dos Dispositivos")
        
        cols = st.columns(min(len(devices), 3))  # Máximo 3 colunas
        for idx, (name, config) in enumerate(devices.items()):
            with cols[idx % 3]:
                with st.container():
                    # Testar conectividade
                    is_online, status_msg = mikrotik.test_connection(config)
                    
                    # Status visual
                    if is_online:
                        st.success(f"✅ **{name}**")
                        st.text(f"📍 {config['ip']}:{config['port']}")
                        st.caption(f"Status: {status_msg}")
                        
                        # Botões de ação
                        if st.button(f":material/sync: Sincronizar", key=f"sync_{name}"):
                            with st.spinner(f"Sincronizando {name}..."):
                                sync_success, sync_msg = mikrotik.sync_device(name, routes.get_active_routes())
                                if sync_success:
                                    st.success(f"✅ {sync_msg}")
                                else:
                                    st.error(f"❌ {sync_msg}")
                        
                        if st.button(f":material/backup: Backup", key=f"backup_{name}"):
                            with st.spinner(f"Criando backup de {name}..."):
                                backup_success, backup_msg = mikrotik.backup_config(name)
                                if backup_success:
                                    st.success(f"✅ {backup_msg}")
                                else:
                                    st.error(f"❌ {backup_msg}")
                    else:
                        st.error(f"❌ **{name}**")
                        st.text(f"📍 {config['ip']}:{config['port']}")
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
        st.markdown("### 🔄 Sincronização em Lote")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(":material/sync_alt: Sincronizar Todos os Dispositivos", use_container_width=True):
                active_routes = routes.get_active_routes()
                if active_routes:
                    with st.spinner("Sincronizando todos os dispositivos..."):
                        sync_results = mikrotik.sync_routes(active_routes)
                        
                        for device, (success, message) in sync_results.items():
                            if success:
                                st.success(f"✅ {device}: {message}")
                            else:
                                st.error(f"❌ {device}: {message}")
                else:
                    st.warning("⚠️ Nenhuma rota ativa para sincronizar")
        
        with col2:
            if st.button(":material/cloud_sync: Backup Todos os Dispositivos", use_container_width=True):
                with st.spinner("Criando backup de todos os dispositivos..."):
                    for name in devices.keys():
                        success, message = mikrotik.backup_config(name)
                        if success:
                            st.info(f"📁 {name}: {message}")
                        else:
                            st.warning(f"⚠️ {name}: {message}")
    
    # Monitoramento e estatísticas
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>monitoring</span>Monitoramento", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>analytics</span>Estatísticas de Rede", unsafe_allow_html=True)
        
        try:
            stats = vpn_manager.get_statistics()
            st.info(f"""
            **📡 Dados Transmitidos:** {stats['tx_bytes']}  
            **📡 Dados Recebidos:** {stats['rx_bytes']}  
            **📦 Pacotes Enviados:** {stats['tx_packets']}  
            **📦 Pacotes Recebidos:** {stats['rx_packets']}  
            """)
        except Exception as e:
            st.error(f"Erro ao obter estatísticas: {e}")
    
    with col2:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>speed</span>Conectividade", unsafe_allow_html=True)
        
        try:
            speed = vpn_manager.get_speed()
            st.info(f"""
            **🌐 Latência:** {speed['latency']} ms  
            **📊 Perda de Pacotes:** {speed['loss']}%  
            **⚡ Download:** {speed['download']} Mbps  
            **⚡ Upload:** {speed['upload']} Mbps  
            """)
        except Exception as e:
            st.error(f"Erro ao obter velocidade: {e}")
    
    # Informações detalhadas
    with st.expander("📊 Informações Detalhadas do Sistema"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔧 Configurações VPN:**")
            vpn_info = vpn_manager.get_connection_info()
            for key, value in vpn_info.items():
                st.text(f"{key.replace('_', ' ').title()}: {value}")
        
        with col2:
            st.markdown("**📈 Estatísticas de Rotas:**")
            route_stats = routes.get_statistics()
            for key, value in route_stats.items():
                if key != 'config_file':  # Não mostrar caminho do arquivo
                    st.text(f"{key.replace('_', ' ').title()}: {value}")
    
    # Logs do sistema
    with st.expander("📋 Ver Logs do OpenVPN"):
        log_lines = st.selectbox("Número de linhas", [20, 50, 100, 200], index=1)
        
        if st.button(":material/refresh: Carregar Logs"):
            with st.spinner("Carregando logs..."):
                try:
                    logs = vpn_manager.get_logs(lines=log_lines)
                    st.code(logs, language="text")
                except Exception as e:
                    st.error(f"Erro ao carregar logs: {e}")
    
    # Auto-refresh
    st.sidebar.markdown("---")
    auto_refresh = st.sidebar.checkbox("🔄 Auto-atualização (30s)", value=False)
    
    if auto_refresh:
        st.sidebar.markdown("⏱️ Próxima atualização em 30s")
        time.sleep(30)
        st.rerun()
    
    # Status footer
    st.sidebar.markdown("---")
    current_status = vpn_manager.get_status()
    if current_status == "connected":
        st.sidebar.success("✅ VPN Gateway Online")
    elif current_status in ["connecting", "starting"]:
        st.sidebar.warning("🔄 VPN Gateway Iniciando")
    else:
        st.sidebar.error("❌ VPN Gateway Offline")
    
    st.sidebar.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")