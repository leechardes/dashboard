import streamlit as st
import os
import subprocess
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.file_scanner import (
    scan_markdown_files, 
    categorize_documents, 
    get_document_statistics,
    search_files_content,
    build_document_tree
)
from utils.agent_scanner import AgentScanner
from components.markdown_viewer import render_markdown_file, create_toc
from collections import defaultdict

# Initialize agent scanner
agent_scanner = AgentScanner()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_documentation_files():
    """Get all markdown files from the project directories"""
    return scan_markdown_files()

def render_tree_streamlit(docs):
    """Render tree using Streamlit native components"""
    tree = build_document_tree(docs)
    
    def render_node(name, node, level=0, parent_key=""):
        """Recursively render tree nodes"""
        node_key = f"{parent_key}_{name}".replace('/', '_').replace('.', '_').replace(' ', '_')
        
        if node.get('_type') == 'folder':
            # Count documents in folder
            doc_count = count_docs_in_node(node)
            folder_icon = "Projeto" if level == 0 else "Pasta"
            
            # Create expander for folder with indentation
            indent = "　" * level  # Using full-width space for better indentation
            with st.expander(f"{indent}{folder_icon} {name} ({doc_count} docs)", expanded=(level < 1)):
                if '_children' in node:
                    # Sort: folders first, then files
                    sorted_children = sorted(
                        node['_children'].items(),
                        key=lambda x: (x[1]['_type'] != 'folder', x[0].lower())
                    )
                    
                    for child_name, child_node in sorted_children:
                        render_node(child_name, child_node, level + 1, node_key)
        else:
            # File node
            doc = node['_doc']
            doc_icons = {
                'README': '',
                'License': '',
                'Changelog': '',
                'TODO': '',
                'API': '',
                'Guide': '',
                'Docker': '',
                'Security': '',
                'FAQ': '',
                'Contributing': '',
                'Installation': '',
                'Configuration': '',
                'Testing': '',
                'Environment': ''
            }
            doc_icon = doc_icons.get(doc.get('doc_type', 'Documentation'), '')
            
            # Create button for file with indentation
            indent = "　" * (level + 1)
            file_label = f"{indent}{doc_icon} {name[:40]}{'...' if len(name) > 40 else ''} ({doc.get('size_kb', 0):.1f} KB)"
            
            if st.button(
                file_label,
                key=f"file_{node_key}",
                use_container_width=True,
                help=f"Caminho: {doc['path']} | Modificado: {doc.get('modified', 'N/A')}"
            ):
                st.session_state.selected_doc = doc
                st.session_state.selected_doc_path = doc['path']
                st.session_state.show_inline = True
                st.rerun()
    
    # Render tree
    for root_name, root_node in sorted(tree.items()):
        # Skip common root folders to flatten the structure
        if root_name in ['srv', 'home', 'var']:
            if '_children' in root_node:
                for child_name, child_node in sorted(root_node['_children'].items()):
                    render_node(child_name, child_node, 0, "root")
        else:
            render_node(root_name, root_node, 0, "root")

def count_docs_in_node(node):
    """Count documents in a node recursively"""
    if node.get('_type') == 'file':
        return 1
    
    count = 0
    if '_children' in node:
        for child in node['_children'].values():
            count += count_docs_in_node(child)
    
    return count

