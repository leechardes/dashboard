"""System Users Component - Get and manage system users"""

import subprocess
import pwd
import grp
import os
from typing import List, Dict, Optional

def get_system_users(min_uid: int = 1000, max_uid: int = 65534) -> List[Dict]:
    """
    Get list of system users (excluding system accounts)
    
    Args:
        min_uid: Minimum UID to consider (default 1000 for regular users)
        max_uid: Maximum UID to consider
        
    Returns:
        List of user dictionaries with info
    """
    users = []
    
    try:
        # Get all users from /etc/passwd
        for user in pwd.getpwall():
            # Filter by UID range (typically 1000-65534 for regular users)
            if min_uid <= user.pw_uid <= max_uid:
                # Check if user has a valid shell (not /bin/false or /usr/sbin/nologin)
                valid_shells = ['/bin/bash', '/bin/sh', '/bin/zsh', '/usr/bin/zsh', '/usr/bin/bash']
                has_valid_shell = any(shell in user.pw_shell for shell in valid_shells)
                
                # Get user's groups
                groups = []
                try:
                    groups = [g.gr_name for g in grp.getgrall() if user.pw_name in g.gr_mem]
                    primary_group = grp.getgrgid(user.pw_gid).gr_name
                    if primary_group not in groups:
                        groups.insert(0, primary_group)
                except:
                    pass
                
                # Check if user has Claude processes
                has_claude = check_user_has_claude(user.pw_name)
                
                users.append({
                    'username': user.pw_name,
                    'uid': user.pw_uid,
                    'gid': user.pw_gid,
                    'full_name': user.pw_gecos.split(',')[0] if user.pw_gecos else '',
                    'home_dir': user.pw_dir,
                    'shell': user.pw_shell,
                    'has_valid_shell': has_valid_shell,
                    'groups': groups,
                    'is_developer': 'developers' in groups or 'developer' in groups,
                    'has_claude_processes': has_claude
                })
                
    except Exception as e:
        print(f"Error getting system users: {e}")
        
    # Sort by username
    users.sort(key=lambda x: x['username'])
    
    return users

def check_user_has_claude(username: str) -> bool:
    """Check if user has any Claude processes running"""
    try:
        result = subprocess.run(
            f"ps aux | grep '^{username}' | grep -i claude | grep -v grep",
            shell=True,
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) > 0
    except:
        return False

def get_developers_group_users() -> List[str]:
    """Get list of users in the developers group"""
    try:
        developers_group = grp.getgrnam('developers')
        return developers_group.gr_mem
    except:
        return []

def get_user_info(username: str) -> Optional[Dict]:
    """Get detailed info about a specific user"""
    try:
        user = pwd.getpwnam(username)
        
        # Get groups
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        primary_group = grp.getgrgid(user.pw_gid).gr_name
        if primary_group not in groups:
            groups.insert(0, primary_group)
            
        # Check Claude processes
        claude_processes = []
        try:
            result = subprocess.run(
                f"ps aux | grep '^{username}' | grep -i claude | grep -v grep",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 11:
                        claude_processes.append({
                            'pid': parts[1],
                            'cpu': parts[2],
                            'mem': parts[3],
                            'vsz': parts[4],
                            'rss': parts[5],
                            'time': parts[9],
                            'command': ' '.join(parts[10:])
                        })
        except:
            pass
            
        return {
            'username': user.pw_name,
            'uid': user.pw_uid,
            'gid': user.pw_gid,
            'full_name': user.pw_gecos.split(',')[0] if user.pw_gecos else '',
            'home_dir': user.pw_dir,
            'shell': user.pw_shell,
            'groups': groups,
            'is_developer': 'developers' in groups or 'developer' in groups,
            'claude_processes': claude_processes,
            'has_claude': len(claude_processes) > 0
        }
        
    except KeyError:
        return None
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

def is_user_admin(username: str) -> bool:
    """Check if user has admin privileges (sudo/root)"""
    try:
        # Check if user is root
        if username == 'root':
            return True
            
        # Check if user is in sudo or wheel group
        user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        return 'sudo' in user_groups or 'wheel' in user_groups or 'admin' in user_groups
        
    except:
        return False