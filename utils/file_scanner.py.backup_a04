import os
import glob
import datetime
from pathlib import Path
from collections import defaultdict

def scan_markdown_files(base_paths=None):
    """Scan for markdown files in specified directories with improved depth"""
    if base_paths is None:
        base_paths = ['/srv/projects']  # Only scan /srv/projects
    
    markdown_files = []
    markdown_extensions = ['.md', '.markdown', '.mdown', '.mkd', '.rst', '.txt']
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
        
        try:
            # Walk through all directories
            for root, dirs, files in os.walk(base_path):
                # Skip hidden directories and common non-doc directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d not in ['node_modules', '__pycache__', 'venv', '.env', 
                                   'dist', 'build', 'target', '.git']]
                
                # Check depth - allow up to 8 levels for i9_smart structure
                depth = root.replace(base_path, '').count(os.sep)
                if depth >= 8:
                    dirs[:] = []  # Don't go deeper
                    continue
                
                for file in files:
                    # Check if file has documentation extension
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in markdown_extensions:
                        file_path = os.path.join(root, file)
                        info = get_file_info(file_path)
                        if info:
                            # Add project and category info
                            info = enrich_file_info(info, base_path)
                            markdown_files.append(info)
        
        except (PermissionError, OSError) as e:
            print(f"Error scanning {base_path}: {e}")
            continue
    
    # Remove duplicates
    seen_paths = set()
    unique_files = []
    for file_info in markdown_files:
        if file_info['path'] not in seen_paths:
            seen_paths.add(file_info['path'])
            unique_files.append(file_info)
    
    # Sort by modification time (newest first)
    unique_files.sort(key=lambda x: x['modified_timestamp'], reverse=True)
    
    return unique_files

def enrich_file_info(info, base_path):
    """Add project and category information to file info"""
    path = info['path']
    relative_path = os.path.relpath(path, base_path)
    path_parts = relative_path.split(os.sep)
    
    # Determine project
    project = 'shared'
    category = 'general'
    
    # Analyze path structure
    if 'inoveon' in path_parts:
        idx = path_parts.index('inoveon')
        if idx + 1 < len(path_parts):
            project = path_parts[idx + 1]  # e.g., 'i9_smart', 'asfrete', 'devflow'
            
            # Determine category
            if idx + 2 < len(path_parts):
                sub_cat = path_parts[idx + 2]
                if sub_cat in ['apis', 'web', 'mobile', 'desktop', 'services']:
                    category = sub_cat
                elif 'doc' in sub_cat.lower():
                    category = 'documentation'
    elif 'shared' in path_parts:
        project = 'shared'
        # Check for specific shared categories
        if 'docs' in path_parts:
            category = 'documentation'
        elif 'scripts' in path_parts:
            category = 'scripts'
        elif 'streamlit-dashboard' in path_parts:
            category = 'dashboard'
    elif 'experimental' in path_parts:
        project = 'experimental'
        category = 'experimental'
    
    # Determine document type based on filename
    doc_type = determine_doc_type(info['name'])
    
    info['project'] = project
    info['category'] = category
    info['doc_type'] = doc_type
    info['relative_path'] = relative_path
    
    return info

def determine_doc_type(filename):
    """Determine document type based on filename patterns"""
    name_lower = filename.lower()
    
    # Common documentation patterns
    if 'readme' in name_lower:
        return 'README'
    elif 'license' in name_lower:
        return 'License'
    elif 'changelog' in name_lower or 'history' in name_lower:
        return 'Changelog'
    elif 'todo' in name_lower:
        return 'TODO'
    elif 'contributing' in name_lower:
        return 'Contributing'
    elif 'install' in name_lower or 'setup' in name_lower:
        return 'Installation'
    elif 'config' in name_lower or 'settings' in name_lower:
        return 'Configuration'
    elif 'api' in name_lower:
        return 'API'
    elif 'guide' in name_lower or 'tutorial' in name_lower:
        return 'Guide'
    elif 'faq' in name_lower:
        return 'FAQ'
    elif 'security' in name_lower:
        return 'Security'
    elif 'docker' in name_lower:
        return 'Docker'
    elif 'test' in name_lower:
        return 'Testing'
    elif '.env' in name_lower:
        return 'Environment'
    else:
        return 'Documentation'

