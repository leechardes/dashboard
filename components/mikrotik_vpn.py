import paramiko
import json
import secrets
import string
import ipaddress
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

class MikroTikVPN:
    """Classe para gerenciamento de usuários VPN no MikroTik via SSH"""
    
    def __init__(self):
        self.host = "10.0.10.1"
        self.user = "admin"
        self.password = "cwTS6FbVs7GNxBRXAigfgaGLWILMdEfv"
        self.port = 22
        self.timeout = 30
        
        # Configuração de IPs VPN
        self.IP_RANGES = {
            "matriz": {
                "network": "10.0.11.0/24",
                "gateway": "10.0.11.1",
                "start": 10,
                "end": 99,
                "fixed": {
                    "mikrotik_escritorio": "10.0.11.2",
                    "lee": "10.0.11.10",
                    "diego": "10.0.11.11",
                    "admin": "10.0.11.5",
                    "backup": "10.0.11.6"
                }
            },
            "escritorio": {
                "network": "10.0.21.0/24", 
                "gateway": "10.0.21.1",
                "start": 10,
                "end": 99,
                "fixed": {}
            }
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _execute_command(self, command: str) -> Tuple[str, str, int]:
        """Executa comando SSH no MikroTik e retorna output, error e exit_code"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                port=self.port,
                timeout=self.timeout
            )
            
            stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
            
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            exit_code = stdout.channel.recv_exit_status()
            
            ssh.close()
            
            self.logger.info(f"Comando executado: {command}")
            self.logger.debug(f"Output: {output}")
            
            return output, error, exit_code
            
        except Exception as e:
            self.logger.error(f"Erro na conexão SSH: {str(e)}")
            return "", str(e), 1
    
    def _backup_config(self) -> bool:
        """Cria backup da configuração antes de alterações"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"vpn_backup_{timestamp}"
            
            command = f"/system backup save name={backup_name}"
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                self.logger.info(f"Backup criado: {backup_name}")
                return True
            else:
                self.logger.error(f"Erro ao criar backup: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {str(e)}")
            return False
    
    def generate_secure_password(self, length: int = 12) -> str:
        """Gera senha segura aleatória"""
        characters = string.ascii_letters + string.digits + "!@#$%&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    
    def get_next_available_ip(self, site: str = "matriz") -> Optional[str]:
        """Retorna próximo IP disponível para o site especificado"""
        if site not in self.IP_RANGES:
            return None
            
        config = self.IP_RANGES[site]
        network = ipaddress.IPv4Network(config["network"])
        base_ip = str(network.network_address)
        base_parts = base_ip.split('.')
        
        # Lista usuários existentes para verificar IPs em uso
        users = self.list_users()
        used_ips = set()
        
        for user in users:
            if user.get("remote_address"):
                used_ips.add(user["remote_address"])
        
        # Adicionar IPs fixos à lista de usados
        for fixed_ip in config["fixed"].values():
            used_ips.add(fixed_ip)
        
        # Procurar próximo IP disponível
        for i in range(config["start"], config["end"] + 1):
            candidate_ip = f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.{i}"
            if candidate_ip not in used_ips:
                return candidate_ip
        
        return None
    
    def add_user(self, username: str, password: Optional[str] = None, 
                 ip_address: Optional[str] = None, site: str = "matriz") -> Dict[str, any]:
        """Adiciona novo usuário VPN"""
        try:
            # Validar entrada
            if not username or not username.strip():
                return {"success": False, "message": "Nome de usuário é obrigatório"}
            
            username = username.strip().lower()
            
            # Verificar se usuário já existe
            existing_users = self.list_users()
            for user in existing_users:
                if user.get("name", "").lower() == username:
                    return {"success": False, "message": f"Usuário '{username}' já existe"}
            
            # Gerar senha se não fornecida
            if not password:
                password = self.generate_secure_password()
            
            # Determinar IP
            if not ip_address:
                ip_address = self.get_next_available_ip(site)
                if not ip_address:
                    return {"success": False, "message": f"Não há IPs disponíveis no site '{site}'"}
            
            # Validar IP está na faixa correta
            if site in self.IP_RANGES:
                network = ipaddress.IPv4Network(self.IP_RANGES[site]["network"])
                if not ipaddress.IPv4Address(ip_address) in network:
                    return {"success": False, "message": f"IP {ip_address} não está na faixa do site {site}"}
            
            # Criar backup antes da alteração
            if not self._backup_config():
                self.logger.warning("Falha ao criar backup, prosseguindo com a operação")
            
            # Construir comando para adicionar usuário
            profile = f"vpn_{site}"
            command = f'/ppp secret add name="{username}" password="{password}" profile="{profile}" remote-address="{ip_address}" comment="Adicionado via Dashboard - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"'
            
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                self.logger.info(f"Usuário VPN criado: {username} - IP: {ip_address}")
                return {
                    "success": True, 
                    "message": f"Usuário '{username}' criado com sucesso",
                    "data": {
                        "username": username,
                        "password": password,
                        "ip_address": ip_address,
                        "site": site,
                        "profile": profile
                    }
                }
            else:
                self.logger.error(f"Erro ao criar usuário: {error}")
                return {"success": False, "message": f"Erro ao criar usuário: {error}"}
                
        except Exception as e:
            self.logger.error(f"Erro ao adicionar usuário: {str(e)}")
            return {"success": False, "message": f"Erro interno: {str(e)}"}
    
    def remove_user(self, username: str) -> Dict[str, any]:
        """Remove usuário VPN"""
        try:
            if not username or not username.strip():
                return {"success": False, "message": "Nome de usuário é obrigatório"}
            
            username = username.strip()
            
            # Verificar se usuário existe
            users = self.list_users()
            user_exists = any(user.get("name", "").lower() == username.lower() for user in users)
            
            if not user_exists:
                return {"success": False, "message": f"Usuário '{username}' não encontrado"}
            
            # Criar backup antes da alteração
            if not self._backup_config():
                self.logger.warning("Falha ao criar backup, prosseguindo com a operação")
            
            # Remover usuário
            command = f'/ppp secret remove [find name="{username}"]'
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                self.logger.info(f"Usuário VPN removido: {username}")
                return {"success": True, "message": f"Usuário '{username}' removido com sucesso"}
            else:
                self.logger.error(f"Erro ao remover usuário: {error}")
                return {"success": False, "message": f"Erro ao remover usuário: {error}"}
                
        except Exception as e:
            self.logger.error(f"Erro ao remover usuário: {str(e)}")
            return {"success": False, "message": f"Erro interno: {str(e)}"}
    
    def list_users(self) -> List[Dict[str, str]]:
        """Lista todos os usuários VPN configurados"""
        try:
            command = '/ppp secret print detail without-paging'
            output, error, exit_code = self._execute_command(command)
            
            if exit_code != 0:
                self.logger.error(f"Erro ao listar usuários: {error}")
                return []
            
            users = []
            current_user = {}
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    if current_user:
                        users.append(current_user)
                        current_user = {}
                    continue
                
                # Parse das linhas de saída do MikroTik
                if line.startswith('*') and 'name=' in line:
                    # Nova entrada de usuário
                    if current_user:
                        users.append(current_user)
                        current_user = {}
                    
                    # Extrair informações da linha
                    parts = line.split()
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            current_user[key] = value.strip('"')
            
            # Adicionar último usuário se existir
            if current_user:
                users.append(current_user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Erro ao listar usuários: {str(e)}")
            return []
    
    def get_active_connections(self) -> List[Dict[str, str]]:
        """Retorna conexões VPN ativas"""
        try:
            command = '/ppp active print detail without-paging'
            output, error, exit_code = self._execute_command(command)
            
            if exit_code != 0:
                self.logger.error(f"Erro ao listar conexões ativas: {error}")
                return []
            
            connections = []
            current_connection = {}
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    if current_connection:
                        connections.append(current_connection)
                        current_connection = {}
                    continue
                
                # Parse das linhas de saída do MikroTik
                if line.startswith('*') and 'name=' in line:
                    # Nova entrada de conexão
                    if current_connection:
                        connections.append(current_connection)
                        current_connection = {}
                    
                    # Extrair informações da linha
                    parts = line.split()
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            current_connection[key] = value.strip('"')
            
            # Adicionar última conexão se existir
            if current_connection:
                connections.append(current_connection)
            
            return connections
            
        except Exception as e:
            self.logger.error(f"Erro ao listar conexões ativas: {str(e)}")
            return []
    
    def get_user_stats(self, username: str) -> Dict[str, any]:
        """Retorna estatísticas de uso de um usuário específico"""
        try:
            # Buscar nas conexões ativas
            active_connections = self.get_active_connections()
            for conn in active_connections:
                if conn.get("name", "").lower() == username.lower():
                    return {
                        "status": "connected",
                        "uptime": conn.get("uptime", "N/A"),
                        "address": conn.get("address", "N/A"),
                        "caller_id": conn.get("caller-id", "N/A"),
                        "bytes_in": conn.get("bytes-in", "0"),
                        "bytes_out": conn.get("bytes-out", "0")
                    }
            
            # Se não está ativo, verificar se existe
            users = self.list_users()
            for user in users:
                if user.get("name", "").lower() == username.lower():
                    return {
                        "status": "configured",
                        "remote_address": user.get("remote-address", "N/A"),
                        "profile": user.get("profile", "N/A"),
                        "comment": user.get("comment", "N/A")
                    }
            
            return {"status": "not_found"}
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar estatísticas do usuário: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def test_connection(self) -> Dict[str, any]:
        """Testa conexão com o MikroTik"""
        try:
            command = '/system identity print'
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                return {"success": True, "message": "Conexão estabelecida com sucesso", "identity": output}
            else:
                return {"success": False, "message": f"Erro de conexão: {error}"}
                
        except Exception as e:
            return {"success": False, "message": f"Erro de conexão: {str(e)}"}
    
    def get_vpn_status(self) -> Dict[str, any]:
        """Retorna status geral do sistema VPN"""
        try:
            total_users = len(self.list_users())
            active_connections = len(self.get_active_connections())
            
            # Calcular IPs disponíveis
            available_ips = {}
            for site, config in self.IP_RANGES.items():
                total_range = config["end"] - config["start"] + 1
                fixed_count = len(config["fixed"])
                available = total_range - fixed_count
                available_ips[site] = {
                    "total": total_range,
                    "fixed": fixed_count,
                    "available": available
                }
            
            return {
                "total_users": total_users,
                "active_connections": active_connections,
                "available_ips": available_ips,
                "sites": list(self.IP_RANGES.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status VPN: {str(e)}")
            return {"error": str(e)}
    
    def change_user_password(self, username: str, new_password: str) -> Dict[str, any]:
        """Altera senha de um usuário existente"""
        try:
            if not username or not username.strip():
                return {"success": False, "message": "Nome de usuário é obrigatório"}
            
            if not new_password or len(new_password) < 8:
                return {"success": False, "message": "Senha deve ter pelo menos 8 caracteres"}
            
            username = username.strip()
            
            # Verificar se usuário existe
            users = self.list_users()
            user_exists = any(user.get("name", "").lower() == username.lower() for user in users)
            
            if not user_exists:
                return {"success": False, "message": f"Usuário '{username}' não encontrado"}
            
            # Criar backup antes da alteração
            if not self._backup_config():
                self.logger.warning("Falha ao criar backup, prosseguindo com a operação")
            
            # Alterar senha
            command = f'/ppp secret set [find name="{username}"] password="{new_password}"'
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                self.logger.info(f"Senha alterada para usuário: {username}")
                return {"success": True, "message": f"Senha alterada com sucesso para '{username}'"}
            else:
                self.logger.error(f"Erro ao alterar senha: {error}")
                return {"success": False, "message": f"Erro ao alterar senha: {error}"}
                
        except Exception as e:
            self.logger.error(f"Erro ao alterar senha: {str(e)}")
            return {"success": False, "message": f"Erro interno: {str(e)}"}
    
    def disconnect_user(self, username: str) -> Dict[str, any]:
        """Desconecta um usuário ativo"""
        try:
            if not username or not username.strip():
                return {"success": False, "message": "Nome de usuário é obrigatório"}
            
            username = username.strip()
            
            # Verificar se usuário está conectado
            active_connections = self.get_active_connections()
            user_connected = any(conn.get("name", "").lower() == username.lower() for conn in active_connections)
            
            if not user_connected:
                return {"success": False, "message": f"Usuário '{username}' não está conectado"}
            
            # Desconectar usuário
            command = f'/ppp active remove [find name="{username}"]'
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                self.logger.info(f"Usuário desconectado: {username}")
                return {"success": True, "message": f"Usuário '{username}' desconectado com sucesso"}
            else:
                self.logger.error(f"Erro ao desconectar usuário: {error}")
                return {"success": False, "message": f"Erro ao desconectar usuário: {error}"}
                
        except Exception as e:
            self.logger.error(f"Erro ao desconectar usuário: {str(e)}")
            return {"success": False, "message": f"Erro interno: {str(e)}"}