import os
import subprocess
import glob
import datetime
from pathlib import Path

def scan_git_repositories(base_paths=None):
    """Scan for Git repositories in specified directories"""
    if base_paths is None:
        base_paths = ['/srv/projects']  # Only scan /srv/projects
    
    repositories = []
    
    for base_path in base_paths:
        base_path = os.path.expanduser(base_path)
        if not os.path.exists(base_path):
            continue
        
        try:
            # Find all .git directories
            git_dirs = []
            for root, dirs, files in os.walk(base_path):
                # Skip deep nesting and hidden directories
                depth = root.replace(base_path, '').count(os.sep)
                if depth >= 6:  # Increased to allow i9_smart repos
                    dirs[:] = []
                    continue
                
                if '.git' in dirs:
                    repo_path = root
                    git_dirs.append(repo_path)
                    # Don't recurse into the .git directory itself
                    dirs.remove('.git')
                
                # Skip common directories that shouldn't contain repositories
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d not in ['node_modules', '__pycache__', 'venv', '.env']]
            
            # Process found repositories
            for repo_path in git_dirs:
                try:
                    repo_info = get_repository_basic_info(repo_path)
                    if repo_info:
                        repositories.append(repo_info)
                except Exception:
                    continue
        
        except (PermissionError, OSError):
            continue
    
    # Sort by name
    repositories.sort(key=lambda x: x['name'].lower())
    
    return repositories

def get_repository_basic_info(repo_path):
    """Get basic information about a Git repository"""
    try:
        if not is_git_repository(repo_path):
            return None
        
        repo_info = {
            'name': os.path.basename(repo_path),
            'path': repo_path,
            'size_mb': get_directory_size(repo_path) / (1024 * 1024),
            'current_branch': get_current_branch(repo_path),
            'is_clean': is_working_directory_clean(repo_path),
            'last_commit': get_last_commit_info(repo_path)
        }
        
        return repo_info
    
    except Exception as e:
        return {
            'name': os.path.basename(repo_path),
            'path': repo_path,
            'error': str(e)
        }

def get_repo_info(repo_path):
    """Get detailed information about a Git repository"""
    try:
        if not is_git_repository(repo_path):
            return {'error': 'Not a Git repository'}
        
        info = {
            'basic': get_repository_basic_info(repo_path),
            'branches': get_branches(repo_path),
            'remotes': get_remotes(repo_path),
            'recent_commits': get_recent_commits(repo_path, limit=10),
            'contributors': get_contributors(repo_path),
            'file_stats': get_repository_file_stats(repo_path)
        }
        
        return info
    
    except Exception as e:
        return {'error': str(e)}

def get_repo_status(repo_path):
    """Get detailed status of a Git repository"""
    try:
        if not is_git_repository(repo_path):
            return {'error': 'Not a Git repository'}
        
        # Get basic info
        basic_info = get_repository_basic_info(repo_path)
        
        # Get detailed status
        status_info = {
            'is_clean': is_working_directory_clean(repo_path),
            'modified_files': get_modified_files(repo_path),
            'untracked_files': get_untracked_files(repo_path),
            'staged_files': get_staged_files(repo_path),
            'ahead_behind': get_ahead_behind_info(repo_path),
            'commit_count': get_commit_count(repo_path),
            'tag_count': get_tag_count(repo_path),
            'branches': get_branches(repo_path)
        }
        
        # Merge basic info with status
        if basic_info:
            status_info.update(basic_info)
        
        return status_info
    
    except Exception as e:
        return {'error': str(e)}

def is_git_repository(path):
    """Check if a directory is a Git repository"""
    return os.path.isdir(os.path.join(path, '.git'))

