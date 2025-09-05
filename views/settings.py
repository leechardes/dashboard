import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

def run():
    """Settings page for managing project paths configuration"""
    
    st.markdown('<div class="main-header"><span class="material-symbols-outlined">settings</span> Settings</div>', unsafe_allow_html=True)
    
    # Configuration file path
    config_file = Path("/srv/projects/shared/config/project-paths.json")
    
    # Load current configuration
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat() + "Z",
            "paths": [
                {
                    "id": "inoveon",
                    "path": "/srv/projects/inoveon",
                    "description": "Projetos principais Inoveon",
                    "enabled": True,
                    "auto_discover": True,
                    "color": "var(--primary-color)"
                }
            ],
            "settings": {
                "max_depth": 5,
                "template_dir": "/srv/projects/shared/scripts/docs-templates",
                "exclude_patterns": ["node_modules", "__pycache__", ".venv", "venv", "dist", "build"]
            }
        }
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Project Paths", "General Settings", "Statistics"])
    
    with tab1:
        st.subheader("Project Paths Configuration")
        st.info("Configure which directories contain projects to be documented")
        
        # Current paths
        st.markdown("### Current Paths")
        
        paths_modified = False
        updated_paths = []
        
        for idx, path_config in enumerate(config["paths"]):
            with st.expander(f"**{path_config['id']}** - {path_config['path']}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Editable fields
                    new_id = st.text_input("ID", value=path_config["id"], key=f"id_{idx}")
                    new_path = st.text_input("Path", value=path_config["path"], key=f"path_{idx}")
                    new_desc = st.text_input("Description", value=path_config["description"], key=f"desc_{idx}")
                    
                    col1a, col1b, col1c = st.columns(3)
                    with col1a:
                        new_enabled = st.checkbox("Enabled", value=path_config["enabled"], key=f"enabled_{idx}")
                    with col1b:
                        new_auto = st.checkbox("Auto Discover", value=path_config["auto_discover"], key=f"auto_{idx}")
                    with col1c:
                        new_color = st.color_picker("Color", value=path_config.get("color", "#2196f3"), key=f"color_{idx}")
                
                with col2:
                    st.markdown("### Actions")
                    if st.button("Remove", key=f"remove_{idx}", use_container_width=True):
                        paths_modified = True
                        continue  # Skip this path
                    
                    # Check if path exists
                    if os.path.exists(new_path):
                        st.success("Path exists")
                    else:
                        st.error("Path not found")
                
                # Update path config if changed
                if (new_id != path_config["id"] or 
                    new_path != path_config["path"] or 
                    new_desc != path_config["description"] or
                    new_enabled != path_config["enabled"] or
                    new_auto != path_config["auto_discover"] or
                    new_color != path_config.get("color", "#2196f3")):
                    paths_modified = True
                
                updated_paths.append({
                    "id": new_id,
                    "path": new_path,
                    "description": new_desc,
                    "enabled": new_enabled,
                    "auto_discover": new_auto,
                    "color": new_color
                })
        
        # Add new path section
        st.markdown("### Add New Path")
        with st.form("add_path_form"):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                new_path_input = st.text_input("Project Path", placeholder="/srv/projects/example")
                new_id_input = st.text_input("ID", placeholder="example")
                new_desc_input = st.text_input("Description", placeholder="Example projects")
                
                col1a, col1b = st.columns(2)
                with col1a:
                    new_enabled_input = st.checkbox("Enabled", value=True)
                with col1b:
                    new_auto_input = st.checkbox("Auto Discover", value=True)
                
                new_color_input = st.color_picker("Color", value="#4caf50")
            
            with col2:
                st.markdown("&nbsp;")  # Spacing
                if st.form_submit_button("Add Path", use_container_width=True, type="primary"):
                    if new_path_input and new_id_input:
                        updated_paths.append({
                            "id": new_id_input,
                            "path": new_path_input,
                            "description": new_desc_input or f"Projects in {new_path_input}",
                            "enabled": new_enabled_input,
                            "auto_discover": new_auto_input,
                            "color": new_color_input
                        })
                        paths_modified = True
                        st.success(f"Added path: {new_path_input}")
                        st.rerun()
                    else:
                        st.error("Please provide both ID and Path")
        
        # Update config if paths were modified
        if paths_modified:
            config["paths"] = updated_paths
    
    with tab2:
        st.subheader("General Settings")
        
        # Max depth setting
        new_max_depth = st.number_input(
            "Max Search Depth",
            min_value=1,
            max_value=10,
            value=config["settings"].get("max_depth", 5),
            help="Maximum directory depth to search for projects"
        )
        
        # Template directory
        new_template_dir = st.text_input(
            "Templates Directory",
            value=config["settings"].get("template_dir", "/srv/projects/shared/scripts/docs-templates"),
            help="Directory containing documentation templates"
        )
        
        # Exclude patterns
        st.markdown("### Exclude Patterns")
        st.info("Directories matching these patterns will be excluded from search")
        
        exclude_patterns = config["settings"].get("exclude_patterns", [])
        new_patterns = st.text_area(
            "Patterns (one per line)",
            value="\n".join(exclude_patterns),
            height=150,
            help="Enter directory names to exclude, one per line"
        )
        
        # Update settings
        config["settings"]["max_depth"] = new_max_depth
        config["settings"]["template_dir"] = new_template_dir
        config["settings"]["exclude_patterns"] = [p.strip() for p in new_patterns.split("\n") if p.strip()]
    
    with tab3:
        st.subheader("Configuration Statistics")
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_paths = len(config["paths"])
            st.metric("Total Paths", total_paths)
        
        with col2:
            enabled_paths = sum(1 for p in config["paths"] if p["enabled"])
            st.metric("Enabled Paths", enabled_paths)
        
        with col3:
            auto_discover = sum(1 for p in config["paths"] if p["auto_discover"])
            st.metric("Auto Discover", auto_discover)
        
        # Path details table
        st.markdown("### Path Details")
        
        if config["paths"]:
            import pandas as pd
            
            df_data = []
            for path in config["paths"]:
                # Check if path exists and count projects
                project_count = 0
                if os.path.exists(path["path"]):
                    try:
                        # Count .git directories
                        for root, dirs, _ in os.walk(path["path"]):
                            project_count += sum(1 for d in dirs if d == ".git")
                            # Don't recurse into .git directories
                            dirs[:] = [d for d in dirs if d != ".git"]
                    except:
                        project_count = -1
                
                df_data.append({
                    "ID": path["id"],
                    "Path": path["path"],
                    "Enabled": "Sim" if path["enabled"] else "Não",
                    "Auto": "Sim" if path["auto_discover"] else "Não",
                    "Exists": "Sim" if os.path.exists(path["path"]) else "Não",
                    "Projects": project_count if project_count >= 0 else "Error"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Configuration info
        st.markdown("### Configuration File")
        st.code(str(config_file), language="text")
        
        st.markdown("### Last Updated")
        st.text(config.get("last_updated", "Unknown"))
    
    # Save button (fixed at bottom)
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button("Save Configuration", use_container_width=True, type="primary"):
            try:
                # Update timestamp
                config["last_updated"] = datetime.now().isoformat() + "Z"
                
                # Ensure directory exists
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Save configuration
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                st.success("Configuration saved successfully!")
                
                # Show which scripts will be affected
                with st.expander("Affected Scripts", expanded=True):
                    scripts = [
                        "discover-projects-to-document.sh",
                        "populate-verification-json.sh",
                        "quick-docs-setup.sh",
                        "standardize-docs-filenames.sh",
                        "summary-docs.sh",
                        "update-agents-template.sh"
                    ]
                    
                    st.info("The following scripts will use the new configuration:")
                    for script in scripts:
                        st.text(f"• {script}")
                
                st.balloons()
                
            except Exception as e:
                st.error(f"Error saving configuration: {str(e)}")
    
    # Display current configuration (debug)
    with st.expander("View Raw Configuration", expanded=False):
        st.json(config)