import streamlit as st
import markdown2
import os
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

def render_markdown_file(file_path):
    """Render a markdown file with syntax highlighting"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        render_markdown_content(content)
        
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {str(e)}")

def render_markdown_content(content):
    """Render markdown content with enhanced features"""
    try:
        # Configure markdown2 with extensions
        extras = [
            'fenced-code-blocks',
            'tables',
            'strike',
            'task_list',
            'wiki-tables',
            'footnotes',
            'header-ids',
            'toc'
        ]
        
        # Process the markdown
        html = markdown2.markdown(content, extras=extras)
        
        # Apply syntax highlighting to code blocks
        html = apply_syntax_highlighting(html)
        
        # Apply custom CSS styling
        html = apply_markdown_styling(html)
        
        # Render the HTML
        st.markdown(html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao renderizar markdown: {str(e)}")
        # Fallback to basic markdown
        st.markdown(content)

def apply_syntax_highlighting(html):
    """Apply syntax highlighting to code blocks"""
    # Pattern to find code blocks with language specification
    code_pattern = r'<pre><code class="language-(\w+)">(.*?)</code></pre>'
    
    def highlight_code(match):
        language = match.group(1)
        code = match.group(2)
        
        try:
            # Decode HTML entities
            import html as html_module
            code = html_module.unescape(code)
            
            # Get lexer for the language
            lexer = get_lexer_by_name(language)
            
            # Create formatter with dark theme
            formatter = HtmlFormatter(
                style='monokai',
                cssclass='highlight',
                noclasses=True
            )
            
            # Highlight the code
            highlighted = highlight(code, lexer, formatter)
            
            # Wrap in a container with language label
            return f'''
            <div class="code-container">
                <div class="code-header">{language}</div>
                {highlighted}
            </div>
            '''
            
        except (ClassNotFound, Exception):
            # Fallback to plain code block
            return f'<pre><code>{code}</code></pre>'
    
    # Apply highlighting
    html = re.sub(code_pattern, highlight_code, html, flags=re.DOTALL)
    
    return html

def apply_markdown_styling(html):
    """Apply custom CSS styling to markdown HTML"""
    
    # Custom CSS for markdown content
    css = """
    <style>
    .markdown-content {
        color: #FAFAFA;
        line-height: 1.6;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .markdown-content h1 {
        color: #FF6B6B;
        border-bottom: 2px solid #FF6B6B;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    .markdown-content h2 {
        color: #4ECDC4;
        border-bottom: 1px solid #4ECDC4;
        padding-bottom: 0.3rem;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    
    .markdown-content h3 {
        color: #45B7D1;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }
    
    .markdown-content h4, .markdown-content h5, .markdown-content h6 {
        color: #96CEB4;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .markdown-content p {
        margin-bottom: 1rem;
        text-align: justify;
    }
    
    .markdown-content ul, .markdown-content ol {
        margin-bottom: 1rem;
        padding-left: 2rem;
    }
    
    .markdown-content li {
        margin-bottom: 0.3rem;
    }
    
    .markdown-content blockquote {
        border-left: 4px solid #FF6B6B;
        padding-left: 1rem;
        margin: 1rem 0;
        background: #262730;
        padding: 1rem;
        border-radius: 5px;
        font-style: italic;
    }
    
    .markdown-content code {
        background: #262730;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        font-family: 'Monaco', 'Consolas', monospace;
        color: #FF6B6B;
    }
    
    .markdown-content pre {
        background: #1E1E1E;
        padding: 1rem;
        border-radius: 5px;
        overflow-x: auto;
        margin: 1rem 0;
        border: 1px solid #333;
    }
    
    .markdown-content pre code {
        background: none;
        padding: 0;
        color: inherit;
    }
    
    .code-container {
        margin: 1rem 0;
    }
    
    .code-header {
        background: #FF6B6B;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px 5px 0 0;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .highlight {
        border-radius: 0 0 5px 5px;
        margin: 0 !important;
    }
    
    .markdown-content table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
        background: #262730;
        border-radius: 5px;
        overflow: hidden;
    }
    
    .markdown-content th {
        background: #FF6B6B;
        color: white;
        padding: 0.8rem;
        text-align: left;
        font-weight: 600;
    }
    
    .markdown-content td {
        padding: 0.8rem;
        border-bottom: 1px solid #444;
    }
    
    .markdown-content tr:nth-child(even) {
        background: #2A2A2A;
    }
    
    .markdown-content a {
        color: #4ECDC4;
        text-decoration: none;
    }
    
    .markdown-content a:hover {
        color: #FF6B6B;
        text-decoration: underline;
    }
    
    .markdown-content hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    .markdown-content img {
        max-width: 100%;
        height: auto;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .markdown-content .task-list-item {
        list-style: none;
        margin-left: -2rem;
    }
    
    .markdown-content .task-list-item input {
        margin-right: 0.5rem;
    }
    </style>
    """
    
    # Wrap content in styled container
    styled_html = f"{css}<div class='markdown-content'>{html}</div>"
    
    return styled_html

def render_log_content(log_path, max_lines=100):
    """Render log file content with syntax highlighting"""
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Get last N lines if file is too long
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
            st.info(f"Mostrando as últimas {max_lines} linhas de {len(lines)} total")
        
        # Join lines and apply log highlighting
        content = ''.join(lines)
        
        # Apply log-specific highlighting
        highlighted_content = apply_log_highlighting(content)
        
        # Display in code block
        st.markdown(highlighted_content, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao ler arquivo de log: {str(e)}")

def apply_log_highlighting(content):
    """Apply highlighting to log content"""
    css = """
    <style>
    .log-content {
        background: #1E1E1E;
        color: #FAFAFA;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 0.9rem;
        line-height: 1.4;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-height: 600px;
        overflow-y: auto;
        border: 1px solid #333;
    }
    
    .log-error { color: #FF6B6B; font-weight: 600; }
    .log-warning { color: #FFA726; font-weight: 600; }
    .log-info { color: #4ECDC4; }
    .log-debug { color: #96CEB4; }
    .log-timestamp { color: #888; }
    .log-level { font-weight: 600; }
    </style>
    """
    
    # Apply log level highlighting
    content = re.sub(r'(\[?\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[^\]]*\]?)', 
                     r'<span class="log-timestamp">\1</span>', content)
    
    content = re.sub(r'\b(ERROR|FATAL)\b', r'<span class="log-error">\1</span>', content, flags=re.IGNORECASE)
    content = re.sub(r'\b(WARN|WARNING)\b', r'<span class="log-warning">\1</span>', content, flags=re.IGNORECASE)
    content = re.sub(r'\b(INFO|INFORMATION)\b', r'<span class="log-info">\1</span>', content, flags=re.IGNORECASE)
    content = re.sub(r'\b(DEBUG|TRACE)\b', r'<span class="log-debug">\1</span>', content, flags=re.IGNORECASE)
    
    return f"{css}<div class='log-content'>{content}</div>"

def create_toc(content):
    """Create table of contents from markdown headers"""
    headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
    
    if not headers:
        return None
    
    toc_html = "<div class='toc'><h3>📋 Índice</h3><ul>"
    
    for level, title in headers:
        # Generate anchor ID
        anchor_id = re.sub(r'[^a-zA-Z0-9\-_]', '-', title.lower()).strip('-')
        indent = "  " * (len(level) - 1)
        
        toc_html += f"{indent}<li><a href='#{anchor_id}'>{title}</a></li>"
    
    toc_html += "</ul></div>"
    
    # Add CSS for TOC
    toc_css = """
    <style>
    .toc {
        background: #262730;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 2rem;
        border-left: 4px solid #4ECDC4;
    }
    
    .toc h3 {
        color: #4ECDC4;
        margin-top: 0;
        margin-bottom: 1rem;
    }
    
    .toc ul {
        list-style: none;
        padding-left: 0;
    }
    
    .toc li {
        margin-bottom: 0.3rem;
    }
    
    .toc a {
        color: #FAFAFA;
        text-decoration: none;
    }
    
    .toc a:hover {
        color: #FF6B6B;
        text-decoration: underline;
    }
    </style>
    """
    
    return toc_css + toc_html

def render_file_with_toc(file_path):
    """Render markdown file with table of contents"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Create TOC
        toc = create_toc(content)
        
        if toc:
            st.markdown(toc, unsafe_allow_html=True)
        
        # Render main content
        render_markdown_content(content)
        
    except Exception as e:
        st.error(f"Erro ao renderizar arquivo: {str(e)}")

def search_in_markdown(content, search_term):
    """Search for term in markdown content and highlight results"""
    if not search_term:
        return content
    
    # Highlight search terms
    highlighted = re.sub(
        f'({re.escape(search_term)})',
        r'<mark style="background: #FF6B6B; color: white; padding: 0.1rem 0.2rem; border-radius: 2px;">\1</mark>',
        content,
        flags=re.IGNORECASE
    )
    
    return highlighted

def get_markdown_stats(content):
    """Get statistics about markdown content"""
    stats = {
        'characters': len(content),
        'words': len(content.split()),
        'lines': len(content.split('\n')),
        'headers': len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
        'links': len(re.findall(r'\[.*?\]\(.*?\)', content)),
        'images': len(re.findall(r'!\[.*?\]\(.*?\)', content)),
        'code_blocks': len(re.findall(r'```', content)) // 2,
        'tables': len(re.findall(r'^\|.*?\|', content, re.MULTILINE))
    }
    
    return stats

def display_markdown_stats(stats):
    """Display markdown statistics"""
    st.subheader("📊 Estatísticas do Documento")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Caracteres", f"{stats['characters']:,}")
        st.metric("Palavras", f"{stats['words']:,}")
    
    with col2:
        st.metric("Linhas", f"{stats['lines']:,}")
        st.metric("Cabeçalhos", stats['headers'])
    
    with col3:
        st.metric("Links", stats['links'])
        st.metric("Imagens", stats['images'])
    
    with col4:
        st.metric("Blocos de Código", stats['code_blocks'])
        st.metric("Tabelas", stats['tables'])