def run_git_command(repo_path, command, capture_output=True):
    """Run a Git command in the specified repository"""
    try:
        full_command = ['git'] + command
        result = subprocess.run(
            full_command,
            cwd=repo_path,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip() if result.stdout else ''
        else:
            return None
    
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        return None

def get_current_branch(repo_path):
    """Get the current branch name"""
    result = run_git_command(repo_path, ['branch', '--show-current'])
    return result if result else 'detached'

def get_branches(repo_path, include_remote=False):
    """Get list of branches"""
    command = ['branch', '-a'] if include_remote else ['branch']
    result = run_git_command(repo_path, command)
    
    if not result:
        return []
    
    branches = []
    for line in result.split('\n'):
        line = line.strip()
        if line:
            # Remove the * marker for current branch
            branch = line.replace('* ', '').strip()
            # Skip remote tracking info
            if not branch.startswith('remotes/') or include_remote:
                branches.append(branch)
    
    return branches

def get_remotes(repo_path):
    """Get remote repositories"""
    result = run_git_command(repo_path, ['remote', '-v'])
    
    if not result:
        return []
    
    remotes = []
    for line in result.split('\n'):
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                remotes.append({
                    'name': parts[0],
                    'url': parts[1],
                    'type': parts[2] if len(parts) > 2 else 'unknown'
                })
    
    return remotes

def is_working_directory_clean(repo_path):
    """Check if the working directory is clean"""
    result = run_git_command(repo_path, ['status', '--porcelain'])
    return result == '' if result is not None else False

def get_modified_files(repo_path):
    """Get list of modified files"""
    result = run_git_command(repo_path, ['diff', '--name-only'])
    return result.split('\n') if result else []

def get_untracked_files(repo_path):
    """Get list of untracked files"""
    result = run_git_command(repo_path, ['ls-files', '--others', '--exclude-standard'])
    return result.split('\n') if result else []

def get_staged_files(repo_path):
    """Get list of staged files"""
    result = run_git_command(repo_path, ['diff', '--cached', '--name-only'])
    return result.split('\n') if result else []

def get_last_commit_info(repo_path):
    """Get information about the last commit"""
    result = run_git_command(repo_path, ['log', '-1', '--pretty=format:%h|%an|%ad|%s', '--date=short'])
    
    if not result:
        return None
    
    parts = result.split('|')
    if len(parts) == 4:
        return {
            'hash': parts[0],
            'author': parts[1],
            'date': parts[2],
            'message': parts[3]
        }
    
    return None

def get_recent_commits(repo_path, limit=10):
    """Get recent commit history"""
    result = run_git_command(repo_path, ['log', f'-{limit}', '--pretty=format:%h - %s (%an, %ar)'])
    
    if not result:
        return []
    
    return result.split('\n')

def get_commit_count(repo_path):
    """Get total number of commits"""
    result = run_git_command(repo_path, ['rev-list', '--count', 'HEAD'])
    
    try:
        return int(result) if result else 0
    except ValueError:
        return 0

def get_tag_count(repo_path):
    """Get number of tags"""
    result = run_git_command(repo_path, ['tag', '--list'])
    
    if not result:
        return 0
    
    return len(result.split('\n'))

def get_contributors(repo_path):
    """Get list of contributors"""
    result = run_git_command(repo_path, ['shortlog', '-sn'])
    
    if not result:
        return []
    
    contributors = []
    for line in result.split('\n'):
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) == 2:
                contributors.append({
                    'name': parts[1],
                    'commits': int(parts[0])
                })
    
    return contributors

def get_ahead_behind_info(repo_path):
    """Get ahead/behind information relative to upstream"""
    current_branch = get_current_branch(repo_path)
    
    if current_branch == 'detached':
        return None
    
    # Try to get upstream branch
    upstream_result = run_git_command(repo_path, ['rev-parse', '--abbrev-ref', f'{current_branch}@{{upstream}}'])
    
    if not upstream_result:
        return None
    
    upstream = upstream_result
    
    # Get ahead/behind count
    result = run_git_command(repo_path, ['rev-list', '--left-right', '--count', f'{upstream}...HEAD'])
    
    if not result:
        return None
    
    parts = result.split('\t')
    if len(parts) == 2:
        try:
            return {
                'behind': int(parts[0]),
                'ahead': int(parts[1]),
                'upstream': upstream
            }
        except ValueError:
            return None
    
    return None