def scan_log_files(base_paths=None):
    """Scan for log files in common directories"""
    if base_paths is None:
        base_paths = [
            '/srv/projects',  # Primary focus on projects
            '/var/log'        # System logs if needed
        ]
    
    log_files = []
    log_patterns = ['*.log', '*.out', '*.err', '*.txt']
    
    for base_path in base_paths:
        # Expand user path
        base_path = os.path.expanduser(base_path)
        
        if not os.path.exists(base_path):
            continue
        
        try:
            # Search recursively but with depth limit
            for root, dirs, files in os.walk(base_path):
                # Limit depth to avoid too deep recursion
                depth = root.replace(base_path, '').count(os.sep)
                if depth >= 3:
                    dirs[:] = []  # Don't recurse deeper
                    continue
                
                # Skip certain directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check if it matches log patterns or has log-like content
                    if (any(file.endswith(ext[1:]) for ext in log_patterns) or
                        'log' in file.lower() or
                        file.endswith('.access') or
                        file.endswith('.error')):
                        
                        try:
                            info = get_file_info(file_path)
                            if info and is_likely_log_file(file_path):
                                info['source'] = determine_log_source(file_path)
                                log_files.append(info)
                        except (PermissionError, OSError):
                            continue
        
        except (PermissionError, OSError):
            continue
    
    # Remove duplicates and sort
    seen_paths = set()
    unique_files = []
    for file_info in log_files:
        if file_info['path'] not in seen_paths:
            seen_paths.add(file_info['path'])
            unique_files.append(file_info)
    
    # Sort by modification time (newest first)
    unique_files.sort(key=lambda x: x['modified_timestamp'], reverse=True)
    
    return unique_files

def get_file_info(file_path):
    """Get detailed information about a file"""
    try:
        stat = os.stat(file_path)
        
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': stat.st_size,
            'size_kb': stat.st_size / 1024,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'modified_timestamp': stat.st_mtime,
            'type': get_file_type(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'directory': os.path.dirname(file_path)
        }
    
    except (OSError, PermissionError):
        return None

def get_file_type(file_path):
    """Determine file type based on extension and content"""
    name = os.path.basename(file_path).lower()
    ext = os.path.splitext(file_path)[1].lower()
    
    # Documentation files
    if ext in ['.md', '.markdown', '.mdown', '.mkd']:
        return 'Markdown'
    elif ext in ['.rst']:
        return 'reStructuredText'
    elif ext in ['.txt']:
        if any(keyword in name for keyword in ['readme', 'license', 'changelog', 'todo']):
            return 'Documentation'
        return 'Text'
    
    # Log files
    elif ext in ['.log']:
        return 'Log'
    elif ext in ['.out', '.err']:
        return 'Output Log'
    
    # Other types
    elif ext in ['.json']:
        return 'JSON'
    elif ext in ['.yaml', '.yml']:
        return 'YAML'
    elif ext in ['.xml']:
        return 'XML'
    elif ext in ['.csv']:
        return 'CSV'
    
    return 'Other'

def is_likely_log_file(file_path):
    """Check if a file is likely a log file based on content sample"""
    try:
        # Read first few lines to check for log patterns
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(1024)  # Read first 1KB
        
        # Check for common log patterns
        log_indicators = [
            # Timestamp patterns
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}:\d{2}:\d{2}',  # HH:MM:SS
            
            # Log levels
            r'\b(DEBUG|INFO|WARN|ERROR|FATAL|TRACE)\b',
            
            # Common log formats
            r'\[.*\]',  # Bracketed content
            r'^\d+\.\d+\.\d+\.\d+',  # IP addresses
        ]
        
        import re
        for pattern in log_indicators:
            if re.search(pattern, sample, re.IGNORECASE | re.MULTILINE):
                return True
        
        # Check file size (log files are usually not tiny)
        stat = os.stat(file_path)
        if stat.st_size < 50:  # Skip very small files
            return False
        
        return False
    
    except (OSError, UnicodeDecodeError):
        return False

def determine_log_source(file_path):
    """Determine the source/type of log file"""
    path_lower = file_path.lower()
    name_lower = os.path.basename(file_path).lower()
    
    # System logs
    if '/var/log' in path_lower:
        if 'syslog' in name_lower:
            return 'System'
        elif 'auth' in name_lower:
            return 'Authentication'
        elif 'kern' in name_lower:
            return 'Kernel'
        elif 'mail' in name_lower:
            return 'Mail'
        elif 'cron' in name_lower:
            return 'Cron'
        elif 'apache' in name_lower or 'httpd' in name_lower:
            return 'Apache'
        elif 'nginx' in name_lower:
            return 'Nginx'
        elif 'mysql' in name_lower or 'mariadb' in name_lower:
            return 'Database'
        else:
            return 'System'
    
    # Application logs
    elif '/srv/projects' in path_lower:
        if 'flask' in path_lower or 'django' in path_lower:
            return 'Web App'
        elif 'celery' in path_lower:
            return 'Task Queue'
        elif 'gunicorn' in path_lower or 'uwsgi' in path_lower:
            return 'WSGI Server'
        else:
            return 'Application'
    
    # User logs
    elif '/home' in path_lower or '~' in path_lower:
        return 'User Application'
    
    # Temporary logs
    elif '/tmp' in path_lower:
        return 'Temporary'
    
    # Docker logs
    elif 'docker' in path_lower:
        return 'Docker'
    
    # Default
    else:
        return 'Unknown'

