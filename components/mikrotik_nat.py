import paramiko
import json
import socket
import ipaddress
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
import re

class MikroTikNAT:
    """Classe para gerenciamento de NAT/Port Forwarding no MikroTik via SSH"""
    
    def __init__(self):
        self.host = "10.0.10.1"
        self.user = "admin"
        self.password = "cwTS6FbVs7GNxBRXAigfgaGLWILMdEfv"
        self.port = 22
        self.timeout = 30
        
        # Servidores conhecidos na rede
        self.KNOWN_SERVERS = {
            "10.0.10.4": "Windows Server",
            "10.0.10.5": "Docker Server",
            "10.0.10.6": "Home Assistant",
            "10.0.10.7": "Development Server",
            "10.0.10.11": "MacBook Pro"
        }
        
        # Templates de serviços comuns
        self.SERVICE_TEMPLATES = {
            "web": {"port": 80, "protocol": "tcp", "name": "HTTP"},
            "https": {"port": 443, "protocol": "tcp", "name": "HTTPS"},
            "ssh": {"port": 22, "protocol": "tcp", "name": "SSH"},
            "rdp": {"port": 3389, "protocol": "tcp", "name": "RDP"},
            "streamlit": {"port": 8501, "protocol": "tcp", "name": "Streamlit"},
            "jupyter": {"port": 8888, "protocol": "tcp", "name": "Jupyter"},
            "mongodb": {"port": 27017, "protocol": "tcp", "name": "MongoDB"},
            "mysql": {"port": 3306, "protocol": "tcp", "name": "MySQL"},
            "postgres": {"port": 5432, "protocol": "tcp", "name": "PostgreSQL"},
            "ftp": {"port": 21, "protocol": "tcp", "name": "FTP"},
            "sftp": {"port": 22, "protocol": "tcp", "name": "SFTP"},
            "telnet": {"port": 23, "protocol": "tcp", "name": "Telnet"},
            "smtp": {"port": 25, "protocol": "tcp", "name": "SMTP"},
            "dns": {"port": 53, "protocol": "udp", "name": "DNS"},
            "dhcp": {"port": 67, "protocol": "udp", "name": "DHCP"},
            "pop3": {"port": 110, "protocol": "tcp", "name": "POP3"},
            "ntp": {"port": 123, "protocol": "udp", "name": "NTP"},
            "imap": {"port": 143, "protocol": "tcp", "name": "IMAP"},
            "snmp": {"port": 161, "protocol": "udp", "name": "SNMP"},
            "ldap": {"port": 389, "protocol": "tcp", "name": "LDAP"},
            "smtps": {"port": 465, "protocol": "tcp", "name": "SMTP/SSL"},
            "imaps": {"port": 993, "protocol": "tcp", "name": "IMAP/SSL"},
            "pop3s": {"port": 995, "protocol": "tcp", "name": "POP3/SSL"},
            "mssql": {"port": 1433, "protocol": "tcp", "name": "MS SQL Server"},
            "oracle": {"port": 1521, "protocol": "tcp", "name": "Oracle DB"},
            "minecraft": {"port": 25565, "protocol": "tcp", "name": "Minecraft Server"},
            "teamspeak": {"port": 9987, "protocol": "udp", "name": "TeamSpeak"},
            "openvpn": {"port": 1194, "protocol": "udp", "name": "OpenVPN"}
        }
        
        # Portas reservadas/privilegiadas que não devem ser usadas
        self.RESERVED_PORTS = set(range(1, 1024))
        
        # Portas comumente usadas pelo sistema que devem ser evitadas
        self.SYSTEM_PORTS = {80, 443, 22, 21, 25, 53, 67, 68, 110, 123, 143, 161, 389, 993, 995}
        
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
            backup_name = f"nat_backup_{timestamp}"
            
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
    
    def _validate_ip(self, ip: str) -> bool:
        """Valida se o IP é válido e está na rede interna"""
        try:
            ip_obj = ipaddress.IPv4Address(ip)
            # Verificar se está em redes privadas
            private_networks = [
                ipaddress.IPv4Network("10.0.0.0/8"),
                ipaddress.IPv4Network("172.16.0.0/12"),
                ipaddress.IPv4Network("192.168.0.0/16")
            ]
            
            for network in private_networks:
                if ip_obj in network:
                    return True
            return False
            
        except Exception:
            return False
    
    def _validate_port(self, port: int) -> bool:
        """Valida se a porta está no range válido"""
        return 1 <= port <= 65535
    
    def _validate_protocol(self, protocol: str) -> bool:
        """Valida se o protocolo é válido"""
        return protocol.lower() in ["tcp", "udp"]
    
    def check_port_available(self, port: int, protocol: str = "tcp") -> Dict[str, any]:
        """Verifica se porta externa está disponível"""
        try:
            if not self._validate_port(port):
                return {"available": False, "reason": "Porta inválida (deve ser entre 1-65535)"}
            
            if not self._validate_protocol(protocol):
                return {"available": False, "reason": "Protocolo inválido (deve ser tcp ou udp)"}
            
            # Listar regras NAT existentes
            nat_rules = self.list_nat_rules()
            
            for rule in nat_rules:
                if (rule.get("dst_port") == str(port) and 
                    rule.get("protocol", "").lower() == protocol.lower()):
                    return {
                        "available": False, 
                        "reason": f"Porta {port}/{protocol} já está em uso",
                        "used_by": rule.get("comment", "Regra sem comentário")
                    }
            
            # Verificar se é porta reservada/sistema
            if port in self.RESERVED_PORTS:
                return {
                    "available": False, 
                    "reason": f"Porta {port} é reservada pelo sistema"
                }
            
            if port in self.SYSTEM_PORTS:
                return {
                    "available": False,
                    "reason": f"Porta {port} é usada por serviços do sistema"
                }
            
            return {"available": True, "reason": "Porta disponível"}
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar disponibilidade da porta: {str(e)}")
            return {"available": False, "reason": f"Erro interno: {str(e)}"}
    
    def suggest_port(self, internal_port: int, protocol: str = "tcp") -> int:
        """Sugere uma porta externa disponível baseada na porta interna"""
        try:
            # Primeiro tentar a mesma porta
            check = self.check_port_available(internal_port, protocol)
            if check["available"]:
                return internal_port
            
            # Tentar portas próximas (acima)
            for offset in range(1, 100):
                candidate = internal_port + offset
                if candidate > 65535:
                    break
                
                check = self.check_port_available(candidate, protocol)
                if check["available"]:
                    return candidate
            
            # Tentar portas aleatórias em ranges seguros
            import random
            safe_ranges = [(8000, 8999), (9000, 9999), (10000, 19999), (20000, 29999)]
            
            for start, end in safe_ranges:
                for _ in range(50):  # Tentar até 50 vezes por range
                    candidate = random.randint(start, end)
                    check = self.check_port_available(candidate, protocol)
                    if check["available"]:
                        return candidate
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao sugerir porta: {str(e)}")
            return None
    
    def test_port(self, ip: str, port: int, protocol: str = "tcp", timeout: int = 5) -> Dict[str, any]:
        """Testa conectividade da porta interna"""
        try:
            if not self._validate_ip(ip):
                return {"reachable": False, "reason": "IP inválido ou não é uma rede privada"}
            
            if not self._validate_port(port):
                return {"reachable": False, "reason": "Porta inválida"}
            
            if protocol.lower() == "tcp":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            elif protocol.lower() == "udp":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else:
                return {"reachable": False, "reason": "Protocolo inválido"}
            
            sock.settimeout(timeout)
            
            try:
                if protocol.lower() == "tcp":
                    result = sock.connect_ex((ip, port))
                    reachable = result == 0
                else:
                    # Para UDP, tentar enviar dados
                    sock.sendto(b"test", (ip, port))
                    reachable = True  # Se não houver exceção, assumir que está alcançável
                
                sock.close()
                
                return {
                    "reachable": reachable,
                    "reason": "Porta alcançável" if reachable else "Porta não alcançável ou serviço inativo"
                }
                
            except Exception as e:
                sock.close()
                return {"reachable": False, "reason": f"Erro de conexão: {str(e)}"}
            
        except Exception as e:
            self.logger.error(f"Erro ao testar porta: {str(e)}")
            return {"reachable": False, "reason": f"Erro interno: {str(e)}"}
    
    def add_port_forward(self, internal_ip: str, internal_port: int, 
                        external_port: Optional[int] = None, protocol: str = "tcp", 
                        comment: str = "") -> Dict[str, any]:
        """Adiciona regra de port forwarding"""
        try:
            # Validações
            if not self._validate_ip(internal_ip):
                return {"success": False, "message": "IP interno inválido"}
            
            if not self._validate_port(internal_port):
                return {"success": False, "message": "Porta interna inválida"}
            
            if not self._validate_protocol(protocol):
                return {"success": False, "message": "Protocolo inválido (tcp ou udp)"}
            
            # Se porta externa não especificada, sugerir uma
            if external_port is None:
                external_port = self.suggest_port(internal_port, protocol)
                if external_port is None:
                    return {"success": False, "message": "Não foi possível encontrar uma porta externa disponível"}
            
            if not self._validate_port(external_port):
                return {"success": False, "message": "Porta externa inválida"}
            
            # Verificar se porta externa está disponível
            port_check = self.check_port_available(external_port, protocol)
            if not port_check["available"]:
                return {"success": False, "message": f"Porta externa não disponível: {port_check['reason']}"}
            
            # Testar conectividade da porta interna
            port_test = self.test_port(internal_ip, internal_port, protocol)
            if not port_test["reachable"]:
                self.logger.warning(f"Porta interna {internal_ip}:{internal_port} pode não estar ativa: {port_test['reason']}")
            
            # Criar backup antes da alteração
            if not self._backup_config():
                self.logger.warning("Falha ao criar backup, prosseguindo com a operação")
            
            # Gerar comentário se não fornecido
            if not comment:
                service_name = self.KNOWN_SERVERS.get(internal_ip, "Servidor")
                comment = f"{service_name} - {internal_port}/{protocol.upper()} - Dashboard {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Construir comando para adicionar regra NAT
            command = (f'/ip firewall nat add '
                      f'chain=dstnat '
                      f'dst-port={external_port} '
                      f'protocol={protocol} '
                      f'to-addresses={internal_ip} '
                      f'to-ports={internal_port} '
                      f'action=dst-nat '
                      f'comment="{comment}"')
            
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                self.logger.info(f"Regra NAT criada: {external_port}->{internal_ip}:{internal_port} ({protocol})")
                
                result = {
                    "success": True,
                    "message": f"Regra de port forwarding criada com sucesso",
                    "data": {
                        "internal_ip": internal_ip,
                        "internal_port": internal_port,
                        "external_port": external_port,
                        "protocol": protocol,
                        "comment": comment,
                        "port_test": port_test
                    }
                }
                
                return result
            else:
                self.logger.error(f"Erro ao criar regra NAT: {error}")
                return {"success": False, "message": f"Erro ao criar regra: {error}"}
                
        except Exception as e:
            self.logger.error(f"Erro ao adicionar port forwarding: {str(e)}")
            return {"success": False, "message": f"Erro interno: {str(e)}"}
    
    def remove_port_forward(self, rule_id: Optional[str] = None, external_port: Optional[int] = None, 
                           protocol: Optional[str] = None, comment: Optional[str] = None) -> Dict[str, any]:
        """Remove regra de port forwarding"""
        try:
            # Criar backup antes da alteração
            if not self._backup_config():
                self.logger.warning("Falha ao criar backup, prosseguindo com a operação")
            
            # Construir comando baseado nos parâmetros fornecidos
            if rule_id:
                # Remover por ID específico
                command = f'/ip firewall nat remove {rule_id}'
            elif comment:
                # Remover por comentário
                command = f'/ip firewall nat remove [find comment="{comment}"]'
            elif external_port and protocol:
                # Remover por porta e protocolo
                command = f'/ip firewall nat remove [find dst-port={external_port} protocol={protocol} chain=dstnat]'
            else:
                return {"success": False, "message": "É necessário fornecer rule_id, comment ou external_port+protocol"}
            
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                self.logger.info(f"Regra NAT removida: {rule_id or external_port or comment}")
                return {"success": True, "message": "Regra de port forwarding removida com sucesso"}
            else:
                self.logger.error(f"Erro ao remover regra NAT: {error}")
                return {"success": False, "message": f"Erro ao remover regra: {error}"}
                
        except Exception as e:
            self.logger.error(f"Erro ao remover port forwarding: {str(e)}")
            return {"success": False, "message": f"Erro interno: {str(e)}"}
    
    def list_nat_rules(self) -> List[Dict[str, str]]:
        """Lista todas as regras NAT de port forwarding"""
        try:
            command = '/ip firewall nat print detail without-paging where chain=dstnat'
            output, error, exit_code = self._execute_command(command)
            
            if exit_code != 0:
                self.logger.error(f"Erro ao listar regras NAT: {error}")
                return []
            
            rules = []
            current_rule = {}
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    if current_rule:
                        rules.append(current_rule)
                        current_rule = {}
                    continue
                
                # Parse das linhas de saída do MikroTik
                if line.startswith('*') or line.startswith('X'):
                    # Nova entrada de regra
                    if current_rule:
                        rules.append(current_rule)
                        current_rule = {}
                    
                    # Status da regra
                    current_rule["status"] = "active" if line.startswith('*') else "disabled"
                    
                    # Extrair ID
                    id_match = re.search(r'(\d+)', line)
                    if id_match:
                        current_rule["id"] = id_match.group(1)
                    
                    # Extrair informações da linha
                    parts = line.split()
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            current_rule[key.replace('-', '_')] = value.strip('"')
                
                elif '=' in line and current_rule:
                    # Linhas de continuação com mais propriedades
                    parts = line.split()
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            current_rule[key.replace('-', '_')] = value.strip('"')
            
            # Adicionar última regra se existir
            if current_rule:
                rules.append(current_rule)
            
            # Filtrar apenas regras de port forwarding (dst-nat)
            port_forward_rules = []
            for rule in rules:
                if rule.get("action") == "dst-nat" or rule.get("chain") == "dstnat":
                    # Adicionar informações extras
                    rule["server_name"] = self.KNOWN_SERVERS.get(rule.get("to_addresses", ""), "Servidor Desconhecido")
                    port_forward_rules.append(rule)
            
            return port_forward_rules
            
        except Exception as e:
            self.logger.error(f"Erro ao listar regras NAT: {str(e)}")
            return []
    
    def get_nat_stats(self) -> Dict[str, any]:
        """Retorna estatísticas das regras NAT"""
        try:
            rules = self.list_nat_rules()
            
            total_rules = len(rules)
            active_rules = len([r for r in rules if r.get("status") == "active"])
            disabled_rules = len([r for r in rules if r.get("status") == "disabled"])
            
            # Agrupar por protocolo
            protocol_stats = {}
            for rule in rules:
                protocol = rule.get("protocol", "unknown")
                protocol_stats[protocol] = protocol_stats.get(protocol, 0) + 1
            
            # Agrupar por servidor
            server_stats = {}
            for rule in rules:
                server = rule.get("server_name", "Desconhecido")
                server_stats[server] = server_stats.get(server, 0) + 1
            
            # Portas mais usadas
            port_usage = {}
            for rule in rules:
                port = rule.get("dst_port", "unknown")
                port_usage[port] = port_usage.get(port, 0) + 1
            
            return {
                "total_rules": total_rules,
                "active_rules": active_rules,
                "disabled_rules": disabled_rules,
                "protocol_stats": protocol_stats,
                "server_stats": server_stats,
                "port_usage": dict(sorted(port_usage.items(), key=lambda x: x[1], reverse=True))
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas NAT: {str(e)}")
            return {"error": str(e)}
    
    def toggle_rule(self, rule_id: str, enable: bool = True) -> Dict[str, any]:
        """Habilita ou desabilita uma regra NAT"""
        try:
            action = "enable" if enable else "disable"
            command = f'/ip firewall nat {action} {rule_id}'
            
            output, error, exit_code = self._execute_command(command)
            
            if exit_code == 0:
                status = "habilitada" if enable else "desabilitada"
                self.logger.info(f"Regra NAT {rule_id} {status}")
                return {"success": True, "message": f"Regra {status} com sucesso"}
            else:
                self.logger.error(f"Erro ao alterar regra NAT: {error}")
                return {"success": False, "message": f"Erro ao alterar regra: {error}"}
                
        except Exception as e:
            self.logger.error(f"Erro ao alterar regra: {str(e)}")
            return {"success": False, "message": f"Erro interno: {str(e)}"}
    
    def get_service_templates(self) -> Dict[str, Dict[str, any]]:
        """Retorna templates de serviços disponíveis"""
        return self.SERVICE_TEMPLATES.copy()
    
    def get_known_servers(self) -> Dict[str, str]:
        """Retorna lista de servidores conhecidos"""
        return self.KNOWN_SERVERS.copy()
    
    def scan_local_network(self, network: str = "10.0.10.0/24") -> List[Dict[str, any]]:
        """Escaneia rede local para encontrar hosts ativos (básico)"""
        try:
            import subprocess
            import ipaddress
            
            net = ipaddress.IPv4Network(network)
            active_hosts = []
            
            # Scan básico com ping (limitado aos primeiros 20 IPs para não demorar)
            for i, ip in enumerate(net.hosts()):
                if i > 20:  # Limitar scan
                    break
                
                try:
                    # Ping simples
                    result = subprocess.run(
                        ['ping', '-c', '1', '-W', '1', str(ip)], 
                        capture_output=True, 
                        timeout=2
                    )
                    
                    if result.returncode == 0:
                        host_info = {
                            "ip": str(ip),
                            "name": self.KNOWN_SERVERS.get(str(ip), "Host Desconhecido"),
                            "status": "active"
                        }
                        active_hosts.append(host_info)
                        
                except Exception:
                    continue
            
            return active_hosts
            
        except Exception as e:
            self.logger.error(f"Erro ao escanear rede: {str(e)}")
            return []
    
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
    
    def get_port_usage_report(self) -> Dict[str, any]:
        """Gera relatório de uso de portas"""
        try:
            rules = self.list_nat_rules()
            
            report = {
                "used_ports": [],
                "available_ranges": [],
                "recommendations": []
            }
            
            used_ports = set()
            for rule in rules:
                port = rule.get("dst_port")
                if port and port.isdigit():
                    used_ports.add(int(port))
                    report["used_ports"].append({
                        "port": int(port),
                        "protocol": rule.get("protocol", "tcp"),
                        "target": f"{rule.get('to_addresses')}:{rule.get('to_ports')}",
                        "comment": rule.get("comment", "Sem comentário")
                    })
            
            # Encontrar ranges disponíveis
            all_ports = set(range(1, 65536))
            available_ports = all_ports - used_ports - self.RESERVED_PORTS - self.SYSTEM_PORTS
            
            # Agrupar portas disponíveis em ranges
            sorted_available = sorted(available_ports)
            ranges = []
            start = None
            end = None
            
            for port in sorted_available:
                if start is None:
                    start = end = port
                elif port == end + 1:
                    end = port
                else:
                    if end - start >= 9:  # Apenas ranges com 10+ portas
                        ranges.append(f"{start}-{end}")
                    start = end = port
            
            if start is not None and end - start >= 9:
                ranges.append(f"{start}-{end}")
            
            report["available_ranges"] = ranges[:10]  # Top 10 ranges
            
            # Recomendações
            if len(used_ports) > 50:
                report["recommendations"].append("Alto número de regras NAT - considere revisar regras não utilizadas")
            
            if any(p < 1024 for p in used_ports):
                report["recommendations"].append("Algumas regras usam portas privilegiadas - verifique se é necessário")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {str(e)}")
            return {"error": str(e)}