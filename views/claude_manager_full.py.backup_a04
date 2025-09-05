"""
Claude Manager Dashboard - Interface Principal
Dashboard completo de gestão de processos Claude.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os

# Adicionar diretório pai ao path para importar componentes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.claude_monitor import claude_monitor
from components.claude_actions import claude_actions
from components.claude_config import claude_config
from components.system_users import get_system_users, get_user_info

# Inicializar session state
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 5
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Funções auxiliares
def format_runtime(minutes):
    """Formatar tempo de execução"""
    if minutes < 60:
        return f"{minutes}m"
    elif minutes < 1440:  # menos que 24h
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"
    else:
        days = minutes // 1440
        hours = (minutes % 1440) // 60
        return f"{days}d {hours}h"

def get_status_emoji(process):
    """Retorna emoji baseado no status do processo"""
    if process['is_old']:
        return "🔴"
    elif process['is_orphan']:
        return "⚠️"
    elif process['memory_mb'] > 1024:
        return "🟡"
    else:
        return "🟢"

def show_confirmation_dialog(title, message, key):
    """Mostra diálogo de confirmação"""
    if f"show_confirm_{key}" not in st.session_state:
        st.session_state[f"show_confirm_{key}"] = False
    
    if st.session_state[f"show_confirm_{key}"]:
        st.error(f"⚠️ **{title}**")
        st.write(message)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Confirmar", key=f"confirm_{key}"):
                st.session_state[f"show_confirm_{key}"] = False
                st.session_state[f"confirmed_{key}"] = True
                st.rerun()
        with col2:
            if st.button("❌ Cancelar", key=f"cancel_{key}"):
                st.session_state[f"show_confirm_{key}"] = False
                st.rerun()
        return False
    
    return st.session_state.get(f"confirmed_{key}", False)

# Header principal
st.title("💻 Claude Process Manager")
st.markdown("Gerenciamento completo de processos Claude em execução no sistema")

# Sidebar para controles globais
with st.sidebar:
    st.header("⚙️ Controles")
    
    # Auto-refresh
    st.session_state.auto_refresh = st.checkbox("Auto Refresh", st.session_state.auto_refresh)
    if st.session_state.auto_refresh:
        st.session_state.refresh_interval = st.slider("Intervalo (s)", 1, 30, st.session_state.refresh_interval)
    
    # Botão refresh manual
    if st.button("🔄 Refresh Manual"):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    # Ações globais perigosas
    st.markdown("---")
    st.markdown("### 🚨 Ações Globais")
    
    if st.button("🧹 Limpar Órfãos"):
        success, message, killed_pids = claude_actions.clean_orphan_processes()
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        st.rerun()
    
    if st.button("⏰ Limpar Antigos (>2h)"):
        success, message, killed_pids = claude_actions.clean_old_processes(2)
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        st.rerun()

# Obter dados atualizados
processes = claude_monitor.get_claude_processes()
memory_stats = claude_monitor.get_memory_stats()
user_ranking = claude_monitor.get_user_ranking()
system_resources = claude_monitor.get_system_resources()

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Processos",
        memory_stats.get('total_processes', 0),
        delta=None
    )

with col2:
    st.metric(
        "Memória Total",
        f"{memory_stats.get('total_memory_mb', 0):.1f} MB",
        delta=None
    )

with col3:
    st.metric(
        "Usuários Ativos",
        memory_stats.get('active_users', 0),
        delta=None
    )

with col4:
    st.metric(
        "CPU Sistema",
        f"{system_resources.get('cpu_percent', 0):.1f}%",
        delta=None
    )

# Tabs principais
tab1, tab2, tab3, tab4 = st.tabs(["📊 Monitor", "📈 Analytics", "⚙️ Config", "📋 Logs"])

# TAB 1: MONITOR
with tab1:
    st.header("📊 Monitor de Processos")
    
    if not processes:
        st.info("😴 Nenhum processo Claude encontrado no sistema")
    else:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            users = ["Todos"] + list(set(p['username'] for p in processes))
            selected_user = st.selectbox("👤 Filtrar por usuário:", users)
        
        with col2:
            status_filter = st.selectbox("🔍 Filtrar por status:", ["Todos", "Normais", "Antigos", "Órfãos"])
        
        with col3:
            sort_by = st.selectbox("📊 Ordenar por:", ["Memória (desc)", "CPU (desc)", "Tempo (desc)", "PID"])
        
        # Aplicar filtros
        filtered_processes = processes
        
        if selected_user != "Todos":
            filtered_processes = [p for p in filtered_processes if p['username'] == selected_user]
        
        if status_filter == "Antigos":
            filtered_processes = [p for p in filtered_processes if p['is_old']]
        elif status_filter == "Órfãos":
            filtered_processes = [p for p in filtered_processes if p['is_orphan']]
        elif status_filter == "Normais":
            filtered_processes = [p for p in filtered_processes if not p['is_old'] and not p['is_orphan']]
        
        # Ordenação
        if sort_by == "Memória (desc)":
            filtered_processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        elif sort_by == "CPU (desc)":
            filtered_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif sort_by == "Tempo (desc)":
            filtered_processes.sort(key=lambda x: x['runtime_minutes'], reverse=True)
        elif sort_by == "PID":
            filtered_processes.sort(key=lambda x: x['pid'])
        
        st.markdown(f"**{len(filtered_processes)} processos encontrados**")
        
        # Tabela de processos
        for i, proc in enumerate(filtered_processes):
            with st.container():
                col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 2, 2, 2, 2, 2])
                
                with col1:
                    status_emoji = get_status_emoji(proc)
                    st.markdown(f"**{status_emoji}**")
                
                with col2:
                    st.markdown(f"**PID:** {proc['pid']}")
                    st.caption(proc['name'])
                
                with col3:
                    st.markdown(f"**User:** {proc['username']}")
                    st.caption(f"Status: {proc['status']}")
                
                with col4:
                    st.markdown(f"**Mem:** {proc['memory_mb']:.1f} MB")
                    st.caption(f"CPU: {proc['cpu_percent']:.1f}%")
                
                with col5:
                    runtime_str = format_runtime(proc['runtime_minutes'])
                    st.markdown(f"**Tempo:** {runtime_str}")
                    st.caption(proc['create_time'].strftime("%H:%M"))
                
                with col6:
                    warnings = []
                    if proc['is_old']:
                        warnings.append("Antigo")
                    if proc['is_orphan']:
                        warnings.append("Órfão")
                    if proc['memory_mb'] > 1024:
                        warnings.append("Alta Mem")
                    
                    if warnings:
                        st.warning(" | ".join(warnings))
                    else:
                        st.success("Normal")
                
                with col7:
                    if st.button(f"🔴 Kill", key=f"kill_{proc['pid']}"):
                        success, message = claude_actions.kill_process(proc['pid'])
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                        time.sleep(1)
                        st.rerun()
                
                st.markdown("---")
        
        # Ações em lote para usuário selecionado
        if selected_user != "Todos" and filtered_processes:
            st.markdown("### 🎯 Ações para usuário selecionado")
            
            if st.button(f"🔴 Matar todos os processos de {selected_user}"):
                if show_confirmation_dialog(
                    "Confirmar ação destrutiva",
                    f"Tem certeza que deseja matar TODOS os {len(filtered_processes)} processos do usuário {selected_user}?",
                    f"kill_user_{selected_user}"
                ):
                    success, message, killed_pids = claude_actions.kill_user_processes(selected_user)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                    st.session_state[f"confirmed_kill_user_{selected_user}"] = False
                    st.rerun()

# TAB 2: ANALYTICS
with tab2:
    st.header("📈 Analytics & Estatísticas")
    
    if not processes:
        st.info("😴 Sem dados para análise - nenhum processo encontrado")
    else:
        # Gráficos em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Distribuição de Memória por Usuário")
            
            if user_ranking:
                # Gráfico de pizza
                user_memory = {user['username']: user['total_memory_mb'] for user in user_ranking}
                
                fig_pie = px.pie(
                    values=list(user_memory.values()),
                    names=list(user_memory.keys()),
                    title="Uso de Memória por Usuário (MB)"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.subheader("⏱️ Processos por Tempo de Execução")
            
            # Histograma de tempo de execução
            runtimes = [proc['runtime_minutes'] for proc in processes]
            fig_hist = px.histogram(
                x=runtimes,
                nbins=20,
                title="Distribuição de Tempo de Execução (minutos)",
                labels={'x': 'Minutos', 'y': 'Quantidade'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            st.subheader("📊 Ranking de Usuários")
            
            # Tabela de ranking
            if user_ranking:
                ranking_df = pd.DataFrame(user_ranking)
                ranking_df = ranking_df.rename(columns={
                    'username': 'Usuário',
                    'process_count': 'Processos',
                    'total_memory_mb': 'Mem Total (MB)',
                    'avg_memory_mb': 'Mem Média (MB)',
                    'max_memory_mb': 'Mem Máx (MB)',
                    'oldest_runtime_minutes': 'Tempo Máx (min)'
                })
                
                st.dataframe(
                    ranking_df,
                    use_container_width=True,
                    hide_index=True
                )
            
            st.subheader("🎯 Estatísticas Gerais")
            
            # Cards de estatísticas
            stats_col1, stats_col2 = st.columns(2)
            
            with stats_col1:
                st.metric("Processo com mais memória", f"{memory_stats.get('max_memory_mb', 0):.1f} MB")
                st.metric("Memória média por processo", f"{memory_stats.get('avg_memory_mb', 0):.1f} MB")
            
            with stats_col2:
                old_processes = len([p for p in processes if p['is_old']])
                orphan_processes = len([p for p in processes if p['is_orphan']])
                st.metric("Processos antigos (>2h)", old_processes)
                st.metric("Processos órfãos", orphan_processes)
        
        # Gráfico de linha temporal (simulado)
        st.subheader("📈 Uso de Recursos ao Longo do Tempo")
        
        # Para demonstração, criar dados simulados
        import numpy as np
        
        time_points = pd.date_range(start=datetime.now() - timedelta(hours=2), end=datetime.now(), freq='10min')
        memory_usage = np.random.normal(memory_stats.get('total_memory_mb', 500), 100, len(time_points))
        memory_usage = np.maximum(memory_usage, 0)  # Não permitir valores negativos
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=time_points,
            y=memory_usage,
            mode='lines+markers',
            name='Uso de Memória (MB)',
            line=dict(color='blue', width=2)
        ))
        
        fig_line.update_layout(
            title="Histórico de Uso de Memória (últimas 2h)",
            xaxis_title="Tempo",
            yaxis_title="Memória (MB)",
            showlegend=True
        )
        
        st.plotly_chart(fig_line, use_container_width=True)

# TAB 3: CONFIG
with tab3:
    st.header("⚙️ Configurações")
    
    # Subtabs para diferentes tipos de configuração
    config_tab1, config_tab2, config_tab3 = st.tabs(["👤 Usuários", "🌍 Global", "🔒 Segurança"])
    
    with config_tab1:
        st.subheader("👤 Configurações por Usuário")
        
        # Seção para adicionar/editar limites de usuário
        st.markdown("#### 🔄 Gerenciamento de Usuários")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("🔄 Carregar Usuários do Sistema", use_container_width=True):
                st.session_state['load_system_users'] = True
                st.rerun()
                
        with col_btn2:
            if st.button("📋 Aplicar Default para Todos", use_container_width=True):
                # Pegar configuração default
                default_config = claude_config.get_user_limit("default")
                system_users = get_system_users()
                
                # Aplicar para todos os usuários do grupo developers
                applied_count = 0
                for user in system_users:
                    if user['is_developer'] or user['has_claude_processes']:
                        success = claude_config.set_user_limit(
                            user['username'],
                            default_config.get('memory_limit_mb', 8192),
                            default_config.get('max_processes', 5),
                            default_config.get('max_runtime_hours', 24),
                            default_config.get('priority', 'normal')
                        )
                        if success:
                            applied_count += 1
                
                st.success(f"✅ Configuração default aplicada para {applied_count} usuários")
                st.rerun()
                
        with col_btn3:
            if st.button("🗑️ Limpar Configurações", use_container_width=True):
                if st.checkbox("Confirmo que quero limpar todas as configurações"):
                    # Resetar para apenas default
                    claude_config.reset_to_defaults()
                    st.success("✅ Configurações resetadas")
                    st.rerun()
        
        st.markdown("---")
        
        # Seção de adicionar/editar usuário
        st.markdown("#### ➕ Adicionar/Editar Configuração de Usuário")
        
        # Pegar valores default da configuração
        default_config = claude_config.get_user_limit("default")
        default_memory = default_config.get('memory_limit_mb', 8192)
        default_processes = default_config.get('max_processes', 5)
        default_runtime = default_config.get('max_runtime_hours', 24)
        
        # Se foi solicitado carregar usuários do sistema
        if st.session_state.get('load_system_users', False):
            system_users = get_system_users()
            user_options = ['Selecione...'] + [
                f"{u['username']} ({u['full_name'] or 'No name'})" 
                for u in system_users 
                if u['is_developer'] or u['has_claude_processes']
            ]
        else:
            user_options = ['Digite manualmente...']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if len(user_options) > 1:
                selected_user = st.selectbox("Selecione o usuário:", user_options)
                if selected_user != 'Selecione...':
                    username_input = selected_user.split(' (')[0]
                else:
                    username_input = st.text_input("Ou digite o nome:")
            else:
                username_input = st.text_input("Nome do usuário:")
        
        with col2:
            memory_limit = st.number_input(
                "Limite de Memória (MB):", 
                min_value=512, 
                max_value=16384, 
                value=default_memory,
                step=1024
            )
        
        with col3:
            max_processes = st.number_input(
                "Máx Processos:", 
                min_value=1, 
                max_value=20, 
                value=default_processes
            )
        
        with col4:
            max_runtime_hours = st.number_input(
                "Máx Tempo (h):", 
                min_value=1, 
                max_value=168,  # 1 semana
                value=default_runtime
            )
        
        if st.button("💾 Salvar Configuração", type="primary", use_container_width=True):
            if username_input and username_input not in ['Selecione...', 'Digite manualmente...']:
                success = claude_config.set_user_limit(
                    username_input, 
                    memory_limit, 
                    max_processes, 
                    max_runtime_hours
                )
                if success:
                    st.success(f"✅ Configuração salva para {username_input}")
                else:
                    st.error("❌ Erro ao salvar configuração")
                st.rerun()
            else:
                st.warning("⚠️ Selecione ou digite um nome de usuário")
        
        st.markdown("---")
        st.markdown("#### 👥 Usuários Configurados")
        
        # Mostrar configurações atuais
        user_limits = claude_config.get_all_user_limits()
        
        # Criar tabs para melhor organização
        if len(user_limits) > 5:
            # Se muitos usuários, usar tabs
            tab_names = list(user_limits.keys())
            tabs = st.tabs(tab_names)
            
            for i, (username, config) in enumerate(user_limits.items()):
                with tabs[i]:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Memória", f"{config.get('memory_limit_mb', 'N/A')} MB")
                    
                    with col2:
                        st.metric("Max Processos", config.get('max_processes', 'N/A'))
                    
                    with col3:
                        st.metric("Max Tempo", f"{config.get('max_runtime_hours', 'N/A')}h")
                    
                    with col4:
                        st.metric("Prioridade", config.get('priority', 'normal'))
                    
                    # Botões de ação
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        if username != 'default':
                            if st.button(f"🔄 Resetar para Default", key=f"reset_{username}"):
                                # Aplicar configuração default
                                success = claude_config.set_user_limit(
                                    username,
                                    default_config.get('memory_limit_mb', 8192),
                                    default_config.get('max_processes', 5),
                                    default_config.get('max_runtime_hours', 24)
                                )
                                if success:
                                    st.success(f"✅ {username} resetado para default")
                                    st.rerun()
                    
                    with col_act2:
                        if username != 'default':
                            if st.button(f"🗑️ Remover", key=f"remove_{username}"):
                                if claude_config.remove_user_limit(username):
                                    st.success(f"✅ Configuração de {username} removida")
                                    st.rerun()
        else:
            # Se poucos usuários, usar expanders
            for username, config in user_limits.items():
                icon = "⚙️" if username == "default" else "👤"
                with st.expander(f"{icon} {username}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**Memória:** {config.get('memory_limit_mb', 'N/A')} MB")
                        if username != 'default':
                            new_mem = st.number_input(
                                "Nova memória:", 
                                value=config.get('memory_limit_mb', 8192),
                                key=f"mem_{username}",
                                min_value=512,
                                max_value=16384,
                                step=1024
                            )
                    
                    with col2:
                        st.write(f"**Max Processos:** {config.get('max_processes', 'N/A')}")
                        if username != 'default':
                            new_proc = st.number_input(
                                "Novos processos:", 
                                value=config.get('max_processes', 5),
                                key=f"proc_{username}",
                                min_value=1,
                                max_value=20
                            )
                    
                    with col3:
                        st.write(f"**Max Tempo:** {config.get('max_runtime_hours', 'N/A')}h")
                        if username != 'default':
                            new_time = st.number_input(
                                "Novo tempo:", 
                                value=config.get('max_runtime_hours', 24),
                                key=f"time_{username}",
                                min_value=1,
                                max_value=168
                            )
                    
                    with col4:
                        st.write(f"**Prioridade:** {config.get('priority', 'normal')}")
                        if username != 'default':
                            if st.button(f"💾 Atualizar", key=f"update_{username}"):
                                success = claude_config.set_user_limit(
                                    username,
                                    new_mem,
                                    new_proc,
                                    new_time
                                )
                                if success:
                                    st.success(f"✅ {username} atualizado")
                                    st.rerun()
                
                with col3:
                    if username != "default":
                        if st.button(f"🗑️ Remover", key=f"remove_{username}"):
                            success = claude_config.remove_user_limit(username)
                            if success:
                                st.success(f"✅ Configuração removida para {username}")
                            else:
                                st.error("❌ Erro ao remover configuração")
                            st.rerun()
    
    with config_tab2:
        st.subheader("🌍 Configurações Globais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Limpeza Automática")
            
            auto_cleanup = st.checkbox(
                "Habilitar limpeza automática",
                value=claude_config.get_global_setting("auto_cleanup_enabled")
            )
            
            cleanup_interval = st.slider(
                "Intervalo de limpeza (minutos):",
                min_value=5, max_value=120,
                value=claude_config.get_global_setting("auto_cleanup_interval_minutes") or 30
            )
            
            max_age_hours = st.slider(
                "Idade máxima do processo (horas):",
                min_value=1, max_value=24,
                value=claude_config.get_global_setting("max_process_age_hours") or 2
            )
            
            orphan_cleanup = st.checkbox(
                "Limpeza de órfãos habilitada",
                value=claude_config.get_global_setting("orphan_cleanup_enabled")
            )
        
        with col2:
            st.markdown("#### Alertas e Limites")
            
            alert_memory_threshold = st.number_input(
                "Limite de alerta - Memória (MB):",
                min_value=512, max_value=16384,
                value=claude_config.get_global_setting("alert_memory_threshold_mb") or 2048
            )
            
            alert_cpu_threshold = st.slider(
                "Limite de alerta - CPU (%):",
                min_value=50, max_value=100,
                value=claude_config.get_global_setting("alert_cpu_threshold_percent") or 80
            )
            
            max_processes_per_user = st.number_input(
                "Máx processos por usuário:",
                min_value=1, max_value=100,
                value=claude_config.get_global_setting("max_processes_per_user") or 10
            )
            
            log_retention_days = st.number_input(
                "Retenção de logs (dias):",
                min_value=1, max_value=30,
                value=claude_config.get_global_setting("log_retention_days") or 7
            )
        
        if st.button("💾 Salvar Configurações Globais"):
            success = True
            success &= claude_config.set_global_setting("auto_cleanup_enabled", auto_cleanup)
            success &= claude_config.set_global_setting("auto_cleanup_interval_minutes", cleanup_interval)
            success &= claude_config.set_global_setting("max_process_age_hours", max_age_hours)
            success &= claude_config.set_global_setting("orphan_cleanup_enabled", orphan_cleanup)
            success &= claude_config.set_global_setting("alert_memory_threshold_mb", alert_memory_threshold)
            success &= claude_config.set_global_setting("alert_cpu_threshold_percent", alert_cpu_threshold)
            success &= claude_config.set_global_setting("max_processes_per_user", max_processes_per_user)
            success &= claude_config.set_global_setting("log_retention_days", log_retention_days)
            
            if success:
                st.success("✅ Configurações globais salvas")
            else:
                st.error("❌ Erro ao salvar algumas configurações")
    
    with config_tab3:
        st.subheader("🔒 Configurações de Segurança")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Confirmações")
            
            require_kill_all_confirm = st.checkbox(
                "Confirmar antes de matar todos os processos",
                value=claude_config.get_security_config().get("require_confirmation_for_kill_all", True)
            )
            
            require_user_kill_confirm = st.checkbox(
                "Confirmar antes de matar processos do usuário",
                value=claude_config.get_security_config().get("require_confirmation_for_user_kill", True)
            )
            
            enable_action_logging = st.checkbox(
                "Habilitar log de ações",
                value=claude_config.get_security_config().get("enable_action_logging", True)
            )
        
        with col2:
            st.markdown("#### Exportar/Importar Config")
            
            if st.button("📤 Exportar Configuração"):
                config_json = claude_config.export_config()
                st.download_button(
                    label="💾 Baixar arquivo de configuração",
                    data=config_json,
                    file_name=f"claude_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            uploaded_file = st.file_uploader("📥 Importar Configuração", type=['json'])
            if uploaded_file is not None:
                config_content = uploaded_file.read().decode('utf-8')
                if st.button("⚡ Aplicar Configuração Importada"):
                    success = claude_config.import_config(config_content)
                    if success:
                        st.success("✅ Configuração importada com sucesso")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao importar configuração")
            
            if st.button("🔄 Resetar para Padrão"):
                if show_confirmation_dialog(
                    "Resetar Configuração",
                    "Tem certeza que deseja resetar TODAS as configurações para os valores padrão? Esta ação não pode ser desfeita.",
                    "reset_config"
                ):
                    success = claude_config.reset_to_default()
                    if success:
                        st.success("✅ Configuração resetada para padrão")
                    else:
                        st.error("❌ Erro ao resetar configuração")
                    st.session_state["confirmed_reset_config"] = False
                    st.rerun()

# TAB 4: LOGS
with tab4:
    st.header("📋 Logs de Ações")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("#### Controles")
        
        log_lines = st.number_input("Linhas para exibir:", min_value=10, max_value=1000, value=100)
        
        if st.button("🔄 Atualizar Logs"):
            st.rerun()
        
        if st.button("🧹 Limpar Logs Antigos"):
            success, message = claude_actions.clear_old_logs(7)
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
            st.rerun()
    
    with col1:
        st.markdown("#### Histórico de Ações")
        
        # Obter logs
        logs = claude_actions.get_action_logs(log_lines)
        
        if not logs:
            st.info("📝 Nenhum log encontrado")
        else:
            # Filtros de log
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                log_level_filter = st.selectbox("Nível:", ["Todos", "SUCCESS", "ERROR", "INFO"])
            
            with filter_col2:
                action_filter = st.selectbox("Ação:", ["Todas", "KILL_PROCESS", "KILL_USER_PROCESSES", "KILL_ALL_PROCESSES"])
            
            with filter_col3:
                user_filter = st.text_input("Filtrar por usuário:")
            
            # Aplicar filtros
            filtered_logs = logs
            
            if log_level_filter != "Todos":
                filtered_logs = [log for log in filtered_logs if log_level_filter in log]
            
            if action_filter != "Todas":
                filtered_logs = [log for log in filtered_logs if action_filter in log]
            
            if user_filter:
                filtered_logs = [log for log in filtered_logs if user_filter.lower() in log.lower()]
            
            st.markdown(f"**{len(filtered_logs)} linhas de log (de {len(logs)} total)**")
            
            # Exibir logs em container scrollável
            log_container = st.container()
            
            with log_container:
                for log_line in reversed(filtered_logs[-50:]):  # Mostrar últimas 50 linhas filtradas
                    if "ERROR" in log_line or "FALHOU" in log_line:
                        st.error(f"🔴 {log_line}")
                    elif "SUCCESS" in log_line:
                        st.success(f"✅ {log_line}")
                    else:
                        st.info(f"ℹ️ {log_line}")

# Auto-refresh logic
if st.session_state.auto_refresh:
    current_time = datetime.now()
    time_diff = (current_time - st.session_state.last_refresh).seconds
    
    if time_diff >= st.session_state.refresh_interval:
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Mostrar contador regressivo
    remaining = st.session_state.refresh_interval - time_diff
    st.sidebar.info(f"⏱️ Próximo refresh em {remaining}s")
    
    # JavaScript para auto-refresh
    st.markdown(f"""
        <script>
            setTimeout(function(){{
                window.location.reload();
            }}, {remaining * 1000});
        </script>
    """, unsafe_allow_html=True)

# Rodapé
st.markdown("---")
st.markdown("**Claude Manager Dashboard** - Desenvolvido para gerenciamento eficiente de processos Claude")
st.caption(f"Última atualização: {st.session_state.last_refresh.strftime('%H:%M:%S')}")