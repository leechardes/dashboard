import streamlit as st
import psutil
import datetime

def create_metric_card(title, value, icon="analytics"):
    """Create a styled metric card"""
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.8rem; color: var(--text-color-secondary); margin-bottom: 0.2rem;">{title}</div>
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--text-color);">{value}</div>
            </div>
            <div class="material-icons" style="font-size: 2rem; color: var(--primary-color);">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_system_metrics():
    """Create a set of system metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_percent = psutil.cpu_percent(interval=1)
        create_metric_card("CPU Usage", f"{cpu_percent}%", "desktop_windows")
    
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

def create_progress_metric(title, current, total, unit="", icon="analytics"):
    """Create a progress metric with progress bar"""
    percentage = (current / total) * 100 if total > 0 else 0
    
    st.markdown(f"**{icon} {title}**")
    st.progress(percentage / 100)
    st.caption(f"{current:.1f}{unit} / {total:.1f}{unit} ({percentage:.1f}%)")

def create_status_metric(title, status, icon="analytics"):
    """Create a status metric with colored indicator"""
    color_map = {
        "online": "var(--success-color)",
        "offline": "var(--error-color)", 
        "warning": "var(--warning-color)",
        "info": "var(--info-color)",
        "clean": "var(--success-color)",
        "modified": "var(--warning-color)",
        "error": "var(--error-color)"
    }
    
    color = color_map.get(status.lower(), "var(--text-muted)")
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem;">
        <div class="material-icons" style="font-size: 1.2rem; color: var(--text-color);">{icon}</div>
        <div>
            <div style="font-weight: 600; color: var(--text-color);">{title}</div>
            <div style="color: {color}; font-size: 0.9rem;">{status.upper()}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_info_grid(data, columns=2):
    """Create an information grid layout"""
    items = list(data.items())
    cols = st.columns(columns)
    
    for i, (key, value) in enumerate(items):
        with cols[i % columns]:
            st.metric(key, value)

def create_expandable_metric(title, value, details, icon="analytics"):
    """Create an expandable metric card with details"""
    with st.expander(f"{title}: {value}"):  # Using emoji temporarily for expander compatibility
        if isinstance(details, dict):
            for key, val in details.items():
                st.text(f"{key}: {val}")
        elif isinstance(details, list):
            for item in details:
                st.text(f"• {item}")
        else:
            st.text(str(details))

def create_comparison_metric(title, current, previous, unit="", icon="analytics"):
    """Create a metric with comparison to previous value"""
    if previous != 0:
        change = ((current - previous) / previous) * 100
        change_color = "var(--success-color)" if change >= 0 else "var(--error-color)"
        change_icon = "trending_up" if change >= 0 else "trending_down"
        change_text = f"{change:+.1f}%"
    else:
        change_color = "var(--text-muted)"
        change_icon = "remove"
        change_text = "N/A"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.2rem;">{title}</div>
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--text-color);">{current}{unit}</div>
                <div style="font-size: 0.8rem; color: {change_color}; display: flex; align-items: center; gap: 0.2rem;">
                    <span class="material-icons" style="font-size: 1rem; color: {change_color};">{change_icon}</span>
                    {change_text}
                </div>
            </div>
            <div class="material-icons" style="font-size: 2rem; color: var(--primary-color);">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_gauge_metric(title, value, max_value, icon="analytics", color_thresholds=None):
    """Create a gauge-style metric"""
    percentage = (value / max_value) * 100 if max_value > 0 else 0
    
    # Default color thresholds
    if color_thresholds is None:
        color_thresholds = [(50, "var(--success-color)"), (75, "var(--warning-color)"), (100, "var(--error-color)")]
    
    # Determine color based on thresholds
    color = "var(--text-muted)"
    for threshold, threshold_color in color_thresholds:
        if percentage <= threshold:
            color = threshold_color
            break
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="text-align: center;">
            <div class="material-icons" style="font-size: 2rem; margin-bottom: 0.5rem; color: var(--primary-color);">{icon}</div>
            <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.5rem;">{title}</div>
            <div style="font-size: 2rem; font-weight: 600; color: {color}; margin-bottom: 0.5rem;">
                {value}
            </div>
            <div style="background: var(--secondary-background-color); border-radius: 10px; overflow: hidden; height: 8px;">
                <div style="background: {color}; height: 100%; width: {percentage}%;"></div>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.3rem;">
                {percentage:.1f}% of {max_value}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_table_metric(title, data, icon="analytics"):
    """Create a table-style metric display"""
    st.markdown(f"### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>{icon}</span>{title}", unsafe_allow_html=True)
    
    if isinstance(data, dict):
        # Convert dict to list of tuples for table display
        table_data = [(key, value) for key, value in data.items()]
        
        for key, value in table_data:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.text(key)
            with col2:
                st.text(str(value))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                cols = st.columns(len(item))
                for i, (key, value) in enumerate(item.items()):
                    with cols[i]:
                        st.metric(key, value)
            else:
                st.text(f"• {item}")

def create_alert_metric(title, message, alert_type="info", icon=None):
    """Create an alert-style metric"""
    if icon is None:
        icon_map = {
            "info": "info",
            "success": "check_circle", 
            "warning": "warning",
            "error": "cancel"
        }
        icon = icon_map.get(alert_type, "info")
    
    alert_functions = {
        "info": st.info,
        "success": st.success,
        "warning": st.warning, 
        "error": st.error
    }
    
    # Create custom alert with Material Icons
    alert_colors = {
        "info": "var(--info-color)",
        "success": "var(--success-color)", 
        "warning": "var(--warning-color)",
        "error": "var(--error-color)"
    }
    color = alert_colors.get(alert_type, "var(--info-color)")
    
    st.markdown(f"""
    <div style="padding: 1rem; border-radius: 0.5rem; border-left: 4px solid {color}; background: var(--secondary-background-color); margin: 0.5rem 0;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="material-icons" style="color: {color};">{icon}</span>
            <strong style="color: var(--text-color);">{title}:</strong>
            <span style="color: var(--text-color);">{message}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_trend_metric(title, values, labels=None, icon="analytics"):
    """Create a simple trend metric with sparkline-like display"""
    if not values:
        st.warning(f"{title}: Nenhum dado disponível")  # Using emoji for warning compatibility
        return
    
    # Calculate trend
    if len(values) >= 2:
        trend_icon = "trending_up" if values[-1] > values[0] else "trending_down" if values[-1] < values[0] else "remove"
        trend = f"<span class='material-icons' style='font-size: 1.2rem;'>{trend_icon}</span>"
        change = values[-1] - values[-2] if len(values) >= 2 else 0
    else:
        trend = "<span class='material-icons' style='font-size: 1.2rem;'>remove</span>"
        change = 0
    
    st.markdown(f"### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>{icon}</span>{title}", unsafe_allow_html=True)
    
    # Display current value and trend
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Atual", f"{values[-1]:.1f}")
    
    with col2:
        st.markdown(f"**Tendência:** {trend}", unsafe_allow_html=True)
    
    with col3:
        st.metric("Mudança", f"{change:+.1f}")
    
    # Create simple line chart
    if labels and len(labels) == len(values):
        import pandas as pd
        df = pd.DataFrame({"Valor": values}, index=labels)
        st.line_chart(df)
    else:
        st.line_chart(values)