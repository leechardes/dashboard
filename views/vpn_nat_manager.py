import streamlit as st
import pandas as pd
from datetime import datetime
import time
import logging
from typing import Dict, List, Optional
import json

# Importar componentes locais
from components.mikrotik_vpn import MikroTikVPN
from components.mikrotik_nat import MikroTikNAT
from components.metrics import create_metric_card, create_alert_metric, create_status_metric

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_session_state():
    """Inicializa variáveis da sessão"""
    if 'vpn_manager' not in st.session_state:
        st.session_state.vpn_manager = MikroTikVPN()
    if 'nat_manager' not in st.session_state:
        st.session_state.nat_manager = MikroTikNAT()
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    if 'show_passwords' not in st.session_state:
        st.session_state.show_passwords = False

def render_vpn_users_tab():
    """Renderiza tab de Usuários VPN"""
    st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>vpn_key</span>Gerenciamento de Usuários VPN", unsafe_allow_html=True)
    
    # Seção de Adicionar Usuário
    with st.expander("Adicionar Novo Usuário VPN"):
        st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>person_add</span>Novo Usuário", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Nome do Usuário", placeholder="Digite o nome do usuário")
            site_options = ["matriz", "escritorio"]
            selected_site = st.selectbox("Site", site_options)
        
        with col2:
            generate_password = st.checkbox("Gerar senha automaticamente", value=True)
            if not generate_password:
                custom_password = st.text_input("Senha", type="password", placeholder="Mínimo 8 caracteres")
            else:
                custom_password = None
            
            custom_ip = st.text_input("IP Específico (opcional)", placeholder="Deixe vazio para automático")
        
        if st.button(":material/person_add: Criar Usuário", type="primary"):
            if new_username.strip():
                with st.spinner("Criando usuário VPN..."):
                    result = st.session_state.vpn_manager.add_user(
                        username=new_username.strip(),
                        password=custom_password if not generate_password else None,
                        ip_address=custom_ip.strip() if custom_ip.strip() else None,
                        site=selected_site
                    )
                
                if result["success"]:
                    st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Usuário '{result['data']['username']}' criado com sucesso!")
                    st.info(f"**IP:** {result['data']['ip_address']}")
                    if generate_password:
                        st.info(f"**Senha:** `{result['data']['password']}`")
                    st.rerun()
                else:
                    st.error(f"<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Erro: {result['message']}")
            else:
                st.error("<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Nome do usuário é obrigatório")
    
    # Lista de Usuários
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>people</span>Usuários Configurados", unsafe_allow_html=True)
    
    with st.spinner("Carregando usuários..."):
        users = st.session_state.vpn_manager.list_users()
        active_connections = st.session_state.vpn_manager.get_active_connections()
    
    if users:
        # Criar DataFrame com informações dos usuários
        user_data = []
        for user in users:
            # Verificar se está conectado
            is_connected = any(conn.get("name", "").lower() == user.get("name", "").lower() 
                             for conn in active_connections)
            
            user_data.append({
                "Usuário": user.get("name", "N/A"),
                "IP": user.get("remote-address", "N/A"),
                "Perfil": user.get("profile", "N/A"),
                "Status": "<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Online" if is_connected else "<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Offline",
                "Ações": user.get("name", "")
            })
        
        df = pd.DataFrame(user_data)
        
        # Exibir tabela
        st.dataframe(df.drop("Ações", axis=1), use_container_width=True)
        
        # Ações para cada usuário
        st.markdown("##### Ações")
        for i, user in enumerate(users):
            username = user.get("name", "N/A")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.text(f"{username}")
            
            with col2:
                if st.button(":material/refresh: Nova Senha", key=f"pwd_{i}"):
                    new_pwd = st.session_state.vpn_manager.generate_secure_password()
                    result = st.session_state.vpn_manager.change_user_password(username, new_pwd)
                    if result["success"]:
                        st.success(f"Nova senha para {username}: `{new_pwd}`")
                    else:
                        st.error(result["message"])
            
            with col3:
                # Verificar se está conectado
                is_connected = any(conn.get("name", "").lower() == username.lower() 
                                 for conn in active_connections)
                if is_connected:
                    if st.button(":material/logout: Desconectar", key=f"disc_{i}"):
                        result = st.session_state.vpn_manager.disconnect_user(username)
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                else:
                    st.text("Desconectado")
            
            with col4:
                if st.button(":material/info: Detalhes", key=f"info_{i}"):
                    stats = st.session_state.vpn_manager.get_user_stats(username)
                    if stats.get("status") == "connected":
                        st.json(stats)
                    else:
                        st.info(f"Status: {stats.get('status', 'N/A')}")
            
            with col5:
                if st.button(":material/delete: Remover", key=f"del_{i}", type="secondary"):
                    st.session_state[f"confirm_delete_user_{username}"] = True
            
            # Confirmação de exclusão
            if st.session_state.get(f"confirm_delete_user_{username}", False):
                st.warning(f"<span class='material-icons' style='color: orange; vertical-align: middle; margin-right: 0.5rem;'>warning</span>Confirma exclusão do usuário **{username}**?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Confirmar", key=f"confirm_del_{i}", type="secondary"):
                        result = st.session_state.vpn_manager.remove_user(username)
                        if result["success"]:
                            st.success(result["message"])
                            del st.session_state[f"confirm_delete_user_{username}"]
                            st.rerun()
                        else:
                            st.error(result["message"])
                with col_no:
                    if st.button("Cancelar", key=f"cancel_del_{i}"):
                        del st.session_state[f"confirm_delete_user_{username}"]
                        st.rerun()
            
            st.divider()
    
    else:
        st.info("Nenhum usuário VPN configurado")