def get_repository_file_stats(repo_path):
    """Get file statistics for the repository"""
    try:
        # Get total files tracked by git
        result = run_git_command(repo_path, ['ls-files'])
        tracked_files = result.split('\n') if result else []
        
        # Get file type distribution
        file_types = {}
        total_size = 0
        
        for file_path in tracked_files:
            if not file_path:
                continue
            
            full_path = os.path.join(repo_path, file_path)
            
            # Get file extension
            ext = os.path.splitext(file_path)[1].lower()
            ext = ext if ext else 'no_extension'
            
            file_types[ext] = file_types.get(ext, 0) + 1
            
            # Get file size
            try:
                if os.path.exists(full_path):
                    total_size += os.path.getsize(full_path)
            except OSError:
                continue
        
        return {
            'tracked_files': len(tracked_files),
            'total_size': total_size,
            'file_types': file_types,
            'languages': detect_programming_languages(file_types)
        }
    
    except Exception:
        return {
            'tracked_files': 0,
            'total_size': 0,
            'file_types': {},
            'languages': []
        }

def detect_programming_languages(file_types):
    """Detect programming languages based on file extensions"""
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.kt': 'Kotlin',
        '.swift': 'Swift',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'Objective-C',
        '.sh': 'Shell',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.vue': 'Vue',
        '.jsx': 'JSX',
        '.tsx': 'TSX',
        '.sql': 'SQL',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.cfg': 'Config',
        '.conf': 'Config',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX'
    }
    
    detected_languages = []
    for ext, count in file_types.items():
        if ext in language_map:
            detected_languages.append({
                'language': language_map[ext],
                'files': count,
                'extension': ext
            })
    
    # Sort by file count
    detected_languages.sort(key=lambda x: x['files'], reverse=True)
    
    return detected_languages

def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    continue
    except (PermissionError, OSError):
        pass
    
    return total_size

def clone_repository(repo_url, destination_path):
    """Clone a Git repository"""
    try:
        result = subprocess.run(
            ['git', 'clone', repo_url, destination_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': 'Clone operation timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }

def pull_repository(repo_path):
    """Pull latest changes from remote repository"""
    try:
        result = run_git_command(repo_path, ['pull'])
        return {
            'success': result is not None,
            'output': result if result else 'No output'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_repository_health(repo_path):
    """Get repository health score and recommendations"""
    try:
        health_score = 100
        issues = []
        recommendations = []
        
        # Check if working directory is clean
        if not is_working_directory_clean(repo_path):
            health_score -= 10
            issues.append("Working directory has uncommitted changes")
            recommendations.append("Commit or stash your changes")
        
        # Check for untracked files
        untracked = get_untracked_files(repo_path)
        if untracked and any(untracked):
            health_score -= 5
            issues.append("Repository has untracked files")
            recommendations.append("Add important files to Git or update .gitignore")
        
        # Check for remote tracking
        remotes = get_remotes(repo_path)
        if not remotes:
            health_score -= 15
            issues.append("No remote repositories configured")
            recommendations.append("Add a remote repository for backup and collaboration")
        
        # Check commit history
        commit_count = get_commit_count(repo_path)
        if commit_count < 5:
            health_score -= 10
            issues.append("Very few commits in repository")
            recommendations.append("Make regular commits to track your progress")
        
        # Check for recent activity
        last_commit = get_last_commit_info(repo_path)
        if last_commit:
            try:
                last_commit_date = datetime.datetime.strptime(last_commit['date'], '%Y-%m-%d')
                days_since_last_commit = (datetime.datetime.now() - last_commit_date).days
                
                if days_since_last_commit > 90:
                    health_score -= 20
                    issues.append("No recent activity (>90 days)")
                    recommendations.append("Consider archiving if project is no longer active")
                elif days_since_last_commit > 30:
                    health_score -= 5
                    issues.append("No recent activity (>30 days)")
            except ValueError:
                pass
        
        # Ensure score doesn't go below 0
        health_score = max(0, health_score)
        
        return {
            'score': health_score,
            'status': get_repo_health_status(health_score),
            'issues': issues,
            'recommendations': recommendations
        }
    
    except Exception as e:
        return {
            'score': 0,
            'status': 'Error',
            'issues': [f"Error analyzing repository: {str(e)}"],
            'recommendations': ['Check repository path and permissions']
        }

def get_repo_health_status(score):
    """Get repository health status based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Fair"
    elif score >= 50:
        return "Poor"
    else:
        return "Critical"