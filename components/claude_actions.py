"""
Claude Process Actions Component
Responsável por executar ações sobre os processos Claude.
"""

import subprocess
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import signal
import time

# Tentar importar psutil, se não conseguir, usar mock
try:
    import psutil
except ImportError:
    print("psutil não encontrado, usando mock para demonstração")
    from . import psutil_mock as psutil

# Configurar logging
log_file_path = "/srv/projects/shared/dashboard/logs/claude_actions.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ClaudeActions:
    """Classe para executar ações sobre processos Claude"""
    
    def __init__(self):
        self.log_file = log_file_path
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Garante que o arquivo de log existe"""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w') as f:
                    f.write(f"{datetime.now().isoformat()} - INFO - Claude Actions Log iniciado\n")
        except Exception as e:
            print(f"Erro ao criar arquivo de log: {e}")
    
    def _log_action(self, action: str, details: str, success: bool = True):
        """Registra uma ação no log"""
        try:
            level = "SUCCESS" if success else "ERROR"
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp} - {level} - {action}: {details}"
            
            logger.info(log_entry)
            
        except Exception as e:
            print(f"Erro ao registrar ação no log: {e}")
    
    def kill_process(self, pid: int, force: bool = False) -> Tuple[bool, str]:
        """
        Mata um processo específico por PID
        
        Args:
            pid: ID do processo
            force: Se True, usa SIGKILL ao invés de SIGTERM
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            if not self._process_exists(pid):
                message = f"Processo {pid} não encontrado"
                self._log_action("KILL_PROCESS", f"PID {pid} - FALHOU: {message}", False)
                return False, message
            
            # Obter informações do processo antes de matar
            try:
                proc = psutil.Process(pid)
                proc_info = {
                    'name': proc.name(),
                    'username': proc.username(),
                    'memory_mb': round(proc.memory_info().rss / (1024 * 1024), 2)
                }
            except:
                proc_info = {'name': 'unknown', 'username': 'unknown', 'memory_mb': 0}
            
            # Tentar matar o processo
            signal_type = signal.SIGKILL if force else signal.SIGTERM
            signal_name = "SIGKILL" if force else "SIGTERM"
            
            try:
                # Usando psutil para maior controle
                process = psutil.Process(pid)
                process.send_signal(signal_type)
                
                # Aguardar um pouco para verificar se o processo morreu
                time.sleep(0.5)
                
                if not self._process_exists(pid):
                    message = f"Processo {pid} ({proc_info['name']}) morto com {signal_name}"
                    self._log_action("KILL_PROCESS", 
                                   f"PID {pid} - User: {proc_info['username']} - "
                                   f"Memory: {proc_info['memory_mb']}MB - Signal: {signal_name}", True)
                    return True, message
                else:
                    # Se SIGTERM não funcionou, tentar SIGKILL
                    if not force:
                        return self.kill_process(pid, force=True)
                    else:
                        message = f"Falha ao matar processo {pid} mesmo com SIGKILL"
                        self._log_action("KILL_PROCESS", f"PID {pid} - FALHOU: {message}", False)
                        return False, message
                        
            except PermissionError:
                # Tentar com sudo
                return self._kill_with_sudo(pid, force, proc_info)
                
        except Exception as e:
            message = f"Erro ao matar processo {pid}: {str(e)}"
            self._log_action("KILL_PROCESS", f"PID {pid} - ERRO: {message}", False)
            return False, message
    
    def _kill_with_sudo(self, pid: int, force: bool, proc_info: Dict) -> Tuple[bool, str]:
        """Mata processo usando sudo"""
        try:
            signal_arg = "-9" if force else "-15"
            signal_name = "SIGKILL" if force else "SIGTERM"
            
            result = subprocess.run(
                ['sudo', 'kill', signal_arg, str(pid)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            time.sleep(0.5)
            
            if result.returncode == 0 and not self._process_exists(pid):
                message = f"Processo {pid} ({proc_info['name']}) morto com sudo {signal_name}"
                self._log_action("KILL_PROCESS_SUDO", 
                               f"PID {pid} - User: {proc_info['username']} - "
                               f"Memory: {proc_info['memory_mb']}MB - Signal: {signal_name}", True)
                return True, message
            else:
                message = f"Falha ao matar processo {pid} com sudo: {result.stderr}"
                self._log_action("KILL_PROCESS_SUDO", f"PID {pid} - FALHOU: {message}", False)
                return False, message
                
        except subprocess.TimeoutExpired:
            message = f"Timeout ao matar processo {pid} com sudo"
            self._log_action("KILL_PROCESS_SUDO", f"PID {pid} - TIMEOUT: {message}", False)
            return False, message
        except Exception as e:
            message = f"Erro ao matar processo {pid} com sudo: {str(e)}"
            self._log_action("KILL_PROCESS_SUDO", f"PID {pid} - ERRO: {message}", False)
            return False, message
    
    def kill_user_processes(self, username: str) -> Tuple[bool, str, List[int]]:
        """
        Mata todos os processos Claude de um usuário específico
        
        Args:
            username: Nome do usuário
            
        Returns:
            Tuple[bool, str, List[int]]: (sucesso_geral, mensagem, lista_pids_mortos)
        """
        try:
            from .claude_monitor import claude_monitor
            
            processes = claude_monitor.get_claude_processes()
            user_processes = [p for p in processes if p['username'] == username]
            
            if not user_processes:
                message = f"Nenhum processo Claude encontrado para o usuário {username}"
                self._log_action("KILL_USER_PROCESSES", f"User: {username} - Nenhum processo encontrado", True)
                return True, message, []
            
            killed_pids = []
            failed_pids = []
            
            for proc in user_processes:
                success, _ = self.kill_process(proc['pid'])
                if success:
                    killed_pids.append(proc['pid'])
                else:
                    failed_pids.append(proc['pid'])
            
            total = len(user_processes)
            killed = len(killed_pids)
            
            if failed_pids:
                message = f"Mortos {killed}/{total} processos do usuário {username}. Falhas: {failed_pids}"
                self._log_action("KILL_USER_PROCESSES", 
                               f"User: {username} - Sucesso: {killed_pids} - Falhas: {failed_pids}", False)
                return False, message, killed_pids
            else:
                message = f"Todos os {killed} processos do usuário {username} foram mortos"
                self._log_action("KILL_USER_PROCESSES", 
                               f"User: {username} - Mortos: {killed_pids}", True)
                return True, message, killed_pids
                
        except Exception as e:
            message = f"Erro ao matar processos do usuário {username}: {str(e)}"
            self._log_action("KILL_USER_PROCESSES", f"User: {username} - ERRO: {message}", False)
            return False, message, []
    
    def kill_all_processes(self) -> Tuple[bool, str, List[int]]:
        """
        Mata todos os processos Claude do sistema
        
        Returns:
            Tuple[bool, str, List[int]]: (sucesso_geral, mensagem, lista_pids_mortos)
        """
        try:
            from .claude_monitor import claude_monitor
            
            processes = claude_monitor.get_claude_processes()
            
            if not processes:
                message = "Nenhum processo Claude encontrado no sistema"
                self._log_action("KILL_ALL_PROCESSES", "Nenhum processo encontrado", True)
                return True, message, []
            
            killed_pids = []
            failed_pids = []
            
            for proc in processes:
                success, _ = self.kill_process(proc['pid'])
                if success:
                    killed_pids.append(proc['pid'])
                else:
                    failed_pids.append(proc['pid'])
            
            total = len(processes)
            killed = len(killed_pids)
            
            if failed_pids:
                message = f"Mortos {killed}/{total} processos Claude. Falhas: {failed_pids}"
                self._log_action("KILL_ALL_PROCESSES", 
                               f"Total: {total} - Sucesso: {killed_pids} - Falhas: {failed_pids}", False)
                return False, message, killed_pids
            else:
                message = f"Todos os {killed} processos Claude foram mortos"
                self._log_action("KILL_ALL_PROCESSES", 
                               f"Todos mortos: {killed_pids}", True)
                return True, message, killed_pids
                
        except Exception as e:
            message = f"Erro ao matar todos os processos: {str(e)}"
            self._log_action("KILL_ALL_PROCESSES", f"ERRO: {message}", False)
            return False, message, []
    
    def clean_old_processes(self, hours: int = 2) -> Tuple[bool, str, List[int]]:
        """
        Mata processos Claude antigos (rodando há mais de X horas)
        
        Args:
            hours: Número de horas limite
            
        Returns:
            Tuple[bool, str, List[int]]: (sucesso_geral, mensagem, lista_pids_mortos)
        """
        try:
            from .claude_monitor import claude_monitor
            
            old_processes = claude_monitor.get_old_processes(hours)
            
            if not old_processes:
                message = f"Nenhum processo Claude antigo (>{hours}h) encontrado"
                self._log_action("CLEAN_OLD_PROCESSES", f"Limite: {hours}h - Nenhum processo antigo", True)
                return True, message, []
            
            killed_pids = []
            failed_pids = []
            
            for proc in old_processes:
                success, _ = self.kill_process(proc['pid'])
                if success:
                    killed_pids.append(proc['pid'])
                else:
                    failed_pids.append(proc['pid'])
            
            total = len(old_processes)
            killed = len(killed_pids)
            
            if failed_pids:
                message = f"Limpos {killed}/{total} processos antigos (>{hours}h). Falhas: {failed_pids}"
                self._log_action("CLEAN_OLD_PROCESSES", 
                               f"Limite: {hours}h - Sucesso: {killed_pids} - Falhas: {failed_pids}", False)
                return False, message, killed_pids
            else:
                message = f"Todos os {killed} processos antigos (>{hours}h) foram limpos"
                self._log_action("CLEAN_OLD_PROCESSES", 
                               f"Limite: {hours}h - Limpos: {killed_pids}", True)
                return True, message, killed_pids
                
        except Exception as e:
            message = f"Erro ao limpar processos antigos: {str(e)}"
            self._log_action("CLEAN_OLD_PROCESSES", f"Limite: {hours}h - ERRO: {message}", False)
            return False, message, []
    
    def clean_orphan_processes(self) -> Tuple[bool, str, List[int]]:
        """
        Mata processos Claude órfãos
        
        Returns:
            Tuple[bool, str, List[int]]: (sucesso_geral, mensagem, lista_pids_mortos)
        """
        try:
            from .claude_monitor import claude_monitor
            
            orphan_processes = claude_monitor.identify_orphans()
            
            if not orphan_processes:
                message = "Nenhum processo Claude órfão encontrado"
                self._log_action("CLEAN_ORPHAN_PROCESSES", "Nenhum processo órfão", True)
                return True, message, []
            
            killed_pids = []
            failed_pids = []
            
            for proc in orphan_processes:
                success, _ = self.kill_process(proc['pid'])
                if success:
                    killed_pids.append(proc['pid'])
                else:
                    failed_pids.append(proc['pid'])
            
            total = len(orphan_processes)
            killed = len(killed_pids)
            
            if failed_pids:
                message = f"Limpos {killed}/{total} processos órfãos. Falhas: {failed_pids}"
                self._log_action("CLEAN_ORPHAN_PROCESSES", 
                               f"Sucesso: {killed_pids} - Falhas: {failed_pids}", False)
                return False, message, killed_pids
            else:
                message = f"Todos os {killed} processos órfãos foram limpos"
                self._log_action("CLEAN_ORPHAN_PROCESSES", 
                               f"Limpos: {killed_pids}", True)
                return True, message, killed_pids
                
        except Exception as e:
            message = f"Erro ao limpar processos órfãos: {str(e)}"
            self._log_action("CLEAN_ORPHAN_PROCESSES", f"ERRO: {message}", False)
            return False, message, []
    
    def _process_exists(self, pid: int) -> bool:
        """Verifica se um processo existe"""
        try:
            return psutil.pid_exists(pid)
        except:
            return False
    
    def get_action_logs(self, limit: int = 100) -> List[str]:
        """
        Retorna as últimas linhas do log de ações
        
        Args:
            limit: Número máximo de linhas para retornar
            
        Returns:
            List[str]: Lista das linhas do log
        """
        try:
            if not os.path.exists(self.log_file):
                return []
            
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Retornar as últimas N linhas
            return [line.strip() for line in lines[-limit:]]
            
        except Exception as e:
            logger.error(f"Erro ao ler logs: {e}")
            return [f"Erro ao ler logs: {str(e)}"]
    
    def clear_old_logs(self, days: int = 7) -> Tuple[bool, str]:
        """
        Remove logs antigos (mais de X dias)
        
        Args:
            days: Número de dias para manter
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            if not os.path.exists(self.log_file):
                return True, "Arquivo de log não existe"
            
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            removed_count = 0
            
            for line in lines:
                try:
                    # Extrair timestamp da linha
                    timestamp_str = line.split(' - ')[0]
                    log_date = datetime.fromisoformat(timestamp_str)
                    
                    if log_date >= cutoff_date:
                        new_lines.append(line)
                    else:
                        removed_count += 1
                except:
                    # Se não conseguir parsear a data, manter a linha
                    new_lines.append(line)
            
            # Reescrever arquivo com logs filtrados
            with open(self.log_file, 'w') as f:
                f.writelines(new_lines)
            
            message = f"Removidos {removed_count} logs antigos (>{days} dias)"
            self._log_action("CLEAR_OLD_LOGS", f"Removidos: {removed_count} - Limite: {days} dias", True)
            
            return True, message
            
        except Exception as e:
            message = f"Erro ao limpar logs antigos: {str(e)}"
            self._log_action("CLEAR_OLD_LOGS", f"ERRO: {message}", False)
            return False, message

# Instância global das ações
claude_actions = ClaudeActions()