def render_port_forwarding_tab():
    """Renderiza tab de Port Forwarding"""
    st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>Gerenciamento de Port Forwarding", unsafe_allow_html=True)
    
    # Seção de Adicionar Regra
    with st.expander("Adicionar Nova Regra"):
        st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>add_circle</span>Nova Regra NAT", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Seletor de servidor conhecido
            known_servers = st.session_state.nat_manager.get_known_servers()
            server_options = ["IP personalizado"] + [f"{ip} - {name}" for ip, name in known_servers.items()]
            selected_server = st.selectbox("Servidor", server_options)
            
            if selected_server == "IP personalizado":
                internal_ip = st.text_input("IP Interno", placeholder="10.0.10.x")
            else:
                internal_ip = selected_server.split(" - ")[0]
                st.text_input("IP Interno", value=internal_ip, disabled=True)
            
            internal_port = st.number_input("Porta Interna", min_value=1, max_value=65535, value=80)
        
        with col2:
            protocol = st.selectbox("Protocolo", ["tcp", "udp"])
            
            # Sugerir porta externa
            if internal_ip and internal_port:
                suggested_port = st.session_state.nat_manager.suggest_port(internal_port, protocol)
                external_port = st.number_input("Porta Externa", min_value=1, max_value=65535, 
                                               value=suggested_port if suggested_port else internal_port)
            else:
                external_port = st.number_input("Porta Externa", min_value=1, max_value=65535, value=80)
            
            comment = st.text_input("Comentário (opcional)", placeholder="Descrição da regra")
        
        # Verificar disponibilidade da porta
        if external_port:
            port_check = st.session_state.nat_manager.check_port_available(external_port, protocol)
            if port_check["available"]:
                st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Porta {external_port}/{protocol} está disponível")
            else:
                st.error(f"<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>{port_check['reason']}")
                if "used_by" in port_check:
                    st.info(f"Usada por: {port_check['used_by']}")
        
        if st.button(":material/add_circle: Criar Regra", type="primary"):
            if internal_ip and internal_port and external_port:
                with st.spinner("Criando regra NAT..."):
                    result = st.session_state.nat_manager.add_port_forward(
                        internal_ip=internal_ip,
                        internal_port=internal_port,
                        external_port=external_port,
                        protocol=protocol,
                        comment=comment
                    )
                
                if result["success"]:
                    st.success("<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Regra de port forwarding criada com sucesso!")
                    
                    # Mostrar informações da regra criada
                    data = result["data"]
                    st.info(f"**Redirecionamento:** {data['external_port']} → {data['internal_ip']}:{data['internal_port']} ({data['protocol'].upper()})")
                    
                    # Status da porta interna
                    port_test = data.get("port_test", {})
                    if port_test.get("reachable"):
                        st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Porta interna {data['internal_ip']}:{data['internal_port']} está ativa")
                    else:
                        st.warning(f"<span class='material-icons' style='color: orange; vertical-align: middle; margin-right: 0.5rem;'>warning</span>Porta interna pode não estar ativa: {port_test.get('reason', 'N/A')}")
                    
                    st.rerun()
                else:
                    st.error(f"<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Erro: {result['message']}")
            else:
                st.error("<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Todos os campos são obrigatórios")
    
    # Lista de Regras
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>list</span>Regras Configuradas", unsafe_allow_html=True)
    
    with st.spinner("Carregando regras NAT..."):
        rules = st.session_state.nat_manager.list_nat_rules()
    
    if rules:
        # Criar DataFrame com as regras
        rule_data = []
        for rule in rules:
            status_icon = "<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>" if rule.get("status") == "active" else "<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>"
            rule_data.append({
                "Status": f"{status_icon} {'Ativa' if rule.get('status') == 'active' else 'Inativa'}",
                "Porta Externa": rule.get("dst_port", "N/A"),
                "Protocolo": rule.get("protocol", "N/A").upper(),
                "IP Interno": rule.get("to_addresses", "N/A"),
                "Porta Interna": rule.get("to_ports", "N/A"),
                "Servidor": rule.get("server_name", "Desconhecido"),
                "Comentário": rule.get("comment", "N/A"),
                "ID": rule.get("id", "N/A")
            })
        
        df = pd.DataFrame(rule_data)
        st.dataframe(df.drop("ID", axis=1), use_container_width=True)
        
        # Ações para cada regra
        st.markdown("##### Ações")
        for i, rule in enumerate(rules):
            rule_id = rule.get("id", "N/A")
            external_port = rule.get("dst_port", "N/A")
            internal_target = f"{rule.get('to_addresses', 'N/A')}:{rule.get('to_ports', 'N/A')}"
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.text(f"<span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>sync</span>{external_port} → {internal_target}")
            
            with col2:
                is_active = rule.get("status") == "active"
                if is_active:
                    if st.button(":material/pause: Desabilitar", key=f"disable_{i}"):
                        result = st.session_state.nat_manager.toggle_rule(rule_id, False)
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                else:
                    if st.button(":material/play_arrow: Habilitar", key=f"enable_{i}"):
                        result = st.session_state.nat_manager.toggle_rule(rule_id, True)
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
            
            with col3:
                if st.button(":material/network_ping: Testar", key=f"test_{i}"):
                    ip = rule.get("to_addresses")
                    port = rule.get("to_ports")
                    protocol = rule.get("protocol", "tcp")
                    
                    if ip and port:
                        result = st.session_state.nat_manager.test_port(ip, int(port), protocol)
                        if result["reachable"]:
                            st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>{ip}:{port} está alcançável")
                        else:
                            st.error(f"<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>{result['reason']}")
            
            with col4:
                if st.button(":material/info: Detalhes", key=f"details_{i}"):
                    st.json(rule)
            
            with col5:
                if st.button(":material/delete: Remover", key=f"remove_{i}", type="secondary"):
                    st.session_state[f"confirm_delete_rule_{rule_id}"] = True
            
            # Confirmação de exclusão
            if st.session_state.get(f"confirm_delete_rule_{rule_id}", False):
                st.warning(f"<span class='material-icons' style='color: orange; vertical-align: middle; margin-right: 0.5rem;'>warning</span>Confirma exclusão da regra **{external_port} → {internal_target}**?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Confirmar", key=f"confirm_rule_{i}", type="secondary"):
                        result = st.session_state.nat_manager.remove_port_forward(rule_id=rule_id)
                        if result["success"]:
                            st.success(result["message"])
                            del st.session_state[f"confirm_delete_rule_{rule_id}"]
                            st.rerun()
                        else:
                            st.error(result["message"])
                with col_no:
                    if st.button("Cancelar", key=f"cancel_rule_{i}"):
                        del st.session_state[f"confirm_delete_rule_{rule_id}"]
                        st.rerun()
            
            st.divider()
    else:
        st.info("Nenhuma regra de port forwarding configurada")

