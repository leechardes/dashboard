import streamlit as st
import os
import glob
import datetime
from utils.file_scanner import scan_log_files
from components.markdown_viewer import render_log_content
from components.metrics import create_metric_card

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_log_files():
    """Get all log files from common log directories"""
    return scan_log_files()

def run():
    """Log viewer and analyzer"""
    
    st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">description</span>Visualizador de Logs</div>', unsafe_allow_html=True)
    
    # Get log files
    with st.spinner("Escaneando arquivos de log..."):
        logs = get_log_files()
    
    if not logs:
        st.warning("Nenhum arquivo de log encontrado.")
        st.info("Procurando em: /var/log, /srv/projects/*/logs, ~/.local/share/")
        return
    
    # Sidebar controls
    st.sidebar.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>filter_alt</span>Filtros de Log", unsafe_allow_html=True)
    
    # Search in log content
    search_term = st.sidebar.text_input("Buscar nos logs", placeholder="Digite para buscar...")
    
    # Filter by log level
    log_levels = ["Todos", "ERROR", "WARN", "INFO", "DEBUG"]
    selected_level = st.sidebar.selectbox("Nível de Log", log_levels, index=0)
    
    # Filter by time range
    time_filter = st.sidebar.selectbox(
        "Período",
        ["Todas", "Última hora", "Últimas 24h", "Última semana", "Último mês"],
        index=0
    )
    
    # Filter by log type/source
    log_sources = sorted(set(log['source'] for log in logs))
    selected_source = st.sidebar.selectbox(
        "Fonte do Log",
        ["Todas"] + log_sources,
        index=0
    )
    
    # Apply filters
    filtered_logs = logs
    
    # Filter by source
    if selected_source != "Todas":
        filtered_logs = [log for log in filtered_logs if log['source'] == selected_source]
    
    # Filter by time
    if time_filter != "Todas":
        now = datetime.datetime.now()
        if time_filter == "Última hora":
            cutoff = now - datetime.timedelta(hours=1)
        elif time_filter == "Últimas 24h":
            cutoff = now - datetime.timedelta(days=1)
        elif time_filter == "Última semana":
            cutoff = now - datetime.timedelta(weeks=1)
        elif time_filter == "Último mês":
            cutoff = now - datetime.timedelta(days=30)
        
        filtered_logs = [
            log for log in filtered_logs 
            if datetime.datetime.fromtimestamp(log['modified_timestamp']) > cutoff
        ]
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card("Total Logs", len(logs), "description")
    
    with col2:
        create_metric_card("Filtrados", len(filtered_logs), "filter_list")
    
    with col3:
        total_size = sum(log['size'] for log in filtered_logs) / (1024*1024)  # MB
        create_metric_card("Tamanho Total", f"{total_size:.1f} MB", "storage")
    
    with col4:
        if st.button(":material/refresh: Atualizar"):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Main layout
    if not filtered_logs:
        st.warning("Nenhum log encontrado com os filtros aplicados.")
        return
    
    # Log file selector
    log_options = [f"{log['name']} ({log['source']})" for log in filtered_logs]
    selected_log_idx = st.selectbox(
        "Selecionar arquivo de log",
        range(len(filtered_logs)),
        format_func=lambda x: log_options[x],
        index=0
    )
    
    selected_log = filtered_logs[selected_log_idx]
    
    # Log file info
    st.info(f"""
    **Arquivo:** {selected_log['name']}
    **Caminho:** {selected_log['path']}
    **Tamanho:** {selected_log['size'] / 1024:.1f} KB
    **Modificado:** {selected_log['modified']}
    **Fonte:** {selected_log['source']}
    """)
    
    # Display options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_lines = st.slider("Linhas a mostrar", 10, 1000, 100)
    
    with col2:
        tail_mode = st.checkbox("Mostrar últimas linhas", value=True)
    
    with col3:
        follow_mode = st.checkbox("Seguir arquivo (live)", value=False)
    
    # Log content display
    st.markdown("---")
    st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>article</span>Conteúdo do Log", unsafe_allow_html=True)
    
    try:
        log_path = selected_log['path']
        
        if not os.path.exists(log_path):
            st.error("Arquivo de log não encontrado.")
            return
        
        # Read log file
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            if tail_mode:
                # Read last N lines
                lines = f.readlines()
                display_lines = lines[-show_lines:] if len(lines) > show_lines else lines
            else:
                # Read first N lines
                display_lines = []
                for i, line in enumerate(f):
                    if i >= show_lines:
                        break
                    display_lines.append(line)
        
        # Apply search filter
        if search_term:
            display_lines = [line for line in display_lines if search_term.lower() in line.lower()]
        
        # Apply log level filter
        if selected_level != "Todos":
            display_lines = [line for line in display_lines if selected_level in line.upper()]
        
        # Display log content with syntax highlighting
        if display_lines:
            # Create color-coded log display
            log_content = ""
            for line in display_lines:
                line = line.strip()
                if "ERROR" in line.upper():
                    log_content += f"[ERROR] {line}\n"
                elif "WARN" in line.upper():
                    log_content += f"[WARN] {line}\n"
                elif "INFO" in line.upper():
                    log_content += f"[INFO] {line}\n"
                elif "DEBUG" in line.upper():
                    log_content += f"[DEBUG] {line}\n"
                else:
                    log_content += f"{line}\n"
            
            st.code(log_content, language='log')
            
            # Show statistics
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                error_count = sum(1 for line in display_lines if "ERROR" in line.upper())
                create_metric_card("Erros", error_count, "error")
            
            with col2:
                warn_count = sum(1 for line in display_lines if "WARN" in line.upper())
                create_metric_card("Avisos", warn_count, "warning")
            
            with col3:
                info_count = sum(1 for line in display_lines if "INFO" in line.upper())
                create_metric_card("Info", info_count, "info")
            
            with col4:
                create_metric_card("Linhas", len(display_lines), "format_list_numbered")
            
        else:
            st.info("Nenhuma linha encontrada com os filtros aplicados.")
    
    except Exception as e:
        st.error(f"Erro ao ler arquivo de log: {str(e)}")
    
    # Download option
    if st.sidebar.button(":material/download: Baixar Log"):
        try:
            with open(selected_log['path'], 'rb') as f:
                st.sidebar.download_button(
                    label=":material/file_download: Download Arquivo",
                    data=f.read(),
                    file_name=selected_log['name'],
                    mime="text/plain"
                )
        except Exception as e:
            st.sidebar.error(f"Erro no download: {str(e)}")
    
    # Auto-refresh for follow mode
    if follow_mode:
        st.sidebar.markdown("**Modo Live Ativo**")
        import time
        time.sleep(5)
        st.rerun()