import streamlit as st
import os
import subprocess
import glob
from utils.git_utils import scan_git_repositories, get_repo_info, get_repo_status
from collections import defaultdict

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_repositories():
    """Get all Git repositories"""
    return scan_git_repositories()

def categorize_repositories(repos):
    """Categorize repositories by type and project"""
    categories = {
        'apis': {'name': 'APIs', 'repos': [], 'icon': '🔌', 'keywords': ['api', 'gateway', 'auth', 'metadata']},
        'web': {'name': 'Web', 'repos': [], 'icon': '🌐', 'keywords': ['web', 'angular', 'react', 'vue']},
        'mobile': {'name': 'Mobile', 'repos': [], 'icon': '📱', 'keywords': ['mobile', 'flutter', 'android', 'ios']},
        'desktop': {'name': 'Desktop', 'repos': [], 'icon': '🖥️', 'keywords': ['desktop', 'electron']},
        'services': {'name': 'Services', 'repos': [], 'icon': '⚙️', 'keywords': ['service', 'worker', 'job', 'mcp']},
        'libs': {'name': 'Libraries', 'repos': [], 'icon': '📚', 'keywords': ['lib', 'library', 'util', 'helper']},
        'dashboards': {'name': 'Dashboards', 'repos': [], 'icon': '📊', 'keywords': ['dashboard', 'streamlit', 'panel']},
        'others': {'name': 'Outros', 'repos': [], 'icon': '📦', 'keywords': []}
    }
    
    # Categorize by path and name patterns
    for repo in repos:
        path = repo['path'].lower()
        name = repo['name'].lower()
        categorized = False
        
        # Check each category
        for cat_key, cat_info in categories.items():
            if cat_key == 'others':
                continue
                
            # Check if any keyword matches
            for keyword in cat_info['keywords']:
                if keyword in path or keyword in name:
                    categories[cat_key]['repos'].append(repo)
                    categorized = True
                    break
            
            if categorized:
                break
        
        # If not categorized, add to others
        if not categorized:
            categories['others']['repos'].append(repo)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v['repos']}

def organize_by_project(repos):
    """Organize repositories by project structure"""
    projects = defaultdict(lambda: {'repos': [], 'categories': defaultdict(list)})
    
    for repo in repos:
        path_parts = repo['path'].split('/')
        
        # Identify project and category from path
        # Example: /srv/projects/inoveon/i9_smart/apis/repo_name
        if 'inoveon' in path_parts:
            idx = path_parts.index('inoveon')
            if idx + 1 < len(path_parts):
                project_name = path_parts[idx + 1]  # e.g., 'i9_smart', 'asfrete', 'devflow'
                
                # Get category if exists
                if idx + 2 < len(path_parts):
                    category = path_parts[idx + 2]  # e.g., 'apis', 'web', 'mobile'
                    projects[project_name]['categories'][category].append(repo)
                else:
                    projects[project_name]['repos'].append(repo)
        else:
            # Other repos not in inoveon
            projects['others']['repos'].append(repo)
    
    return dict(projects)

