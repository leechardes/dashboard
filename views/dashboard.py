import streamlit as st
import psutil
import platform
import datetime
from components.metrics import create_metric_card, create_system_metrics
from components.charts import create_cpu_chart, create_memory_chart, create_disk_chart

def run():
    """Main dashboard view"""
    
    st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">analytics</span>Sistema Dashboard</div>', unsafe_allow_html=True)
    
    # Auto-refresh every 30 seconds
    # Material icon refresh button
    st.sidebar.markdown("""
    <style>
    .refresh-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--primary-color);
        color: var(--background-color);
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: none;
        cursor: pointer;
        width: 100%;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button(":material/refresh: Atualizar Dados"):
        st.rerun()
    
    # System overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_percent = psutil.cpu_percent(interval=1)
        create_metric_card("Uso de CPU", f"{cpu_percent}%", "desktop_windows")
    
    with col2:
        memory = psutil.virtual_memory()
        create_metric_card("Memória", f"{memory.percent}%", "memory")
    
    with col3:
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        create_metric_card("Disco", f"{disk_percent:.1f}%", "storage")
    
    with col4:
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        create_metric_card("Uptime", f"{uptime.days}d", "schedule")
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>show_chart</span>Uso de CPU", unsafe_allow_html=True)
        create_cpu_chart()
    
    with col2:
        st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>analytics</span>Uso de Memória", unsafe_allow_html=True)
        create_memory_chart()
    
    # Disk usage chart
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>storage</span>Uso de Disco", unsafe_allow_html=True)
    create_disk_chart()
    
    # System information
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>info</span>Informações do Sistema", unsafe_allow_html=True)
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.info(f"""
        **Sistema Operacional:** {platform.system()} {platform.release()}
        **Arquitetura:** {platform.machine()}
        **Processador:** {platform.processor()}
        **Python:** {platform.python_version()}
        """)
    
    with info_col2:
        st.info(f"""
        **CPU Cores:** {psutil.cpu_count()} físicos, {psutil.cpu_count(logical=True)} lógicos
        **Memória Total:** {psutil.virtual_memory().total // (1024**3)} GB
        **Disco Total:** {disk.total // (1024**3)} GB
        **Boot Time:** {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
        """)
    
    # Process information
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>refresh</span>Processos Ativos", unsafe_allow_html=True)
    
    show_processes = st.checkbox("Mostrar top 10 processos por CPU")
    if show_processes:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Create dataframe for display
        import pandas as pd
        df = pd.DataFrame(processes[:10])
        
        if not df.empty:
            st.dataframe(
                df,
                column_config={
                    "pid": "PID",
                    "name": "Nome do Processo",
                    "cpu_percent": st.column_config.ProgressColumn(
                        "CPU %",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%"
                    ),
                    "memory_percent": st.column_config.ProgressColumn(
                        "Memória %",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%"
                    )
                },
                width='stretch'
            )
    
    # Auto-refresh timer
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div style='display: flex; align-items: center; gap: 0.5rem;'><span class='material-icons'>schedule</span><strong>Auto-refresh:</strong> 30s</div>", unsafe_allow_html=True)
    
    # Add auto-refresh functionality
    import time
    time.sleep(30)
    if st.sidebar.checkbox("Auto-refresh ativo", value=True):
        st.rerun()