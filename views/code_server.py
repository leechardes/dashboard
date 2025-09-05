import streamlit as st
import subprocess
import psutil
import json
import datetime
from pathlib import Path
from components.metrics import create_metric_card

def get_code_server_status():
    """Obtém status de todos os serviços code-server"""
    users = ['devadmin', 'lee', 'diego']
    status_info = []
    
    for user in users:
        service_name = f'code-server@{user}'
        try:
            # Verificar status do serviço
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            is_active = result.stdout.strip() == 'active'
            
            # Obter informações detalhadas se ativo
            if is_active:
                # Verificar porta
                port_map = {'devadmin': 9000, 'lee': 9001, 'diego': 9002}
                port = port_map.get(user, 9000)
                
                # Verificar se processo está rodando
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'code-server' in str(proc.info['cmdline']) and str(port) in str(proc.info['cmdline']):
                            memory_mb = proc.memory_info().rss / 1024 / 1024
                            cpu_percent = proc.cpu_percent(interval=0.1)
                            
                            status_info.append({
                                'user': user,
                                'status': 'active',
                                'port': port,
                                'pid': proc.info['pid'],
                                'memory_mb': memory_mb,
                                'cpu_percent': cpu_percent
                            })
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                else:
                    status_info.append({
                        'user': user,
                        'status': 'active',
                        'port': port,
                        'pid': None,
                        'memory_mb': 0,
                        'cpu_percent': 0
                    })
            else:
                port_map = {'devadmin': 9000, 'lee': 9001, 'diego': 9002}
                status_info.append({
                    'user': user,
                    'status': 'inactive',
                    'port': port_map.get(user, 9000),
                    'pid': None,
                    'memory_mb': 0,
                    'cpu_percent': 0
                })
                
        except Exception as e:
            status_info.append({
                'user': user,
                'status': 'error',
                'port': None,
                'pid': None,
                'memory_mb': 0,
                'cpu_percent': 0,
                'error': str(e)
            })
    
    return status_info

def get_session_info():
    """Obtém informações sobre sessões ativas"""
    sessions = []
    
    # Verificar logs de autenticação
    try:
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', 'code-server-auth', '-n', '100', '--no-pager', '-o', 'json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        log = json.loads(line)
                        message = log.get('MESSAGE', '')
                        
                        # Procurar por logins bem-sucedidos
                        if 'Login bem-sucedido' in message or 'iniciado para' in message:
                            timestamp = datetime.datetime.fromtimestamp(
                                int(log.get('__REALTIME_TIMESTAMP', 0)) / 1000000
                            )
                            sessions.append({
                                'time': timestamp,
                                'message': message
                            })
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass
    
    return sessions[-10:] if sessions else []  # Últimas 10 sessões

