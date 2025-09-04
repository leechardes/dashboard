import streamlit as st
import psutil
import platform
import socket
import datetime
import os
from utils.system_monitor import get_detailed_system_info, get_network_info, get_process_info

def run():
    """Detailed system information view"""
    
    st.markdown('<div class="main-header">🖥️ Informações Detalhadas do Sistema</div>', unsafe_allow_html=True)
    
    # Refresh button
    if st.sidebar.button("🔄 Atualizar Informações"):
        st.rerun()
    
    # System overview
    st.subheader("🖥️ Visão Geral do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Basic system info
        st.info(f"""
        **🏠 Hostname:** {socket.gethostname()}
        **🖥️ Sistema:** {platform.system()} {platform.release()}
        **🏗️ Arquitetura:** {platform.machine()}
        **🐍 Python:** {platform.python_version()}
        **👤 Usuário:** {os.getenv('USER', 'N/A')}
        """)
    
    with col2:
        # Uptime and boot info
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        
        st.info(f"""
        **⏰ Boot Time:** {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
        **⏱️ Uptime:** {uptime.days} dias, {uptime.seconds//3600}h {(uptime.seconds//60)%60}m
        **🌐 IP Local:** {socket.gethostbyname(socket.gethostname())}
        **🔧 PID Atual:** {os.getpid()}
        **📁 Working Dir:** {os.getcwd()}
        """)
    
    # Hardware Information
    st.markdown("---")
    st.subheader("🔧 Informações de Hardware")
    
    # CPU Information
    st.markdown("### 🖥️ Processador")
    cpu_col1, cpu_col2 = st.columns(2)
    
    with cpu_col1:
        cpu_info = get_detailed_system_info()['cpu']
        st.info(f"""
        **Modelo:** {cpu_info.get('model', 'N/A')}
        **Cores Físicos:** {cpu_info['physical_cores']}
        **Cores Lógicos:** {cpu_info['logical_cores']}
        **Frequência Base:** {cpu_info['base_frequency']:.2f} MHz
        **Frequência Atual:** {cpu_info['current_frequency']:.2f} MHz
        """)
    
    with cpu_col2:
        # CPU usage per core
        cpu_percents = psutil.cpu_percent(percpu=True, interval=1)
        st.markdown("**Uso por Core:**")
        for i, percent in enumerate(cpu_percents):
            st.progress(percent/100, text=f"Core {i+1}: {percent}%")
    
    # Memory Information
    st.markdown("### 💾 Memória")
    memory_col1, memory_col2 = st.columns(2)
    
    with memory_col1:
        memory = psutil.virtual_memory()
        st.info(f"""
        **Total:** {memory.total / (1024**3):.2f} GB
        **Disponível:** {memory.available / (1024**3):.2f} GB
        **Usado:** {memory.used / (1024**3):.2f} GB
        **Percentual:** {memory.percent}%
        **Buffers:** {memory.buffers / (1024**2):.0f} MB
        **Cache:** {memory.cached / (1024**2):.0f} MB
        """)
    
    with memory_col2:
        # Swap memory
        swap = psutil.swap_memory()
        st.info(f"""
        **Swap Total:** {swap.total / (1024**3):.2f} GB
        **Swap Usado:** {swap.used / (1024**3):.2f} GB
        **Swap Livre:** {swap.free / (1024**3):.2f} GB
        **Swap %:** {swap.percent}%
        **Swap In:** {swap.sin / (1024**2):.0f} MB
        **Swap Out:** {swap.sout / (1024**2):.0f} MB
        """)
    
    # Disk Information
    st.markdown("### 💽 Armazenamento")
    
    # Get all disk partitions
    partitions = psutil.disk_partitions()
    
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            
            st.markdown(f"**📁 {partition.mountpoint}** ({partition.fstype})")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💽 Total", f"{partition_usage.total / (1024**3):.1f} GB")
            
            with col2:
                st.metric("✅ Livre", f"{partition_usage.free / (1024**3):.1f} GB")
            
            with col3:
                used_percent = (partition_usage.used / partition_usage.total) * 100
                st.metric("⚠️ Usado", f"{used_percent:.1f}%")
            
            # Progress bar for disk usage
            st.progress(used_percent/100)
            
        except PermissionError:
            st.warning(f"Sem permissão para acessar {partition.mountpoint}")
        
        st.markdown("---")
    
    # Network Information
    st.markdown("### 🌐 Informações de Rede")
    
    network_info = get_network_info()
    
    # Network interfaces
    net_col1, net_col2 = st.columns(2)
    
    with net_col1:
        st.markdown("**🔌 Interfaces de Rede:**")
        for interface, addresses in network_info['interfaces'].items():
            st.text(f"• {interface}")
            for addr in addresses:
                # addr is a dict from _asdict()
                if isinstance(addr, dict):
                    # socket.AF_INET value is 2, socket.AF_INET6 is 10
                    if addr.get('family') == 2:  # IPv4
                        st.text(f"  IPv4: {addr.get('address', 'N/A')}")
                    elif addr.get('family') == 10:  # IPv6
                        st.text(f"  IPv6: {addr.get('address', 'N/A')}")
    
    with net_col2:
        st.markdown("**📊 Estatísticas de Rede:**")
        net_stats = psutil.net_io_counters()
        st.text(f"Bytes Enviados: {net_stats.bytes_sent / (1024**2):.1f} MB")
        st.text(f"Bytes Recebidos: {net_stats.bytes_recv / (1024**2):.1f} MB")
        st.text(f"Pacotes Enviados: {net_stats.packets_sent:,}")
        st.text(f"Pacotes Recebidos: {net_stats.packets_recv:,}")
        st.text(f"Erros de Entrada: {net_stats.errin}")
        st.text(f"Erros de Saída: {net_stats.errout}")
    
    # Active connections
    st.markdown("---")
    st.subheader("🔗 Conexões Ativas")
    
    show_connections = st.checkbox("Mostrar conexões de rede ativas")
    if show_connections:
        try:
            connections = psutil.net_connections(kind='inet')
            active_connections = [conn for conn in connections if conn.status == 'ESTABLISHED']
            
            if active_connections:
                conn_data = []
                for conn in active_connections[:20]:  # Limit to 20 connections
                    local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                    remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    
                    conn_data.append({
                        'Protocolo': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                        'Endereço Local': local_addr,
                        'Endereço Remoto': remote_addr,
                        'Status': conn.status,
                        'PID': conn.pid or 'N/A'
                    })
                
                import pandas as pd
                df = pd.DataFrame(conn_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nenhuma conexão ativa encontrada.")
        
        except Exception as e:
            st.error(f"Erro ao obter conexões: {str(e)}")
    
    # Process Information
    st.markdown("---")
    st.subheader("🔄 Informações de Processos")
    
    process_col1, process_col2 = st.columns(2)
    
    with process_col1:
        total_processes = len(psutil.pids())
        running_processes = len([p for p in psutil.process_iter() if p.status() == 'running'])
        sleeping_processes = len([p for p in psutil.process_iter() if p.status() == 'sleeping'])
        
        st.metric("📊 Total de Processos", total_processes)
        st.metric("🏃 Em Execução", running_processes)
        st.metric("😴 Dormindo", sleeping_processes)
    
    with process_col2:
        # Top processes by memory
        st.markdown("**🔝 Top 5 Processos (Memória):**")
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            for proc in processes[:5]:
                st.text(f"• {proc['name']} ({proc['pid']}): {proc['memory_percent']:.1f}%")
        
        except Exception as e:
            st.error(f"Erro ao obter processos: {str(e)}")
    
    # System load (Linux/Unix only)
    try:
        load_avg = os.getloadavg()
        st.markdown("---")
        st.subheader("📈 Carga do Sistema")
        
        load_col1, load_col2, load_col3 = st.columns(3)
        
        with load_col1:
            st.metric("1 minuto", f"{load_avg[0]:.2f}")
        
        with load_col2:
            st.metric("5 minutos", f"{load_avg[1]:.2f}")
        
        with load_col3:
            st.metric("15 minutos", f"{load_avg[2]:.2f}")
    
    except (AttributeError, OSError):
        # os.getloadavg() not available on Windows
        pass
    
    # Environment variables (limited view)
    st.markdown("---")
    st.subheader("🌍 Variáveis de Ambiente (Selecionadas)")
    
    important_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'PWD', 'PYTHONPATH']
    env_data = []
    
    for var in important_vars:
        value = os.getenv(var, 'Não definida')
        # Truncate long values
        display_value = (value[:50] + '...') if len(value) > 50 else value
        env_data.append({'Variável': var, 'Valor': display_value})
    
    import pandas as pd
    env_df = pd.DataFrame(env_data)
    st.dataframe(env_df, use_container_width=True)
    
    # Auto-refresh option
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Opções")
    
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        st.sidebar.markdown("🔄 **Auto-refresh ativo**")
        import time
        time.sleep(30)
        st.rerun()
    
    # Export system info
    if st.sidebar.button("💾 Exportar Info Sistema"):
        system_info = get_detailed_system_info()
        
        # Create comprehensive system report
        report = f"""
# Relatório do Sistema - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Informações Básicas
- Hostname: {socket.gethostname()}
- Sistema: {platform.system()} {platform.release()}
- Arquitetura: {platform.machine()}
- Uptime: {uptime.days} dias

## CPU
- Cores Físicos: {system_info['cpu']['physical_cores']}
- Cores Lógicos: {system_info['cpu']['logical_cores']}
- Frequência: {system_info['cpu']['current_frequency']:.2f} MHz

## Memória
- Total: {memory.total / (1024**3):.2f} GB
- Usado: {memory.percent}%

## Disco
- Partições: {len(partitions)}

## Rede
- Interfaces: {len(network_info['interfaces'])}
- Bytes Enviados: {net_stats.bytes_sent / (1024**2):.1f} MB
- Bytes Recebidos: {net_stats.bytes_recv / (1024**2):.1f} MB
"""
        
        st.sidebar.download_button(
            label="📥 Baixar Relatório",
            data=report,
            file_name=f"system_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )