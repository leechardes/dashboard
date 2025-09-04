"""
Claude Process Monitor Component
Responsável por monitorar processos Claude em execução no sistema.
"""

import subprocess
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import os

# Tentar importar psutil, se não conseguir, usar mock
try:
    import psutil
except ImportError:
    print("psutil não encontrado, usando mock para demonstração")
    from . import psutil_mock as psutil

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeMonitor:
    """Monitor para processos Claude"""
    
    def __init__(self):
        self.claude_keywords = ['claude', 'anthropic', 'claude-api', 'claude-cli']
    
    def get_claude_processes(self) -> List[Dict]:
        """Retorna lista de processos Claude em execução"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 
                                           'cpu_percent', 'create_time', 'status', 'cmdline']):
                try:
                    proc_info = proc.info
                    
                    # Verificar se é um processo Claude
                    if self._is_claude_process(proc_info):
                        memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                        create_time = datetime.fromtimestamp(proc_info['create_time'])
                        runtime = datetime.now() - create_time
                        
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'username': proc_info['username'] or 'unknown',
                            'memory_mb': round(memory_mb, 2),
                            'cpu_percent': proc_info['cpu_percent'] or 0,
                            'create_time': create_time,
                            'runtime_minutes': int(runtime.total_seconds() / 60),
                            'status': proc_info['status'],
                            'cmdline': ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else '',
                            'is_orphan': self._is_orphan(proc_info),
                            'is_old': runtime > timedelta(hours=2)
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao obter processos Claude: {e}")
            return []
    
    def _is_claude_process(self, proc_info: Dict) -> bool:
        """Verifica se um processo é relacionado ao Claude"""
        try:
            name = proc_info['name'].lower()
            cmdline = ' '.join(proc_info['cmdline']).lower() if proc_info['cmdline'] else ''
            
            # Verificar nome do processo
            for keyword in self.claude_keywords:
                if keyword in name or keyword in cmdline:
                    return True
            
            # Verificar por padrões específicos na linha de comando
            claude_patterns = [
                'claude',
                'anthropic',
                '--model claude',
                'claude-api',
                'claude-cli'
            ]
            
            for pattern in claude_patterns:
                if pattern in cmdline:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_orphan(self, proc_info: Dict) -> bool:
        """Verifica se um processo é órfão"""
        try:
            proc = psutil.Process(proc_info['pid'])
            parent = proc.parent()
            
            if parent is None:
                return True
            
            # Se o pai for init (PID 1) pode ser órfão
            if parent.pid == 1:
                return True
                
            return False
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True
    
    def get_memory_stats(self) -> Dict:
        """Retorna estatísticas de uso de memória dos processos Claude"""
        try:
            processes = self.get_claude_processes()
            
            if not processes:
                return {
                    'total_processes': 0,
                    'total_memory_mb': 0,
                    'avg_memory_mb': 0,
                    'max_memory_mb': 0,
                    'active_users': 0
                }
            
            total_memory = sum(p['memory_mb'] for p in processes)
            avg_memory = total_memory / len(processes)
            max_memory = max(p['memory_mb'] for p in processes)
            active_users = len(set(p['username'] for p in processes))
            
            return {
                'total_processes': len(processes),
                'total_memory_mb': round(total_memory, 2),
                'avg_memory_mb': round(avg_memory, 2),
                'max_memory_mb': round(max_memory, 2),
                'active_users': active_users
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas de memória: {e}")
            return {}
    
    def get_user_ranking(self) -> List[Dict]:
        """Retorna ranking de usuários por consumo de recursos"""
        try:
            processes = self.get_claude_processes()
            
            user_stats = {}
            for proc in processes:
                username = proc['username']
                
                if username not in user_stats:
                    user_stats[username] = {
                        'username': username,
                        'process_count': 0,
                        'total_memory_mb': 0,
                        'avg_memory_mb': 0,
                        'max_memory_mb': 0,
                        'oldest_runtime_minutes': 0
                    }
                
                stats = user_stats[username]
                stats['process_count'] += 1
                stats['total_memory_mb'] += proc['memory_mb']
                stats['max_memory_mb'] = max(stats['max_memory_mb'], proc['memory_mb'])
                stats['oldest_runtime_minutes'] = max(stats['oldest_runtime_minutes'], 
                                                     proc['runtime_minutes'])
            
            # Calcular médias
            for username, stats in user_stats.items():
                stats['avg_memory_mb'] = round(stats['total_memory_mb'] / stats['process_count'], 2)
                stats['total_memory_mb'] = round(stats['total_memory_mb'], 2)
                stats['max_memory_mb'] = round(stats['max_memory_mb'], 2)
            
            # Ordenar por consumo total de memória
            ranking = sorted(user_stats.values(), 
                           key=lambda x: x['total_memory_mb'], reverse=True)
            
            return ranking
            
        except Exception as e:
            logger.error(f"Erro ao calcular ranking de usuários: {e}")
            return []
    
    def identify_orphans(self) -> List[Dict]:
        """Identifica processos órfãos Claude"""
        try:
            processes = self.get_claude_processes()
            orphans = [p for p in processes if p['is_orphan']]
            
            return orphans
            
        except Exception as e:
            logger.error(f"Erro ao identificar processos órfãos: {e}")
            return []
    
    def get_old_processes(self, hours: int = 2) -> List[Dict]:
        """Identifica processos antigos (rodando há mais de X horas)"""
        try:
            processes = self.get_claude_processes()
            old_processes = []
            
            for proc in processes:
                if proc['runtime_minutes'] > (hours * 60):
                    old_processes.append(proc)
            
            return old_processes
            
        except Exception as e:
            logger.error(f"Erro ao identificar processos antigos: {e}")
            return []
    
    def get_process_by_pid(self, pid: int) -> Optional[Dict]:
        """Retorna informações de um processo específico por PID"""
        try:
            processes = self.get_claude_processes()
            for proc in processes:
                if proc['pid'] == pid:
                    return proc
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter processo {pid}: {e}")
            return None
    
    def get_system_resources(self) -> Dict:
        """Retorna informações sobre recursos do sistema"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            return {
                'total_memory_gb': round(memory.total / (1024**3), 2),
                'used_memory_gb': round(memory.used / (1024**3), 2),
                'available_memory_gb': round(memory.available / (1024**3), 2),
                'memory_percent': memory.percent,
                'cpu_percent': cpu,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter recursos do sistema: {e}")
            return {}

# Instância global do monitor
claude_monitor = ClaudeMonitor()