def manage_service(user, action):
    """Gerencia serviço code-server para um usuário"""
    service_name = f'code-server@{user}'
    
    try:
        if action == 'start':
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', service_name],
                capture_output=True,
                text=True
            )
        elif action == 'stop':
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', service_name],
                capture_output=True,
                text=True
            )
        elif action == 'restart':
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', service_name],
                capture_output=True,
                text=True
            )
        else:
            return False, "Ação inválida"
        
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def run():
    """View principal do gerenciador Code-Server"""
    
    # Header principal com Material Icon
    st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">code</span>Gerenciador Code-Server</div>', unsafe_allow_html=True)
    
    # Botão para abrir Code-Server no sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>code</span>Acesso Rápido", unsafe_allow_html=True)
    
    # Botão com link direto
    st.sidebar.markdown("""
    <a href="http://10.0.10.7:8080" target="_blank" style="
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        background: var(--primary-color);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        text-decoration: none;
        font-weight: 600;
        margin-bottom: 1rem;
    ">
        <span class="material-icons">open_in_new</span>
        Abrir Code-Server
    </a>
    """, unsafe_allow_html=True)
    
    st.sidebar.info("""
    **URL:** http://10.0.10.7:8080
    **Login:** Use suas credenciais Linux
    """)
    
    st.sidebar.markdown("---")
    
    # Botão de atualizar
    if st.sidebar.button(":material/refresh: Atualizar Status"):
        st.rerun()
    
    # Obter status dos serviços
    status_info = get_code_server_status()
    
    # Métricas principais
    active_count = sum(1 for s in status_info if s['status'] == 'active')
    total_memory = sum(s.get('memory_mb', 0) for s in status_info)
    total_cpu = sum(s.get('cpu_percent', 0) for s in status_info)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card("Serviços Ativos", f"{active_count}/3", "power")
    
    with col2:
        create_metric_card("Memória Total", f"{total_memory:.0f} MB", "memory")
    
    with col3:
        create_metric_card("CPU Total", f"{total_cpu:.1f}%", "speed")
    
    with col4:
        create_metric_card("Porta Principal", "8080", "public")
    
    st.markdown("---")
    
    # Status dos usuários
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>people</span>Status dos Usuários", unsafe_allow_html=True)
    
    for user_info in status_info:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
            
            with col1:
                if user_info['status'] == 'active':
                    st.markdown(f"<span class='material-icons' style='color: var(--success-color); vertical-align: middle;'>check_circle</span> **{user_info['user']}**", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span class='material-icons' style='color: var(--text-secondary); vertical-align: middle;'>radio_button_unchecked</span> **{user_info['user']}**", unsafe_allow_html=True)
            
            with col2:
                st.text(f"Porta: {user_info['port']}")
            
            with col3:
                if user_info['pid']:
                    st.text(f"PID: {user_info['pid']}")
                else:
                    st.text("PID: -")
            
            with col4:
                if user_info['status'] == 'active':
                    st.text(f"Mem: {user_info['memory_mb']:.0f}MB")
                else:
                    st.text("Mem: -")
            
            with col5:
                subcol1, subcol2, subcol3 = st.columns(3)
                
                with subcol1:
                    if user_info['status'] != 'active':
                        if st.button(":material/play_arrow: Iniciar", key=f"start_{user_info['user']}"):
                            success, msg = manage_service(user_info['user'], 'start')
                            if success:
                                st.success(f"Serviço iniciado para {user_info['user']}")
                                st.rerun()
                            else:
                                st.error(f"Erro ao iniciar: {msg}")
                
                with subcol2:
                    if user_info['status'] == 'active':
                        if st.button(":material/stop: Parar", key=f"stop_{user_info['user']}"):
                            success, msg = manage_service(user_info['user'], 'stop')
                            if success:
                                st.success(f"Serviço parado para {user_info['user']}")
                                st.rerun()
                            else:
                                st.error(f"Erro ao parar: {msg}")
                
                with subcol3:
                    if user_info['status'] == 'active':
                        if st.button(":material/restart_alt: Reiniciar", key=f"restart_{user_info['user']}"):
                            success, msg = manage_service(user_info['user'], 'restart')
                            if success:
                                st.success(f"Serviço reiniciado para {user_info['user']}")
                                st.rerun()
                            else:
                                st.error(f"Erro ao reiniciar: {msg}")
    
    st.markdown("---")
    
    # Configurações do sistema
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>settings</span>Configurações do Sistema", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>schedule</span>Auto-Stop", unsafe_allow_html=True)
        st.info("""
        **Configurado:** 4 horas de inatividade
        **Status:** Ativo
        **Timer:** systemd timer ativo
        """)
    
    with col2:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>login</span>Auto-Start", unsafe_allow_html=True)
        st.info("""
        **Configurado:** Ao fazer login
        **Backend:** Flask + PAM
        **Porta:** 8080 (nginx proxy)
        """)
    
    # Sessões recentes
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>history</span>Sessões Recentes", unsafe_allow_html=True)
    
    sessions = get_session_info()
    if sessions:
        for session in sessions[-5:]:  # Mostrar últimas 5
            col1, col2 = st.columns([1, 3])
            with col1:
                st.text(session['time'].strftime('%d/%m %H:%M'))
            with col2:
                st.text(session['message'][:80])
    else:
        st.info("Nenhuma sessão recente encontrada")
    
    # Informações de serviços
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>info</span>Informações dos Serviços", unsafe_allow_html=True)
    
    with st.expander("Detalhes dos Serviços Systemd"):
        services = ['nginx', 'code-server-auth', 'code-server-inactivity.timer']
        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True
                )
                status = result.stdout.strip()
                
                if status == 'active':
                    st.success(f"{service}: {status}")
                else:
                    st.warning(f"{service}: {status}")
            except:
                st.error(f"{service}: erro ao verificar")
    
    with st.expander("Arquivos de Configuração"):
        st.code("""
/etc/nginx/sites-available/code-server-login
/etc/systemd/system/code-server@.service
/etc/systemd/system/code-server-auth.service
/etc/systemd/system/code-server-inactivity.service
/etc/systemd/system/code-server-inactivity.timer
/var/www/code-server-login/auth_server.py
/usr/local/share/code-server-scripts/check-inactivity.sh
/usr/local/share/code-server-scripts/get-user-port.sh
        """)
    
    # Ações administrativas
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>admin_panel_settings</span>Ações Administrativas", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(":material/restart_alt: Reiniciar Nginx"):
            try:
                subprocess.run(['sudo', 'systemctl', 'restart', 'nginx'], check=True)
                st.success("Nginx reiniciado com sucesso")
            except:
                st.error("Erro ao reiniciar nginx")
    
    with col2:
        if st.button(":material/restart_alt: Reiniciar Auth"):
            try:
                subprocess.run(['sudo', 'systemctl', 'restart', 'code-server-auth'], check=True)
                st.success("Serviço de autenticação reiniciado")
            except:
                st.error("Erro ao reiniciar autenticação")
    
    with col3:
        if st.button(":material/description: Ver Logs"):
            with st.expander("Logs Recentes"):
                try:
                    result = subprocess.run(
                        ['sudo', 'journalctl', '-u', 'code-server-auth', '-n', '20', '--no-pager'],
                        capture_output=True,
                        text=True
                    )
                    st.code(result.stdout)
                except:
                    st.error("Erro ao obter logs")