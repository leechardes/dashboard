import streamlit as st
import psutil
import platform
import datetime
from components.metrics import create_metric_card, create_system_metrics
from components.charts import create_cpu_chart, create_memory_chart, create_disk_chart

def run():
    """Main dashboard view"""
    
    st.markdown('<div class="main-header">📊 Sistema Dashboard</div>', unsafe_allow_html=True)
    
    # Auto-refresh every 30 seconds
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.rerun()
    
    # System overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_percent = psutil.cpu_percent(interval=1)
        create_metric_card("CPU Usage", f"{cpu_percent}%", "🖥️")
    
    with col2:
        memory = psutil.virtual_memory()
        create_metric_card("Memória", f"{memory.percent}%", "💾")
    
    with col3:
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        create_metric_card("Disco", f"{disk_percent:.1f}%", "💽")
    
    with col4:
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        create_metric_card("Uptime", f"{uptime.days}d", "⏱️")
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Uso de CPU")
        create_cpu_chart()
    
    with col2:
        st.subheader("📊 Uso de Memória")
        create_memory_chart()
    
    # Disk usage chart
    st.subheader("💽 Uso de Disco")
    create_disk_chart()
    
    # System information
    st.markdown("---")
    st.subheader("ℹ️ Informações do Sistema")
    
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
    st.subheader("🔄 Processos Ativos")
    
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
                use_container_width=True
            )
    
    # Auto-refresh timer
    st.sidebar.markdown("---")
    st.sidebar.markdown("⏰ **Auto-refresh:** 30s")
    
    # Add auto-refresh functionality
    import time
    time.sleep(30)
    if st.sidebar.checkbox("Auto-refresh ativo", value=True):
        st.rerun()