def scan_directory_tree(path, max_depth=3, include_files=True):
    """Scan directory tree and return structure"""
    def scan_recursive(current_path, current_depth=0):
        if current_depth > max_depth:
            return []
        
        items = []
        try:
            for item in sorted(os.listdir(current_path)):
                if item.startswith('.'):
                    continue
                
                item_path = os.path.join(current_path, item)
                
                if os.path.isdir(item_path):
                    dir_info = {
                        'name': item,
                        'path': item_path,
                        'type': 'directory',
                        'depth': current_depth,
                        'children': scan_recursive(item_path, current_depth + 1)
                    }
                    items.append(dir_info)
                
                elif include_files and os.path.isfile(item_path):
                    file_info = get_file_info(item_path)
                    if file_info:
                        file_info['depth'] = current_depth
                        items.append(file_info)
        
        except (PermissionError, OSError):
            pass
        
        return items
    
    return scan_recursive(path)

def search_files_content(search_term, file_paths, max_results=100):
    """Search for content within files"""
    results = []
    
    for file_path in file_paths[:max_results]:  # Limit to avoid performance issues
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Search in lines
            for line_num, line in enumerate(lines, 1):
                if search_term.lower() in line.lower():
                    results.append({
                        'file': file_path,
                        'line_number': line_num,
                        'line_content': line.strip(),
                        'context': get_line_context(lines, line_num, context_size=2)
                    })
                    
                    # Limit matches per file
                    if len([r for r in results if r['file'] == file_path]) >= 10:
                        break
        
        except (OSError, UnicodeDecodeError):
            continue
    
    return results

def get_line_context(lines, line_num, context_size=2):
    """Get context lines around a specific line"""
    start = max(0, line_num - context_size - 1)
    end = min(len(lines), line_num + context_size)
    
    context_lines = []
    for i in range(start, end):
        prefix = ">>> " if i == line_num - 1 else "    "
        context_lines.append(f"{prefix}{i+1}: {lines[i].strip()}")
    
    return "\n".join(context_lines)

def get_directory_stats(path):
    """Get statistics about a directory"""
    stats = {
        'total_files': 0,
        'total_dirs': 0,
        'total_size': 0,
        'file_types': {},
        'largest_files': [],
        'recent_files': []
    }
    
    try:
        for root, dirs, files in os.walk(path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            stats['total_dirs'] += len(dirs)
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    file_mtime = file_stat.st_mtime
                    
                    stats['total_files'] += 1
                    stats['total_size'] += file_size
                    
                    # File type distribution
                    ext = os.path.splitext(file)[1].lower()
                    ext = ext if ext else 'no_extension'
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                    
                    # Track largest files
                    stats['largest_files'].append({
                        'path': file_path,
                        'size': file_size,
                        'name': file
                    })
                    
                    # Track recent files
                    stats['recent_files'].append({
                        'path': file_path,
                        'mtime': file_mtime,
                        'name': file
                    })
                
                except (OSError, PermissionError):
                    continue
    
    except (OSError, PermissionError):
        return stats
    
    # Sort and limit results
    stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]
    
    stats['recent_files'].sort(key=lambda x: x['mtime'], reverse=True)
    stats['recent_files'] = stats['recent_files'][:10]
    
    return stats

def categorize_documents(docs):
    """Categorize documents by project and type"""
    categories = defaultdict(lambda: defaultdict(list))
    
    for doc in docs:
        project = doc.get('project', 'unknown')
        category = doc.get('category', 'general')
        doc_type = doc.get('doc_type', 'Documentation')
        
        # Create hierarchical structure
        categories[project][category].append(doc)
    
    return dict(categories)

def build_document_tree(docs):
    """Build a hierarchical tree structure from documents"""
    tree = {}
    
    for doc in docs:
        path_parts = doc['path'].split('/')
        current = tree
        
        # Build the tree structure
        for i, part in enumerate(path_parts[:-1]):  # All parts except the file
            if part not in current:
                current[part] = {
                    '_type': 'folder',
                    '_name': part,
                    '_path': '/'.join(path_parts[:i+1]),
                    '_children': {}
                }
            current = current[part]['_children']
        
        # Add the file
        file_name = path_parts[-1]
        current[file_name] = {
            '_type': 'file',
            '_name': file_name,
            '_path': doc['path'],
            '_doc': doc
        }
    
    return tree

def get_document_statistics(docs):
    """Get statistics about documents"""
    stats = {
        'total': len(docs),
        'by_project': defaultdict(int),
        'by_category': defaultdict(int),
        'by_type': defaultdict(int),
        'by_extension': defaultdict(int),
        'total_size_mb': sum(doc.get('size_mb', 0) for doc in docs),
        'recent': sorted(docs, key=lambda x: x['modified_timestamp'], reverse=True)[:5]
    }
    
    for doc in docs:
        stats['by_project'][doc.get('project', 'unknown')] += 1
        stats['by_category'][doc.get('category', 'general')] += 1
        stats['by_type'][doc.get('doc_type', 'Documentation')] += 1
        stats['by_extension'][doc.get('extension', '.txt')] += 1
    
    return stats