def render_agent_metrics():
    """Render agent verification metrics"""
    st.markdown("### <span class='material-symbols-outlined'>smart_toy</span> Agent Documentation Status", unsafe_allow_html=True)
    
    # Get data
    projects, total_stats = agent_scanner.scan_all_verification_jsons()
    
    if total_stats['total_projects'] == 0:
        st.info("No agent verification data found. Run the documentation agents first.")
        return
    
    # Display overall metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Projects",
            total_stats['total_projects'],
            delta=f"{total_stats['projects_complete']} complete"
        )
    
    with col2:
        st.metric(
            "Total Files",
            total_stats['total_files']
        )
    
    with col3:
        st.metric(
            "Verified Files",
            total_stats['verified_files'],
            delta=f"{total_stats['verified_files']/total_stats['total_files']*100:.1f}%" if total_stats['total_files'] > 0 else "0%"
        )
    
    with col4:
        st.metric(
            "Pending Files",
            total_stats['pending_files'],
            delta="-" + str(total_stats['pending_files']) if total_stats['pending_files'] > 0 else "OK",
            delta_color="inverse"
        )
    
    with col5:
        overall_completion = (total_stats['verified_files'] / total_stats['total_files'] * 100) if total_stats['total_files'] > 0 else 0
        st.metric(
            "Overall Progress",
            f"{overall_completion:.1f}%",
            delta="Complete" if overall_completion == 100 else f"{100-overall_completion:.1f}% to go"
        )
    
    # Create visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for overall status
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Verified', 'Pending'],
            values=[total_stats['verified_files'], total_stats['pending_files']],
            hole=.3,
            marker_colors=['#00CC88', '#FF6B6B']
        )])
        fig_pie.update_layout(
            title="Overall File Verification Status",
            height=300
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart for projects status
        if projects:
            df_projects = pd.DataFrame(projects)
            df_top_pending = df_projects.nlargest(10, 'pending_files')
            
            if not df_top_pending.empty:
                fig_bar = px.bar(
                    df_top_pending,
                    x='project_name',
                    y='pending_files',
                    title="Top 10 Projects with Pending Files",
                    color='pending_files',
                    color_continuous_scale='Reds',
                    labels={'pending_files': 'Pending Files', 'project_name': 'Project'}
                )
                fig_bar.update_layout(
                    xaxis_tickangle=-45,
                    height=300
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    
    # Projects table with progress
    st.markdown("#### <span class='material-symbols-outlined'>analytics</span> Projects Documentation Status", unsafe_allow_html=True)
    
    if projects:
        df = pd.DataFrame(projects)
        
        # Format the dataframe for display
        df_display = df[['project_name', 'total_files', 'verified_files', 
                        'pending_files', 'completion_percentage', 'last_scan']]
        df_display.columns = ['Project', 'Total', 'Verified', 'Pending', 'Progress %', 'Last Scan']
        
        # Sort by pending files
        df_display = df_display.sort_values('Pending', ascending=False)
        
        # Display with styling
        st.dataframe(
            df_display,
            use_container_width=True,
            height=300,
            column_config={
                "Progress %": st.column_config.ProgressColumn(
                    "Progress %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

def render_action_buttons():
    """Render action buttons for maintenance scripts"""
    st.markdown("### <span class='material-symbols-outlined'>build</span> Documentation Maintenance Actions", unsafe_allow_html=True)
    
    scripts_path = Path("/srv/projects/shared/scripts/agents")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### <span class='material-symbols-outlined'>edit_note</span> File Management", unsafe_allow_html=True)
        
        if st.button(":material/refresh: Standardize Filenames", 
                    use_container_width=True,
                    help="Standardize all documentation filenames to UPPERCASE-WITH-HYPHENS"):
            script = scripts_path / "standardize-docs-filenames.sh"
            if script.exists():
                with st.spinner("Standardizing filenames..."):
                    try:
                        result = subprocess.run(
                            [str(script), "--quiet"],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode == 0:
                            st.success("Filenames standardized successfully!")
                            if result.stdout:
                                with st.expander("View details"):
                                    st.code(result.stdout)
                        else:
                            st.error("Error standardizing filenames")
                            if result.stderr:
                                st.code(result.stderr)
                    except subprocess.TimeoutExpired:
                        st.error("Operation timed out")
            else:
                st.error(f"Script not found: {script}")
    
    with col2:
        st.markdown("#### Update JSONs")
        
        if st.button("Update Verification JSONs",
                    use_container_width=True,
                    help="Scan all projects and update verification JSONs"):
            script = scripts_path / "populate-verification-json.sh"
            if script.exists():
                with st.spinner("Updating verification JSONs... This may take a while"):
                    try:
                        result = subprocess.run(
                            [str(script)],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if result.returncode == 0:
                            st.success("JSONs updated successfully!")
                            st.balloons()
                            # Force refresh of the page
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Error updating JSONs")
                            if result.stderr:
                                st.code(result.stderr)
                    except subprocess.TimeoutExpired:
                        st.error("Operation timed out after 5 minutes")
            else:
                st.error(f"Script not found: {script}")
        
        if st.button("Quick Docs Setup",
                    use_container_width=True,
                    help="Quick setup of documentation structure"):
            script = scripts_path / "quick-docs-setup.sh"
            if script.exists():
                with st.spinner("Running quick docs setup..."):
                    try:
                        result = subprocess.run(
                            [str(script)],
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        if result.returncode == 0:
                            st.success("Documentation setup complete!")
                            with st.expander("View output"):
                                st.code(result.stdout)
                        else:
                            st.error("Error in setup")
                            if result.stderr:
                                st.code(result.stderr)
                    except subprocess.TimeoutExpired:
                        st.error("Operation timed out after 2 minutes")
            else:
                st.error(f"Script not found: {script}")
    
    with col3:
        st.markdown("#### Automation")
        
        if st.button("Generate Summary",
                    use_container_width=True,
                    help="Generate documentation summary"):
            script = scripts_path / "summary-docs.sh"
            if script.exists():
                with st.spinner("Generating summary..."):
                    try:
                        result = subprocess.run(
                            [str(script)],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode == 0:
                            st.success("Summary generated!")
                            with st.expander("View summary"):
                                st.code(result.stdout)
                        else:
                            st.error("Error generating summary")
                            if result.stderr:
                                st.code(result.stderr)
                    except subprocess.TimeoutExpired:
                        st.error("Operation timed out")
            else:
                st.error(f"Script not found: {script}")
        
        # Master Coordinator - with warning
        st.warning("Long running process!")
        if st.button("Run Master Coordinator",
                    use_container_width=True,
                    type="primary",
                    help="Run the complete documentation process for all projects"):
            
            # Require confirmation
            with st.expander("Confirmation Required"):
                st.warning("This process can take a very long time (30+ minutes)")
                if st.checkbox("I understand this will take a long time"):
                    if st.button("Confirm and Run", type="primary"):
                        st.info("Starting Master Coordinator...")
                        st.warning("This process runs in background. Check terminal for progress.")
                        # TODO: Implement async execution with progress tracking
                        st.info("Feature in development - use terminal for now")

def render_analytics():
    """Render analytics and trends"""
    st.markdown("### <span class='material-symbols-outlined'>trending_up</span> Documentation Analytics", unsafe_allow_html=True)
    
    projects, total_stats = agent_scanner.scan_all_verification_jsons()
    
    if not projects:
        st.info("No data available for analytics")
        return
    
    df = pd.DataFrame(projects)
    
    # Distribution of completion
    fig_hist = px.histogram(
        df,
        x='completion_percentage',
        nbins=20,
        title="Distribution of Project Completion",
        labels={'completion_percentage': 'Completion %', 'count': 'Number of Projects'},
        color_discrete_sequence=['#4CAF50']
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Scatter plot - Files vs Completion
    fig_scatter = px.scatter(
        df,
        x='total_files',
        y='completion_percentage',
        size='pending_files',
        color='is_complete',
        title="Project Size vs Completion",
        labels={
            'total_files': 'Total Files',
            'completion_percentage': 'Completion %',
            'is_complete': 'Complete'
        },
        hover_data=['project_name'],
        color_discrete_map={True: '#00CC88', False: '#FF6B6B'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Recent activity
    st.markdown("#### Recent Activity")
    recent = agent_scanner.get_recent_activity(5)
    for project in recent:
        if project['last_scan'] != 'N/A':
            st.info(f"**{project['project_name']}** - Last scan: {project['last_scan'][:19]} - Progress: {project['completion_percentage']}%")

def run():
    """Enhanced documentation view with agent metrics"""
    
    st.markdown('<div class="main-header"><span class="material-symbols-outlined">library_books</span> Documentation Center</div>', unsafe_allow_html=True)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "Documents", 
        "Agent Status", 
        "Actions",
        "Analytics"
    ])
    
    with tab1:
        # Scan for documentation
        with st.spinner("Scanning documentation..."):
            docs = get_documentation_files()
        
        if not docs:
            st.warning("No documentation files found.")
            st.info("Looking for .md, .txt, .rst files in /srv/projects/")
            return
        
        # Get statistics
        stats = get_document_statistics(docs)
        
        # Statistics row
        st.markdown("### <span class='material-symbols-outlined'>analytics</span> Statistics", unsafe_allow_html=True)
        stat_cols = st.columns(6)
        
        with stat_cols[0]:
            st.metric("Total", stats['total'])
    
    with stat_cols[1]:
        st.metric("Projetos", len(stats['by_project']))
    
    with stat_cols[2]:
        st.metric("Categorias", len(stats['by_category']))
    
    with stat_cols[3]:
        st.metric("Tipos", len(stats['by_type']))
    
    with stat_cols[4]:
        st.metric("Tamanho", f"{stats['total_size_mb']:.1f} MB")
    
    with stat_cols[5]:
        if st.button(":material/refresh: Atualizar"):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Search and filters
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "Buscar documentos", 
            placeholder="Digite para filtrar documentos...",
            help="Filtra documentos por nome, caminho ou tipo"
        )
    
    with col2:
        # Project filter
        project_options = ["Todos"] + sorted(list(stats['by_project'].keys()))
        selected_project = st.selectbox("Projeto", project_options)
    
    with col3:
        # Category filter (apis, web, mobile, etc)
        category_options = ["Todas"] + sorted(list(stats['by_category'].keys()))
        selected_category = st.selectbox("Categoria", category_options)
    
    with col4:
        # Extension filter
        ext_options = ["Todas"] + sorted(list(stats['by_extension'].keys()))
        selected_ext = st.selectbox("Extensão", ext_options)
    
    # Apply filters
    filtered_docs = docs
    
    if selected_project != "Todos":
        filtered_docs = [d for d in filtered_docs if d.get('project') == selected_project]
    
    if selected_category != "Todas":
        filtered_docs = [d for d in filtered_docs if d.get('category') == selected_category]
    
    if selected_ext != "Todas":
        filtered_docs = [d for d in filtered_docs if d.get('extension') == selected_ext]
    
    if search_term:
        filtered_docs = [
            d for d in filtered_docs 
            if search_term.lower() in d['name'].lower() or 
               search_term.lower() in d['path'].lower() or
               search_term.lower() in d.get('doc_type', '').lower()
        ]
    
    # Two column layout
    tree_col, content_col = st.columns([1, 2])
    
    with tree_col:
        st.markdown("### <span class='material-symbols-outlined'>folder_open</span> Explorador de Documentos", unsafe_allow_html=True)
        
        # Add a container with scroll for the tree
        with st.container():
            if filtered_docs:
                # Add custom CSS for tree styling
                st.markdown("""
                <style>
                    div[data-testid="stExpander"] {
                        border: none;
                        background-color: transparent;
                    }
                    div[data-testid="stExpander"] > div:first-child {
                        background-color: rgba(28, 31, 35, 0.6);
                        border-radius: 4px;
                    }
                    div[data-testid="stExpander"] > div:first-child:hover {
                        background-color: rgba(48, 54, 61, 0.8);
                    }
                    .stButton > button {
                        text-align: left;
                        background-color: transparent;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 4px;
                    }
                    .stButton > button:hover {
                        background-color: rgba(48, 54, 61, 0.8);
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Render the tree
                render_tree_streamlit(filtered_docs)
            else:
                st.warning("Nenhum documento encontrado com os filtros aplicados.")
    
    with content_col:
        st.markdown("### Visualização")
        
        # Check if a document is selected
        if 'selected_doc' in st.session_state and st.session_state.get('show_inline', False):
            doc = st.session_state.selected_doc
            
            # Document header with info
            doc_type = doc.get('doc_type', 'Documentation')
            
            # Create a nice header
            st.success(f"""
            **{doc['name']}** ({doc_type})  
            Projeto: {doc.get('project', 'unknown')} | Categoria: {doc.get('category', 'general')}  
            Tamanho: {doc.get('size_kb', 0):.1f} KB | Modificado: {doc.get('modified', 'N/A')}
            """)
            
            # Show full path in expander
            with st.expander("Caminho completo"):
                st.code(doc['path'])
            
            # Render the document content
            if os.path.exists(doc['path']):
                try:
                    # Add a divider
                    st.markdown("---")
                    
                    # Render markdown
                    with st.container():
                        render_markdown_file(doc['path'])
                    
                except Exception as e:
                    st.error(f"Erro ao renderizar: {str(e)}")
            else:
                st.error("Arquivo não encontrado.")
            
            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Copiar caminho"):
                    st.code(doc['path'])
                    st.success("Caminho exibido acima para copiar!")
            
            with col2:
                if st.button(":material/refresh: Recarregar"):
                    st.rerun()
            
            with col3:
                if st.button("Fechar"):
                    st.session_state.show_inline = False
                    if 'selected_doc' in st.session_state:
                        del st.session_state.selected_doc
                    st.rerun()
        else:
            # No document selected
            st.info("""
            **Navegue pela árvore de documentos**
            
            • Clique nas pastas para expandir/colapsar
            • Clique nos arquivos para visualizar
            • Use os filtros para refinar a busca
            • A busca filtra documentos em tempo real
            """)
            
            # Show recent documents as suggestions
            if stats['recent']:
                st.markdown("### <span class='material-symbols-outlined'>history</span> Documentos Recentes", unsafe_allow_html=True)
                for i, doc in enumerate(stats['recent'][:5]):
                    doc_icon = ''
                    if 'readme' in doc['name'].lower():
                        doc_icon = ''
                    elif 'license' in doc['name'].lower():
                        doc_icon = ''
                    elif 'changelog' in doc['name'].lower():
                        doc_icon = ''
                    elif 'todo' in doc['name'].lower():
                        doc_icon = ''
                    
                    if st.button(
                        f"{doc_icon} {doc['name']}",
                        key=f"recent_{i}_{doc['path'].replace('/', '_').replace('.', '_')}",
                        use_container_width=True,
                        help=f"Projeto: {doc.get('project', 'unknown')} | Tamanho: {doc.get('size_kb', 0):.1f} KB"
                    ):
                        st.session_state.selected_doc = doc
                        st.session_state.selected_doc_path = doc['path']
                        st.session_state.show_inline = True
                        st.rerun()
    
    # Sidebar info
    with st.sidebar:
        st.markdown("---")
        st.subheader("Resumo")
        
        # Top projects
        st.markdown("**Top Projetos:**")
        for project, count in sorted(stats['by_project'].items(), key=lambda x: x[1], reverse=True)[:5]:
            project_display = project.replace('_', ' ').title()
            st.caption(f"• {project_display}: {count} docs")
        
        # Top categories
        st.markdown("**Top Categorias:**")
        for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True)[:5]:
            st.caption(f"• {category}: {count} docs")
        
        # Recent docs
        st.markdown("**Recentes:**")
        for doc in stats['recent'][:5]:
            st.caption(f"• {doc['name'][:20]}...")
        
        # Current filters
        if any([selected_project != "Todos", selected_category != "Todas", selected_ext != "Todas", search_term]):
            st.markdown("---")
            st.markdown("**Filtros Ativos:**")
            if selected_project != "Todos":
                st.caption(f"• Projeto: {selected_project}")
            if selected_category != "Todas":
                st.caption(f"• Categoria: {selected_category}")
            if selected_ext != "Todas":
                st.caption(f"• Extensão: {selected_ext}")
            if search_term:
                st.caption(f"• Busca: {search_term}")
            st.caption(f"{len(filtered_docs)} de {len(docs)} docs")
        
        # Export
        st.markdown("---")
        if st.button("Exportar Lista"):
            import pandas as pd
            df = pd.DataFrame(filtered_docs)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name="documentacao.csv",
                mime="text/csv"
            )
    
    with tab2:
        # Agent status metrics
        render_agent_metrics()
    
    with tab3:
        # Action buttons
        render_action_buttons()
    
    with tab4:
        # Analytics
        render_analytics()