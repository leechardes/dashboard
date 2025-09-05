import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import views
from views import dashboard, documentation_antd, logs, repositories, system, settings, claude_manager, service_management

# Configure Streamlit page
st.set_page_config(
    page_title="Dev Dashboard",
    page_icon=":material/rocket:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Material Icons and adaptive CSS
try:
    with open('static/adaptive_theme.css', 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Custom CSS for better styling
st.markdown("""
<style>
    /* Material Icons Font */
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
    .material-icons {
        font-family: 'Material Icons';
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
        color: var(--text-color);
    }
    
    /* Adaptive theming for material icons */
    @media (prefers-color-scheme: dark) {
        .material-icons {
            color: var(--text-color);
            filter: brightness(0.9);
        }
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, var(--secondary-background-color) 0%, var(--background-color) 100%);
        border-radius: 10px;
        border: 1px solid var(--primary-color);
    }
    
    .metric-card {
        background: var(--secondary-background-color);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .nav-header {
        color: var(--primary-color);
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Sidebar header
    with st.sidebar:
        st.markdown('<div class="nav-header"><span class="material-icons">rocket_launch</span> Dev Dashboard</div>', unsafe_allow_html=True)
        st.markdown("---")
    
    # Create navigation using st.navigation  
    pages = [
        st.Page(dashboard.run, title="Painel", icon=":material/analytics:", url_path="dashboard"),
        st.Page(documentation_antd.run, title="Documentação", icon=":material/menu_book:", url_path="docs"),
        st.Page(repositories.run, title="Repositórios", icon=":material/folder:", url_path="repos"),
        st.Page(system.run, title="Sistema", icon=":material/desktop_windows:", url_path="system"),
        st.Page(claude_manager.run, title="Gerenciador Claude", icon=":material/computer:", url_path="claude-manager"),
        st.Page(service_management.run, title="Controle de Serviços", icon=":material/handyman:", url_path="service-control"),
        st.Page(logs.run, title="Logs", icon=":material/assignment:", url_path="logs"),
        st.Page(settings.run, title="Configurações", icon=":material/settings:", url_path="settings")
    ]
    
    # Navigation
    nav = st.navigation(pages)
    nav.run()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Status:** <span class='material-icons' style='color: var(--success-color); font-size: 1rem;'>check_circle</span> Online", unsafe_allow_html=True)
    st.sidebar.markdown(f"**Porta:** {os.getenv('STREAMLIT_SERVER_PORT', '8081')}")

if __name__ == "__main__":
    main()