def render_quick_services_tab():
    """Renderiza tab de Serviços Rápidos"""
    st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>flash_on</span>Serviços Rápidos", unsafe_allow_html=True)
    
    # Templates de serviços
    service_templates = st.session_state.nat_manager.get_service_templates()
    known_servers = st.session_state.nat_manager.get_known_servers()
    
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>apps</span>Templates de Serviços", unsafe_allow_html=True)
    st.info("Configure rapidamente port forwarding para serviços comuns")
    
    # Seleção de servidor e serviço
    col1, col2 = st.columns(2)
    
    with col1:
        server_options = [f"{ip} - {name}" for ip, name in known_servers.items()]
        if server_options:
            selected_server = st.selectbox("Selecione o Servidor", server_options)
            target_ip = selected_server.split(" - ")[0]
        else:
            target_ip = st.text_input("IP do Servidor", placeholder="10.0.10.x")
    
    with col2:
        service_options = [f"{key} - {info['name']} ({info['port']}/{info['protocol']})" 
                          for key, info in service_templates.items()]
        selected_service = st.selectbox("Selecione o Serviço", service_options)
        service_key = selected_service.split(" - ")[0]
        service_info = service_templates[service_key]
    
    # Mostrar informações do serviço
    st.markdown("##### Detalhes do Serviço")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Porta Padrão", service_info["port"])
    with col2:
        st.metric("Protocolo", service_info["protocol"].upper())
    with col3:
        # Verificar se porta está disponível
        port_check = st.session_state.nat_manager.check_port_available(service_info["port"], service_info["protocol"])
        status = "Disponível" if port_check["available"] else "Em Uso"
        st.metric("Status da Porta", status)
    
    # Opções de configuração
    st.markdown("##### Configurações")
    col1, col2 = st.columns(2)
    
    with col1:
        use_default_port = st.checkbox("Usar porta padrão como externa", value=True)
        if not use_default_port:
            suggested_port = st.session_state.nat_manager.suggest_port(service_info["port"], service_info["protocol"])
            external_port = st.number_input("Porta Externa", min_value=1, max_value=65535,
                                           value=suggested_port if suggested_port else service_info["port"] + 1000)
        else:
            external_port = service_info["port"]
    
    with col2:
        custom_comment = st.text_input("Comentário personalizado", 
                                      placeholder=f"Deixe vazio para usar: {service_info['name']}")
    
    # Botão de criação
    if st.button(f":material/flash_on: Configurar {service_info['name']}", type="primary"):
        if target_ip:
            comment = custom_comment if custom_comment else f"{service_info['name']} - Configurado via Dashboard"
            
            with st.spinner(f"Configurando {service_info['name']}..."):
                result = st.session_state.nat_manager.add_port_forward(
                    internal_ip=target_ip,
                    internal_port=service_info["port"],
                    external_port=external_port,
                    protocol=service_info["protocol"],
                    comment=comment
                )
            
            if result["success"]:
                st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>{service_info['name']} configurado com sucesso!")
                
                data = result["data"]
                st.info(f"**Acesso externo:** {data['external_port']}/{data['protocol'].upper()}")
                st.info(f"**Redirecionamento:** {data['external_port']} → {data['internal_ip']}:{data['internal_port']}")
                
                # Status da conectividade
                port_test = data.get("port_test", {})
                if port_test.get("reachable"):
                    st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Serviço está ativo em {data['internal_ip']}:{data['internal_port']}")
                else:
                    st.warning(f"<span class='material-icons' style='color: orange; vertical-align: middle; margin-right: 0.5rem;'>warning</span>Serviço pode não estar ativo: {port_test.get('reason', 'N/A')}")
                    
            else:
                st.error(f"<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Erro: {result['message']}")
        else:
            st.error("<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Selecione um servidor")
    
    # Seção de Serviços Populares
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>star</span>Serviços Populares", unsafe_allow_html=True)
    
    popular_services = ["web", "https", "ssh", "rdp", "streamlit"]
    cols = st.columns(len(popular_services))
    
    for i, service_key in enumerate(popular_services):
        service = service_templates[service_key]
        with cols[i]:
            with st.container():
                st.markdown(f"**{service['name']}**")
                st.text(f"Porta: {service['port']}")
                st.text(f"Protocolo: {service['protocol'].upper()}")
                
                if st.button(f"Configurar", key=f"quick_{service_key}"):
                    st.session_state[f"selected_quick_service"] = service_key
                    st.rerun()
    
    # Configuração rápida se serviço foi selecionado
    if st.session_state.get("selected_quick_service"):
        selected_key = st.session_state["selected_quick_service"]
        selected_service = service_templates[selected_key]
        
        st.markdown(f"##### Configuração Rápida: {selected_service['name']}")
        
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            quick_server_options = [f"{ip} - {name}" for ip, name in known_servers.items()]
            quick_selected_server = st.selectbox("Servidor", quick_server_options, key="quick_server")
            quick_target_ip = quick_selected_server.split(" - ")[0]
        
        with quick_col2:
            quick_external_port = st.number_input("Porta Externa", value=selected_service["port"], key="quick_port")
        
        with quick_col3:
            if st.button(f":material/flash_on: Configurar Agora", type="primary", key="quick_config"):
                comment = f"{selected_service['name']} - Configuração Rápida"
                
                result = st.session_state.nat_manager.add_port_forward(
                    internal_ip=quick_target_ip,
                    internal_port=selected_service["port"],
                    external_port=quick_external_port,
                    protocol=selected_service["protocol"],
                    comment=comment
                )
                
                if result["success"]:
                    st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>{selected_service['name']} configurado!")
                    del st.session_state["selected_quick_service"]
                    st.rerun()
                else:
                    st.error(f"<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>{result['message']}")

