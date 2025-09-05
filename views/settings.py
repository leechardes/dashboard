import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

def run():
    """Settings page for managing project paths configuration"""
    
    st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem; color: var(--info-color);">settings</span>Configurações</div>', unsafe_allow_html=True)
    
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
    tab1, tab2, tab3 = st.tabs(["Caminhos dos Projetos", "Configurações Gerais", "Estatísticas"])
    
    with tab1:
        st.subheader("Configuração de Caminhos dos Projetos")
        st.info("Configure quais diretórios contêm projetos a serem documentados")
        
        # Current paths
        st.markdown("### Caminhos Atuais")
        
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
                        new_enabled = st.checkbox("Habilitado", value=path_config["enabled"], key=f"enabled_{idx}")
                    with col1b:
                        new_auto = st.checkbox("Descoberta Automática", value=path_config["auto_discover"], key=f"auto_{idx}")
                    with col1c:
                        new_color = st.color_picker("Cor", value=path_config.get("color", "#2196f3"), key=f"color_{idx}")
                
                with col2:
                    st.markdown("### Ações")
                    if st.button(":material/delete: Remover", key=f"remove_{idx}"):
                        paths_modified = True
                        continue  # Skip this path
                    
                    # Check if path exists
                    if os.path.exists(new_path):
                        st.success("Caminho existe")
                    else:
                        st.error("Caminho não encontrado")
                
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
        st.markdown("### Adicionar Novo Caminho")
        with st.form("add_path_form"):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                new_path_input = st.text_input("Caminho do Projeto", placeholder="/srv/projects/example")
                new_id_input = st.text_input("ID", placeholder="example")
                new_desc_input = st.text_input("Descrição", placeholder="Projetos de exemplo")
                
                col1a, col1b = st.columns(2)
                with col1a:
                    new_enabled_input = st.checkbox("Habilitado", value=True)
                with col1b:
                    new_auto_input = st.checkbox("Descoberta Automática", value=True)
                
                new_color_input = st.color_picker("Cor", value="#4caf50")
            
            with col2:
                st.markdown("&nbsp;")  # Spacing
                if st.form_submit_button(":material/add: Adicionar Caminho", type="primary"):
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
                        st.success(f"Caminho adicionado: {new_path_input}")
                        st.rerun()
                    else:
                        st.error("Por favor, forneça tanto o ID quanto o Caminho")
        
        # Update config if paths were modified
        if paths_modified:
            config["paths"] = updated_paths
    
    with tab2:
        st.subheader("Configurações Gerais")
        
        # Max depth setting
        new_max_depth = st.number_input(
            "Profundidade Máxima de Busca",
            min_value=1,
            max_value=10,
            value=config["settings"].get("max_depth", 5),
            help="Profundidade máxima de diretórios para buscar projetos"
        )
        
        # Template directory
        new_template_dir = st.text_input(
            "Diretório de Templates",
            value=config["settings"].get("template_dir", "/srv/projects/shared/scripts/docs-templates"),
            help="Diretório contendo templates de documentação"
        )
        
        # Exclude patterns
        st.markdown("### Padrões de Exclusão")
        st.info("Diretórios que correspondem a estes padrões serão excluídos da busca")
        
        exclude_patterns = config["settings"].get("exclude_patterns", [])
        new_patterns = st.text_area(
            "Padrões (um por linha)",
            value="\n".join(exclude_patterns),
            height=150,
            help="Digite nomes de diretórios para excluir, um por linha"
        )
        
        # Update settings
        config["settings"]["max_depth"] = new_max_depth
        config["settings"]["template_dir"] = new_template_dir
        config["settings"]["exclude_patterns"] = [p.strip() for p in new_patterns.split("\n") if p.strip()]
    
    with tab3:
        st.subheader("Estatísticas da Configuração")
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_paths = len(config["paths"])
            st.metric("Total de Caminhos", total_paths)
        
        with col2:
            enabled_paths = sum(1 for p in config["paths"] if p["enabled"])
            st.metric("Caminhos Habilitados", enabled_paths)
        
        with col3:
            auto_discover = sum(1 for p in config["paths"] if p["auto_discover"])
            st.metric("Descoberta Automática", auto_discover)
        
        # Path details table
        st.markdown("### Detalhes dos Caminhos")
        
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
                    "Habilitado": "Sim" if path["enabled"] else "Não",
                    "Auto": "Sim" if path["auto_discover"] else "Não",
                    "Existe": "Sim" if os.path.exists(path["path"]) else "Não",
                    "Projetos": project_count if project_count >= 0 else "Erro"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, width=None, hide_index=True)
        
        # Configuration info
        st.markdown("### Arquivo de Configuração")
        st.code(str(config_file), language="text")
        
        st.markdown("### Última Atualização")
        st.text(config.get("last_updated", "Desconhecido"))
    
    # Save button (fixed at bottom)
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button(":material/save: Salvar Configuração", type="primary"):
            try:
                # Update timestamp
                config["last_updated"] = datetime.now().isoformat() + "Z"
                
                # Ensure directory exists
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Save configuration
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                st.success("Configuração salva com sucesso!")
                
                # Show which scripts will be affected
                with st.expander("Scripts Afetados", expanded=True):
                    scripts = [
                        "discover-projects-to-document.sh",
                        "populate-verification-json.sh",
                        "quick-docs-setup.sh",
                        "standardize-docs-filenames.sh",
                        "summary-docs.sh",
                        "update-agents-template.sh"
                    ]
                    
                    st.info("Os seguintes scripts usarão a nova configuração:")
                    for script in scripts:
                        st.text(f"• {script}")
                
                st.balloons()
                
            except Exception as e:
                st.error(f"Erro ao salvar configuração: {str(e)}")
    
    # Display current configuration (debug)
    with st.expander("Ver Configuração Bruta", expanded=False):
        st.json(config)