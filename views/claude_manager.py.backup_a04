"""Claude Manager view - Direct implementation"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

def run():
    """Run the Claude Manager view"""
    # Import and execute the full Claude Manager
    try:
        # Import directly from views
        from views import claude_manager_full
        
        # Execute the Claude Manager code
        import importlib
        importlib.reload(claude_manager_full)
        
    except Exception as e:
        st.error(f"Failed to load Claude Manager: {str(e)}")
        st.info("Trying alternative method...")
        
        # Alternative: Execute the file directly
        try:
            claude_manager_path = parent_dir / "views" / "claude_manager_full.py"
            if claude_manager_path.exists():
                exec(open(claude_manager_path).read(), globals())
            else:
                st.error("Claude Manager file not found!")
        except Exception as e2:
            st.error(f"Alternative method also failed: {str(e2)}")