def render_monitoring_tab():
    """Renderiza tab de Monitoramento"""
    st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>monitoring</span>Monitoramento e Status", unsafe_allow_html=True)
    
    # Status da conexão
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>Status do MikroTik", unsafe_allow_html=True)
        
        if st.button(":material/refresh: Testar Conexão"):
            with st.spinner("Testando conexão..."):
                vpn_test = st.session_state.vpn_manager.test_connection()
                nat_test = st.session_state.nat_manager.test_connection()
            
            if vpn_test["success"] and nat_test["success"]:
                st.success("<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Conexão estabelecida com sucesso")
                if vpn_test.get("identity"):
                    st.info(f"Identidade: {vpn_test['identity']}")
            else:
                st.error("<span class='material-icons' style='color: red; vertical-align: middle; margin-right: 0.5rem;'>cancel</span>Erro de conexão")
                st.error(vpn_test["message"])
    
    with col2:
        st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>schedule</span>Última Atualização", unsafe_allow_html=True)
        last_refresh = st.session_state.get('last_refresh', datetime.now())
        st.info(f"<span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>schedule</span>{last_refresh.strftime('%H:%M:%S')}")
        
        if st.button(":material/refresh: Atualizar Dados"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    # Métricas VPN
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>vpn_key</span>Estatísticas VPN", unsafe_allow_html=True)
    
    with st.spinner("Carregando dados VPN..."):
        vpn_status = st.session_state.vpn_manager.get_vpn_status()
    
    if "error" not in vpn_status:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card("Usuários Total", vpn_status.get("total_users", 0), "people")
        
        with col2:
            create_metric_card("Conexões Ativas", vpn_status.get("active_connections", 0), "link")
        
        with col3:
            sites = vpn_status.get("sites", [])
            create_metric_card("Sites", len(sites), "location_on")
        
        with col4:
            # Calcular total de IPs disponíveis
            total_available = sum(site_info.get("available", 0) 
                                for site_info in vpn_status.get("available_ips", {}).values())
            create_metric_card("IPs Disponíveis", total_available, "dns")
        
        # Detalhes por site
        st.markdown("##### Disponibilidade por Site")
        available_ips = vpn_status.get("available_ips", {})
        
        for site, info in available_ips.items():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Site: {site.title()}", f"{info['available']}/{info['total']}")
            with col2:
                st.metric("IPs Fixos", info['fixed'])
            with col3:
                usage_percent = ((info['total'] - info['available']) / info['total'] * 100) if info['total'] > 0 else 0
                st.metric("Uso", f"{usage_percent:.1f}%")
    
    # Métricas NAT
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>Estatísticas NAT", unsafe_allow_html=True)
    
    with st.spinner("Carregando dados NAT..."):
        nat_stats = st.session_state.nat_manager.get_nat_stats()
    
    if "error" not in nat_stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card("Regras Total", nat_stats.get("total_rules", 0), "rule")
        
        with col2:
            create_metric_card("Regras Ativas", nat_stats.get("active_rules", 0), "check_circle")
        
        with col3:
            create_metric_card("Regras Inativas", nat_stats.get("disabled_rules", 0), "cancel")
        
        with col4:
            protocol_stats = nat_stats.get("protocol_stats", {})
            tcp_count = protocol_stats.get("tcp", 0)
            create_metric_card("Regras TCP", tcp_count, "language")
        
        # Gráficos e estatísticas detalhadas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top Servidores")
            server_stats = nat_stats.get("server_stats", {})
            if server_stats:
                server_df = pd.DataFrame(list(server_stats.items()), columns=["Servidor", "Regras"])
                server_df = server_df.sort_values("Regras", ascending=False).head(5)
                st.dataframe(server_df, use_container_width=True)
            else:
                st.info("Nenhum dado disponível")
        
        with col2:
            st.markdown("##### Protocolos")
            protocol_stats = nat_stats.get("protocol_stats", {})
            if protocol_stats:
                protocol_df = pd.DataFrame(list(protocol_stats.items()), columns=["Protocolo", "Quantidade"])
                st.dataframe(protocol_df, use_container_width=True)
            else:
                st.info("Nenhum dado disponível")
    
    # Conexões VPN Ativas
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>link</span>Conexões VPN Ativas", unsafe_allow_html=True)
    
    with st.spinner("Carregando conexões ativas..."):
        active_connections = st.session_state.vpn_manager.get_active_connections()
    
    if active_connections:
        conn_data = []
        for conn in active_connections:
            conn_data.append({
                "Usuário": conn.get("name", "N/A"),
                "IP": conn.get("address", "N/A"),
                "Tempo Ativo": conn.get("uptime", "N/A"),
                "Origem": conn.get("caller-id", "N/A"),
                "Dados Recebidos": conn.get("bytes-in", "0"),
                "Dados Enviados": conn.get("bytes-out", "0")
            })
        
        conn_df = pd.DataFrame(conn_data)
        st.dataframe(conn_df, use_container_width=True)
    else:
        st.info("Nenhuma conexão VPN ativa no momento")
    
    # Scan de Rede (básico)
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>network_check</span>Scan de Rede", unsafe_allow_html=True)
    
    if st.button(":material/network_check: Escanear Rede Local"):
        with st.spinner("Escaneando rede 10.0.10.0/24..."):
            active_hosts = st.session_state.nat_manager.scan_local_network()
        
        if active_hosts:
            st.success(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>{len(active_hosts)} hosts ativos encontrados")
            
            host_data = []
            for host in active_hosts:
                host_data.append({
                    "IP": host["ip"],
                    "Nome": host["name"],
                    "Status": "<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>Ativo"
                })
            
            host_df = pd.DataFrame(host_data)
            st.dataframe(host_df, use_container_width=True)
        else:
            st.warning("Nenhum host ativo encontrado no scan")
    
    # Relatório de Uso de Portas
    st.markdown("#### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>analytics</span>Relatório de Portas", unsafe_allow_html=True)
    
    if st.button(":material/analytics: Gerar Relatório"):
        with st.spinner("Gerando relatório..."):
            report = st.session_state.nat_manager.get_port_usage_report()
        
        if "error" not in report:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Portas em Uso")
                used_ports = report.get("used_ports", [])
                if used_ports:
                    used_df = pd.DataFrame(used_ports)
                    st.dataframe(used_df.head(10), use_container_width=True)
                else:
                    st.info("Nenhuma porta em uso")
            
            with col2:
                st.markdown("##### Faixas Disponíveis")
                available_ranges = report.get("available_ranges", [])
                if available_ranges:
                    for range_str in available_ranges[:5]:
                        st.text(f"<span class='material-icons' style='color: green; vertical-align: middle; margin-right: 0.5rem;'>check_circle</span>{range_str}")
                else:
                    st.info("Nenhuma faixa grande disponível")
            
            # Recomendações
            recommendations = report.get("recommendations", [])
            if recommendations:
                st.markdown("##### Recomendações")
                for rec in recommendations:
                    st.warning(f"<span class='material-icons' style='color: orange; vertical-align: middle; margin-right: 0.5rem;'>warning</span>{rec}")

def run():
    """Função principal da aplicação"""
    # Carregar CSS adaptativo
    try:
        with open('/srv/projects/shared/dashboard/static/adaptive_theme.css', 'r') as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback CSS se o arquivo não existir
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        
        :root {
            --bg-primary: var(--background-color);
            --text-primary: var(--text-color);
            --bg-secondary: var(--secondary-background-color);
            --text-secondary: var(--text-color-secondary);
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --info-color: #3b82f6;
            --border-color: rgba(128, 128, 128, 0.2);
        }
        
        .main-header {
            padding: 1.5rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            margin-bottom: 1.5rem;
            border-left: 4px solid var(--info-color);
            display: flex;
            align-items: center;
            gap: 1rem;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .material-icons,
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            vertical-align: middle;
        }
        
        .metric-card {
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">security</span>Gerenciador VPN e NAT</div>', unsafe_allow_html=True)
    
    # Inicializar session state
    init_session_state()
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "Usuários VPN",
        "Port Forwarding", 
        "Serviços Rápidos",
        "Monitoramento"
    ])
    
    with tab1:
        render_vpn_users_tab()
    
    with tab2:
        render_port_forwarding_tab()
    
    with tab3:
        render_quick_services_tab()
    
    with tab4:
        render_monitoring_tab()
    
    # Footer com informações
    st.markdown("---")
    st.markdown(
        f"<small style='color: var(--text-color-secondary);'>"
        f"<span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>build</span>MikroTik Manager | "
        f"<span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>router</span>{st.session_state.vpn_manager.host} | "
        f"<span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>schedule</span>Atualizado: {st.session_state.last_refresh.strftime('%H:%M:%S')}"
        f"</small>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    run()