def display_repository_card(repo, index):
    """Display a repository card with complete information"""
    with st.expander(f"{repo.get('icon', '📁')} **{repo['name']}**", expanded=False):
        
        # Repository info columns
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.info(f"""
            **📂 Nome:** {repo['name']}
            **🗂️ Caminho:** {repo['path']}
            **🌿 Branch Atual:** {repo.get('current_branch', 'N/A')}
            **📏 Tamanho:** {repo.get('size_mb', 0):.1f} MB
            """)
        
        with info_col2:
            # Get detailed repo status
            try:
                status = get_repo_status(repo['path'])
                
                # Status indicators
                status_text = "✅ Limpo" if status.get('is_clean', False) else "⚠️ Modificado"
                
                st.info(f"""
                **🔄 Status:** {status_text}
                **📝 Commits:** {status.get('commit_count', 'N/A')}
                **🏷️ Tags:** {status.get('tag_count', 'N/A')}
                **🌿 Branches:** {len(status.get('branches', []))}
                """)
                
            except Exception as e:
                st.error(f"Erro ao obter status: {str(e)}")
                status = {}
        
        # Repository details
        st.markdown("---")
        
        # Tabs for different info
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Status", "🌿 Branches", "📋 Commits", "📁 Arquivos"])
        
        with tab1:
            try:
                if not status.get('is_clean', True):
                    if status.get('modified_files'):
                        st.subheader("📝 Arquivos Modificados")
                        for file in status['modified_files']:
                            if file:  # Only show non-empty files
                                st.text(f"• {file}")
                    
                    if status.get('untracked_files'):
                        st.subheader("➕ Arquivos Não Rastreados")
                        for file in status['untracked_files']:
                            if file:  # Only show non-empty files
                                st.text(f"• {file}")
                    
                    if status.get('staged_files'):
                        st.subheader("✅ Arquivos Staged")
                        for file in status['staged_files']:
                            if file:  # Only show non-empty files
                                st.text(f"• {file}")
                else:
                    st.success("✅ Repositório limpo - sem modificações pendentes")
            
            except Exception as e:
                st.error(f"Erro ao obter status detalhado: {str(e)}")
        
        with tab2:
            try:
                info = get_repo_info(repo['path'])
                branches = info.get('branches', [])
                
                if branches:
                    st.subheader("🌿 Branches Disponíveis")
                    for branch in branches:
                        current = "👉 " if branch == repo.get('current_branch') else "   "
                        st.text(f"{current}{branch}")
                else:
                    st.info("Nenhuma branch encontrada")
            
            except Exception as e:
                st.error(f"Erro ao obter branches: {str(e)}")
        
        with tab3:
            try:
                info = get_repo_info(repo['path'])
                commits = info.get('recent_commits', [])
                
                if commits:
                    st.subheader("📋 Commits Recentes")
                    for commit in commits[:10]:  # Show last 10 commits
                        st.text(f"• {commit}")
                else:
                    st.info("Nenhum commit encontrado")
            
            except Exception as e:
                st.error(f"Erro ao obter commits: {str(e)}")
        
        with tab4:
            # Show repository structure
            try:
                files = glob.glob(os.path.join(repo['path'], '*'), recursive=False)
                files = [os.path.basename(f) for f in files if not f.startswith('.git')]
                files.sort()
                
                if files:
                    st.subheader("📁 Estrutura do Projeto")
                    
                    # Show in columns
                    cols = st.columns(3)
                    for file_idx, file in enumerate(files):
                        with cols[file_idx % 3]:
                            if os.path.isdir(os.path.join(repo['path'], file)):
                                st.text(f"📁 {file}/")
                            else:
                                st.text(f"📄 {file}")
                else:
                    st.info("Diretório vazio")
            
            except Exception as e:
                st.error(f"Erro ao listar arquivos: {str(e)}")
        
        # Action buttons
        st.markdown("---")
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            if st.button(f"📂 Abrir", key=f"open_{index}_{repo['name']}"):
                st.info(f"Caminho: {repo['path']}")
        
        with action_col2:
            if st.button(f"🔄 Status", key=f"status_{index}_{repo['name']}"):
                try:
                    result = subprocess.run(
                        ['git', 'status', '--porcelain'],
                        cwd=repo['path'],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        st.code(result.stdout, language='bash')
                    else:
                        st.success("Working directory clean")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        
        with action_col3:
            if st.button(f"⬇️ Pull", key=f"pull_{index}_{repo['name']}"):
                try:
                    with st.spinner("Fazendo git pull..."):
                        result = subprocess.run(
                            ['git', 'pull'],
                            cwd=repo['path'],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if result.returncode == 0:
                            st.success("✅ Pull realizado com sucesso!")
                            if result.stdout:
                                st.code(result.stdout, language='bash')
                        else:
                            st.error("❌ Erro ao fazer pull")
                            if result.stderr:
                                st.code(result.stderr, language='bash')
                except subprocess.TimeoutExpired:
                    st.error("⏱️ Timeout - operação demorou muito")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        
        with action_col4:
            if st.button(f"🌐 Remote", key=f"remote_{index}_{repo['name']}"):
                try:
                    result = subprocess.run(
                        ['git', 'remote', '-v'],
                        cwd=repo['path'],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        st.code(result.stdout, language='bash')
                    else:
                        st.info("Nenhum remote configurado")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")

def run():
    """Git repositories management view with improved organization"""
    
    st.markdown('<div class="main-header">📁 Gerenciador de Repositórios</div>', unsafe_allow_html=True)
    
    # Scan for repositories
    with st.spinner("Escaneando repositórios Git..."):
        repos = get_all_repositories()
    
    if not repos:
        st.warning("Nenhum repositório Git encontrado.")
        st.info("Procurando em /srv/projects/ por diretórios .git/")
        return
    
    # Display mode selector
    display_mode = st.radio(
        "Modo de visualização:",
        ["📊 Por Categoria", "🏗️ Por Projeto", "📋 Lista Simples"],
        horizontal=True
    )
    
    # Statistics
    st.markdown("### 📈 Estatísticas")
    stat_cols = st.columns(6)
    
    with stat_cols[0]:
        st.metric("Total", len(repos))
    
    # Count by category
    categories = categorize_repositories(repos)
    for i, (cat_key, cat_info) in enumerate(categories.items(), 1):
        if i < len(stat_cols):
            with stat_cols[i]:
                st.metric(f"{cat_info['icon']} {cat_info['name']}", len(cat_info['repos']))
    
    st.markdown("---")
    
    # Search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Buscar repositório", placeholder="Digite o nome...")
    
    with col2:
        if display_mode == "📊 Por Categoria":
            selected_category = st.selectbox(
                "Categoria",
                ["Todas"] + [f"{cat_info['icon']} {cat_info['name']}" for cat_info in categories.values()]
            )
        else:
            selected_category = "Todas"
    
    with col3:
        # Get all unique branches
        all_branches = set()
        for repo in repos:
            if 'current_branch' in repo:
                all_branches.add(repo['current_branch'])
        
        selected_branch = st.selectbox(
            "Branch",
            ["Todos"] + sorted(list(all_branches))
        )
    
    # Apply filters
    filtered_repos = repos
    
    if search_term:
        filtered_repos = [
            repo for repo in filtered_repos 
            if search_term.lower() in repo['name'].lower() or 
               search_term.lower() in repo['path'].lower()
        ]
    
    if selected_branch != "Todos":
        filtered_repos = [
            repo for repo in filtered_repos 
            if repo.get('current_branch') == selected_branch
        ]
    
    # Display repositories based on selected mode
    if display_mode == "📊 Por Categoria":
        # Display by category
        categories = categorize_repositories(filtered_repos)
        
        for cat_key, cat_info in categories.items():
            if selected_category != "Todas" and f"{cat_info['icon']} {cat_info['name']}" != selected_category:
                continue
                
            if cat_info['repos']:
                st.markdown(f"### {cat_info['icon']} {cat_info['name']} ({len(cat_info['repos'])})")
                
                # Create columns for better layout
                for i in range(0, len(cat_info['repos']), 2):
                    cols = st.columns(2)
                    for j, col in enumerate(cols):
                        if i + j < len(cat_info['repos']):
                            with col:
                                repo = cat_info['repos'][i + j]
                                repo['icon'] = cat_info['icon']
                                display_repository_card(repo, i + j)
                
                st.markdown("---")
    
    elif display_mode == "🏗️ Por Projeto":
        # Display by project hierarchy
        projects = organize_by_project(filtered_repos)
        
        # Sort projects with i9_smart first
        sorted_projects = sorted(projects.items(), key=lambda x: (x[0] != 'i9_smart', x[0]))
        
        for project_name, project_data in sorted_projects:
            if project_name == 'others':
                project_display_name = "📦 Outros"
            else:
                project_display_name = project_name.replace('_', ' ').title()
                if 'i9_smart' in project_name:
                    project_display_name = f"🏢 {project_display_name}"
                elif 'devflow' in project_name:
                    project_display_name = f"🔧 {project_display_name}"
                elif 'asfrete' in project_name:
                    project_display_name = f"🚚 {project_display_name}"
            
            # Count total repos in project
            total_in_project = len(project_data['repos'])
            for cat_repos in project_data['categories'].values():
                total_in_project += len(cat_repos)
            
            st.markdown(f"### {project_display_name} ({total_in_project} repositórios)")
            
            # Display categories within project
            for category_name, category_repos in sorted(project_data['categories'].items()):
                if category_repos:
                    # Determine category icon
                    cat_icon = {
                        'apis': '🔌',
                        'web': '🌐',
                        'mobile': '📱',
                        'desktop': '🖥️',
                        'services': '⚙️'
                    }.get(category_name, '📁')
                    
                    with st.expander(f"{cat_icon} {category_name.upper()} ({len(category_repos)})", expanded=True):
                        for repo in category_repos:
                            repo['icon'] = cat_icon
                            display_repository_card(repo, 0)
            
            # Display uncategorized repos in project
            if project_data['repos']:
                with st.expander(f"📁 Outros ({len(project_data['repos'])})", expanded=True):
                    for repo in project_data['repos']:
                        display_repository_card(repo, 0)
            
            st.markdown("---")
    
    else:
        # Simple list mode
        st.markdown(f"### 📋 Lista de Repositórios ({len(filtered_repos)})")
        
        for i, repo in enumerate(filtered_repos):
            display_repository_card(repo, i)
    
    # Footer with refresh button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Atualizar Repositórios", use_container_width=True):
            st.cache_data.clear()
            st.rerun()