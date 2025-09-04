import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import psutil
import pandas as pd
import datetime
import time

@st.cache_data(ttl=30)
def get_system_metrics():
    """Get current system metrics"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
        'timestamp': datetime.datetime.now()
    }

def create_cpu_chart():
    """Create CPU usage chart"""
    # Get CPU usage per core
    cpu_percents = psutil.cpu_percent(percpu=True, interval=1)
    
    # Create bar chart
    fig = go.Figure(data=go.Bar(
        x=[f"Core {i+1}" for i in range(len(cpu_percents))],
        y=cpu_percents,
        marker_color=['#FF6B6B' if cpu > 80 else '#4ECDC4' if cpu > 50 else '#45B7D1' for cpu in cpu_percents],
        text=[f"{cpu:.1f}%" for cpu in cpu_percents],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Uso de CPU por Core",
        xaxis_title="Cores do Processador",
        yaxis_title="Uso (%)",
        yaxis=dict(range=[0, 100]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_memory_chart():
    """Create memory usage pie chart"""
    memory = psutil.virtual_memory()
    
    # Memory breakdown
    labels = ['Usado', 'Buffers', 'Cache', 'Livre']
    values = [
        memory.used - memory.buffers - memory.cached,
        memory.buffers,
        memory.cached,
        memory.free
    ]
    
    # Convert to GB
    values_gb = [v / (1024**3) for v in values]
    
    fig = go.Figure(data=go.Pie(
        labels=labels,
        values=values_gb,
        hole=0.4,
        marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'],
        textinfo='label+percent',
        textfont_size=12
    ))
    
    fig.update_layout(
        title=f"Distribuição de Memória ({memory.total / (1024**3):.1f} GB Total)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_disk_chart():
    """Create disk usage chart for all partitions"""
    partitions = psutil.disk_partitions()
    disk_data = []
    
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_data.append({
                'Partição': partition.mountpoint,
                'Total (GB)': usage.total / (1024**3),
                'Usado (GB)': usage.used / (1024**3),
                'Livre (GB)': usage.free / (1024**3),
                'Uso (%)': (usage.used / usage.total) * 100
            })
        except PermissionError:
            continue
    
    if not disk_data:
        st.warning("Nenhuma informação de disco disponível")
        return
    
    df = pd.DataFrame(disk_data)
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Usado',
        x=df['Partição'],
        y=df['Usado (GB)'],
        marker_color='#FF6B6B'
    ))
    
    fig.add_trace(go.Bar(
        name='Livre',
        x=df['Partição'],
        y=df['Livre (GB)'],
        marker_color='#4ECDC4'
    ))
    
    fig.update_layout(
        title="Uso de Disco por Partição",
        xaxis_title="Partições",
        yaxis_title="Espaço (GB)",
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_network_chart():
    """Create network I/O chart"""
    net_stats = psutil.net_io_counters()
    
    # Create simple metrics display since we don't have historical data
    data = {
        'Métrica': ['Bytes Enviados', 'Bytes Recebidos', 'Pacotes Enviados', 'Pacotes Recebidos'],
        'Valor': [
            net_stats.bytes_sent / (1024**2),  # MB
            net_stats.bytes_recv / (1024**2),  # MB
            net_stats.packets_sent,
            net_stats.packets_recv
        ],
        'Unidade': ['MB', 'MB', 'pacotes', 'pacotes']
    }
    
    df = pd.DataFrame(data)
    
    # Create bar chart
    fig = go.Figure(data=go.Bar(
        x=df['Métrica'],
        y=df['Valor'],
        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'],
        text=[f"{val:.1f} {unit}" for val, unit in zip(df['Valor'], df['Unidade'])],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Estatísticas de Rede",
        xaxis_title="Métricas",
        yaxis_title="Valor",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_process_chart():
    """Create top processes chart by CPU usage"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Sort by CPU usage and get top 10
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    top_processes = processes[:10]
    
    if not top_processes:
        st.warning("Nenhum processo encontrado")
        return
    
    df = pd.DataFrame(top_processes)
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='CPU %',
        x=df['cpu_percent'],
        y=df['name'],
        orientation='h',
        marker_color='#FF6B6B'
    ))
    
    fig.update_layout(
        title="Top 10 Processos por Uso de CPU",
        xaxis_title="CPU Usage (%)",
        yaxis_title="Processo",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_system_overview_chart():
    """Create system overview chart with multiple metrics"""
    metrics = get_system_metrics()
    
    # Create gauge-style chart for system overview
    fig = go.Figure()
    
    # CPU Gauge
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = metrics['cpu_percent'],
        domain = {'x': [0, 0.33], 'y': [0, 1]},
        title = {'text': "CPU"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#FF6B6B"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    # Memory Gauge
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = metrics['memory_percent'],
        domain = {'x': [0.33, 0.66], 'y': [0, 1]},
        title = {'text': "Memória"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#4ECDC4"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    # Disk Gauge
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = metrics['disk_percent'],
        domain = {'x': [0.66, 1], 'y': [0, 1]},
        title = {'text': "Disco"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#45B7D1"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    fig.update_layout(
        title="Visão Geral do Sistema",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_time_series_chart(data, title="Sistema ao Longo do Tempo", height=400):
    """Create a time series chart for system metrics"""
    if not data:
        st.info("Nenhum dado histórico disponível")
        return
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    # Add traces for each metric
    if 'cpu_percent' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cpu_percent'],
            mode='lines+markers',
            name='CPU %',
            line_color='#FF6B6B'
        ))
    
    if 'memory_percent' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['memory_percent'],
            mode='lines+markers',
            name='Memória %',
            line_color='#4ECDC4'
        ))
    
    if 'disk_percent' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['disk_percent'],
            mode='lines+markers',
            name='Disco %',
            line_color='#45B7D1'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Tempo",
        yaxis_title="Uso (%)",
        yaxis=dict(range=[0, 100]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=height,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_custom_metric_chart(data, chart_type="bar", title="Métricas Customizadas"):
    """Create a custom chart based on provided data"""
    if not data:
        st.warning("Nenhum dado fornecido")
        return
    
    df = pd.DataFrame(data)
    
    if chart_type == "bar":
        fig = px.bar(df, x=df.columns[0], y=df.columns[1], 
                     color_discrete_sequence=['#FF6B6B'])
    elif chart_type == "line":
        fig = px.line(df, x=df.columns[0], y=df.columns[1])
    elif chart_type == "pie":
        fig = px.pie(df, values=df.columns[1], names=df.columns[0])
    elif chart_type == "scatter":
        fig = px.scatter(df, x=df.columns[0], y=df.columns[1],
                        color_discrete_sequence=['#4ECDC4'])
    else:
        st.error("Tipo de gráfico não suportado")
        return
    
    fig.update_layout(
        title=title,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_comparison_chart(data1, data2, labels, title="Comparação"):
    """Create a comparison chart between two datasets"""
    x = list(range(len(labels)))
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=labels[0] if len(labels) >= 2 else 'Dataset 1',
        x=x,
        y=data1,
        marker_color='#FF6B6B'
    ))
    
    fig.add_trace(go.Bar(
        name=labels[1] if len(labels) >= 2 else 'Dataset 2',
        x=x,
        y=data2,
        marker_color='#4ECDC4'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Categorias",
        yaxis_title="Valores",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)