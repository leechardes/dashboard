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
    page_icon="🚀",  # Material: rocket_launch
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        st.Page(dashboard.run, title="Dashboard", icon="📊", url_path="dashboard"),  # Material: analytics
        st.Page(documentation_antd.run, title="Documentation", icon="📚", url_path="docs"),  # Material: menu_book
        st.Page(repositories.run, title="Repositories", icon="📁", url_path="repos"),  # Material: folder
        st.Page(system.run, title="System", icon="🖥️", url_path="system"),  # Material: desktop_windows
        st.Page(claude_manager.run, title="Claude Manager", icon="💻", url_path="claude-manager"),  # Material: computer
        st.Page(service_management.run, title="Service Control", icon="🛠️", url_path="service-control"),  # Material: handyman
        st.Page(logs.run, title="Logs", icon="📋", url_path="logs"),  # Material: assignment
        st.Page(settings.run, title="Settings", icon="⚙️", url_path="settings")  # Material: settings
    ]
    
    # Navigation
    nav = st.navigation(pages)
    nav.run()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Status:** <span class='material-icons' style='color: var(--success-color); font-size: 1rem;'>check_circle</span> Online", unsafe_allow_html=True)
    st.sidebar.markdown(f"**Port:** {os.getenv('STREAMLIT_SERVER_PORT', '8081')}")

if __name__ == "__main__":
    main()