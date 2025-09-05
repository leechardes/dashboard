import json
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

class AgentScanner:
    """Scanner for agent verification JSONs"""
    
    def __init__(self):
        self.scripts_path = Path("/srv/projects/shared/scripts/agents")
        self.config_file = Path("/srv/projects/shared/config/project-paths.json")
        self.base_paths = self._load_project_paths()
    
    def _load_project_paths(self):
        """Load project paths from configuration file"""
        paths = []
        
        # Try to load from config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Get enabled paths
                for path_config in config.get('paths', []):
                    if path_config.get('enabled', True):
                        paths.append(Path(path_config['path']))
            except Exception as e:
                print(f"Error loading config: {e}")
                # Fallback to default
                paths = [Path("/srv/projects/inoveon")]
        else:
            # Default path if no config
            paths = [Path("/srv/projects/inoveon")]
        
        return paths
    
    def scan_all_verification_jsons(self):
        """Scan all projects for verification status JSONs"""
        projects_data = []
        total_stats = {
            'total_projects': 0,
            'total_files': 0,
            'verified_files': 0,
            'pending_files': 0,
            'projects_complete': 0,
            'projects_pending': 0
        }
        
        # Find all projects with verification JSONs in all configured paths
        for base_path in self.base_paths:
            if not base_path.exists():
                continue
                
            for project_path in base_path.rglob("*/.git"):
                project_dir = project_path.parent
                json_path = project_dir / "docs/agents/.verification-status.json"
                
                if json_path.exists():
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        stats = data.get('statistics', {})
                        total_files = stats.get('total_files', 0)
                        verified_files = stats.get('verified_files', 0)
                        pending_files = stats.get('pending_files', 0)
                        
                        # Calculate completion percentage
                        completion = (verified_files / total_files * 100) if total_files > 0 else 0
                        is_complete = pending_files == 0
                        
                        projects_data.append({
                            'project_name': project_dir.name,
                            'project_path': str(project_dir),
                            'total_files': total_files,
                            'verified_files': verified_files,
                            'pending_files': pending_files,
                            'completion_percentage': round(completion, 1),
                            'is_complete': is_complete,
                            'last_scan': data.get('last_scan', 'N/A'),
                            'analysis_date': data.get('analysis_date', 'N/A')
                        })
                        
                        # Update totals
                        total_stats['total_projects'] += 1
                        total_stats['total_files'] += total_files
                        total_stats['verified_files'] += verified_files
                        total_stats['pending_files'] += pending_files
                        if is_complete:
                            total_stats['projects_complete'] += 1
                        else:
                            total_stats['projects_pending'] += 1
                            
                    except Exception as e:
                        print(f"Error reading {json_path}: {e}")
        
        return projects_data, total_stats
    
    def get_recent_activity(self, limit=10):
        """Get recently analyzed projects"""
        projects, _ = self.scan_all_verification_jsons()
        
        # Sort by last_scan date
        for project in projects:
            try:
                if project['last_scan'] != 'N/A':
                    project['scan_datetime'] = datetime.fromisoformat(
                        project['last_scan'].replace('Z', '+00:00')
                    )
                else:
                    project['scan_datetime'] = datetime.min
            except:
                project['scan_datetime'] = datetime.min
        
        # Sort and return top N
        projects.sort(key=lambda x: x['scan_datetime'], reverse=True)
        return projects[:limit]
    
    def get_projects_needing_attention(self):
        """Get projects with pending documentation"""
        projects, _ = self.scan_all_verification_jsons()
        
        # Filter projects with pending files
        pending_projects = [p for p in projects if p['pending_files'] > 0]
        
        # Sort by number of pending files (descending)
        pending_projects.sort(key=lambda x: x['pending_files'], reverse=True)
        
        return pending_projects