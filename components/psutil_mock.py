"""
Mock do psutil para testes quando o psutil não está disponível
"""

import subprocess
import os
from datetime import datetime
import time

class MockProcess:
    def __init__(self, pid):
        self.pid = pid
        self._name = f"claude_process_{pid}"
        self._username = "testuser"
        self._memory_mb = 512 + (pid % 1000)
        self._cpu_percent = pid % 100
        self._create_time = time.time() - (pid % 7200)  # Até 2h atrás
        
    def name(self):
        return self._name
        
    def username(self):
        return self._username
        
    def memory_info(self):
        class MemInfo:
            def __init__(self, rss):
                self.rss = rss
        return MemInfo(self._memory_mb * 1024 * 1024)
    
    def cpu_percent(self):
        return self._cpu_percent
        
    def create_time(self):
        return self._create_time
        
    def status(self):
        return "running"
        
    def cmdline(self):
        return ["claude-cli", "--model", "claude-3-sonnet"]
    
    def parent(self):
        if self.pid == 1001:  # Simular órfão
            return None
        return MockProcess(1)  # Parent é init
    
    def send_signal(self, signal):
        pass

class MockVirtualMemory:
    def __init__(self):
        self.total = 16 * 1024 * 1024 * 1024  # 16GB
        self.used = 8 * 1024 * 1024 * 1024    # 8GB
        self.available = 8 * 1024 * 1024 * 1024  # 8GB
        self.percent = 50

def process_iter(attrs):
    """Mock process_iter que simula processos Claude"""
    # Simular alguns processos Claude
    claude_pids = [1001, 1002, 1003, 2001, 2002]
    
    for pid in claude_pids:
        try:
            proc = MockProcess(pid)
            proc_info = {}
            
            for attr in attrs:
                if attr == 'pid':
                    proc_info['pid'] = proc.pid
                elif attr == 'name':
                    proc_info['name'] = proc.name()
                elif attr == 'username':
                    proc_info['username'] = proc.username()
                elif attr == 'memory_info':
                    proc_info['memory_info'] = proc.memory_info()
                elif attr == 'cpu_percent':
                    proc_info['cpu_percent'] = proc.cpu_percent()
                elif attr == 'create_time':
                    proc_info['create_time'] = proc.create_time()
                elif attr == 'status':
                    proc_info['status'] = proc.status()
                elif attr == 'cmdline':
                    proc_info['cmdline'] = proc.cmdline()
            
            proc.info = proc_info
            yield proc
            
        except:
            continue

def Process(pid):
    return MockProcess(pid)

def pid_exists(pid):
    return pid in [1001, 1002, 1003, 2001, 2002]

def virtual_memory():
    return MockVirtualMemory()

def cpu_percent(interval=None):
    return 25.5

# Constantes de sinais
SIGTERM = 15
SIGKILL = 9

# Exceções
class NoSuchProcess(Exception):
    pass

class AccessDenied(Exception):
    pass
    
class ZombieProcess(Exception):
    pass