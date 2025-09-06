import json
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("Aviso: paramiko não está instalado. Funcionalidade SSH limitada.")

class MikroTikConfig:
    """Configurador SSH para dispositivos MikroTik"""
    
    def __init__(self):
        self.config_file = Path("/srv/projects/shared/dashboard/config/mikrotik_devices.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self.devices = {}
        self.load_config()
        
    def load_config(self):
        """Carrega configurações dos dispositivos"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self.devices = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar configuração MikroTik: {e}")
                self.devices = {}
        else:
            # Configuração inicial padrão
            self.devices = {
                "Casa": {
                    "ip": "10.0.10.1",
                    "port": 22,
                    "user": "admin",
                    "password": "",
                    "enabled": True,
                    "last_sync": None,
                    "description": "MikroTik da residência"
                },
                "Escritório": {
                    "ip": "10.0.20.1", 
                    "port": 22,
                    "user": "admin",
                    "password": "",
                    "enabled": True,
                    "last_sync": None,
                    "description": "MikroTik do escritório"
                }
            }
            self.save_config()
    
    def save_config(self):
        """Salva configurações no arquivo"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.devices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configuração MikroTik: {e}")
            
    def save_device(self, name: str, ip: str, port: int, user: str, password: str, description: str = ""):
        """Salva configuração de um dispositivo"""
        self.devices[name] = {
            'ip': ip,
            'port': int(port),
            'user': user,
            'password': password,
            'enabled': True,
            'last_sync': None,
            'description': description
        }
        self.save_config()
        return True
    
    def get_devices(self) -> Dict:
        """Retorna dispositivos configurados"""
        return self.devices
    
    def delete_device(self, name: str) -> bool:
        """Remove um dispositivo da configuração"""
        if name in self.devices:
            del self.devices[name]
            self.save_config()
            return True
        return False
    
    def toggle_device(self, name: str) -> bool:
        """Ativa/desativa um dispositivo"""
        if name in self.devices:
            self.devices[name]['enabled'] = not self.devices[name]['enabled']
            self.save_config()
            return True
        return False
    
    def test_connection(self, config: Dict) -> Tuple[bool, str]:
        """Testa conexão SSH com dispositivo"""
        if not PARAMIKO_AVAILABLE:
            return False, "Paramiko não disponível"
            
        if not config.get('enabled', True):
            return False, "Dispositivo desabilitado"
        
        try:
            # Primeiro teste básico de conectividade
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((config['ip'], config['port']))
            sock.close()
            
            if result != 0:
                return False, "Porta SSH não acessível"
            
            # Teste SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                config['ip'],
                port=config['port'],
                username=config['user'],
                password=config['password'],
                timeout=5,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Teste comando simples
            stdin, stdout, stderr = ssh.exec_command(":put \"test\"", timeout=5)
            output = stdout.read().decode().strip()
            
            ssh.close()
            
            if "test" in output:
                return True, "Conexão estabelecida"
            else:
                return True, "Conectado mas resposta inesperada"
                
        except paramiko.AuthenticationException:
            return False, "Falha na autenticação"
        except paramiko.SSHException as e:
            return False, f"Erro SSH: {str(e)}"
        except socket.timeout:
            return False, "Timeout de conexão"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def execute_command(self, device_name: str, command: str) -> Tuple[bool, str]:
        """Executa comando em um dispositivo específico"""
        if not PARAMIKO_AVAILABLE:
            return False, "Paramiko não disponível"
            
        if device_name not in self.devices:
            return False, "Dispositivo não encontrado"
        
        config = self.devices[device_name]
        if not config.get('enabled', True):
            return False, "Dispositivo desabilitado"
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                config['ip'],
                port=config['port'],
                username=config['user'],
                password=config['password'],
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            ssh.close()
            
            if error:
                return False, f"Erro: {error}"
            
            return True, output
            
        except Exception as e:
            return False, f"Erro ao executar comando: {str(e)}"
    
    def sync_device(self, name: str, routes: List[Dict]) -> Tuple[bool, str]:
        """Sincroniza rotas com dispositivo MikroTik específico"""
        if not PARAMIKO_AVAILABLE:
            return False, "Paramiko não disponível"
            
        if name not in self.devices:
            return False, "Dispositivo não encontrado"
        
        config = self.devices[name]
        if not config.get('enabled', True):
            return False, "Dispositivo desabilitado"
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                config['ip'],
                port=config['port'],
                username=config['user'],
                password=config['password'],
                timeout=15,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Verificar se rota padrão para 10.0.10.7 já existe
            gateway_ip = "10.0.10.7"
            
            # Primeiro, verificar conectividade com o gateway
            test_cmd = f"/ping {gateway_ip} count=2"
            stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=10)
            ping_result = stdout.read().decode().strip()
            
            if "timeout" in ping_result.lower():
                ssh.close()
                return False, f"Gateway {gateway_ip} não acessível do dispositivo"
            
            # Remover rotas VPN antigas
            remove_cmd = '/ip route remove [find comment="vpn-gateway"]'
            stdin, stdout, stderr = ssh.exec_command(remove_cmd, timeout=10)
            stdout.read()  # Aguardar conclusão
            
            # Adicionar novas rotas
            success_count = 0
            error_messages = []
            
            for route in routes:
                network = route['network']
                comment = f"vpn-gateway-{network.replace('/', '_')}"
                
                # Comando para adicionar rota
                add_cmd = f'/ip route add dst-address={network} gateway={gateway_ip} comment="{comment}" distance=1'
                
                stdin, stdout, stderr = ssh.exec_command(add_cmd, timeout=10)
                error_output = stderr.read().decode().strip()
                
                if error_output:
                    if "already have" not in error_output.lower():  # Ignorar se rota já existe
                        error_messages.append(f"Rota {network}: {error_output}")
                else:
                    success_count += 1
            
            ssh.close()
            
            # Atualizar timestamp de sincronização
            self.devices[name]['last_sync'] = datetime.now().isoformat()
            self.save_config()
            
            if success_count > 0:
                return True, f"Sincronizado: {success_count} rotas. Erros: {len(error_messages)}"
            else:
                error_summary = "; ".join(error_messages[:3])  # Primeiros 3 erros
                return False, f"Nenhuma rota sincronizada. Erros: {error_summary}"
                
        except Exception as e:
            return False, f"Erro ao sincronizar {name}: {str(e)}"
    
    def sync_routes(self, routes: List[Dict]) -> Dict[str, Tuple[bool, str]]:
        """Sincroniza rotas com todos os dispositivos habilitados"""
        results = {}
        
        for name, config in self.devices.items():
            if config.get('enabled', True):
                success, message = self.sync_device(name, routes)
                results[name] = (success, message)
            else:
                results[name] = (False, "Dispositivo desabilitado")
        
        return results
    
    def get_device_info(self, name: str) -> Optional[Dict]:
        """Obtém informações detalhadas de um dispositivo"""
        if name not in self.devices:
            return None
        
        config = self.devices[name].copy()
        
        # Testar conectividade
        is_online, status_msg = self.test_connection(config)
        config['online'] = is_online
        config['status_message'] = status_msg
        
        # Obter informações do sistema se online
        if is_online and PARAMIKO_AVAILABLE:
            try:
                system_info = self.get_system_info(name)
                config.update(system_info)
            except:
                pass
        
        return config
    
    def get_system_info(self, name: str) -> Dict:
        """Obtém informações do sistema MikroTik"""
        if not PARAMIKO_AVAILABLE or name not in self.devices:
            return {}
        
        config = self.devices[name]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                config['ip'],
                port=config['port'],
                username=config['user'],
                password=config['password'],
                timeout=10
            )
            
            # Obter informações básicas
            stdin, stdout, stderr = ssh.exec_command('/system resource print', timeout=10)
            resource_output = stdout.read().decode().strip()
            
            stdin, stdout, stderr = ssh.exec_command('/system identity print', timeout=5)
            identity_output = stdout.read().decode().strip()
            
            ssh.close()
            
            # Parse das informações
            info = {}
            
            # Parse identity
            if "name:" in identity_output:
                name_line = [line for line in identity_output.split('\n') if 'name:' in line]
                if name_line:
                    info['identity'] = name_line[0].split('name:')[1].strip()
            
            # Parse resource (versão, uptime, etc)
            resource_lines = resource_output.split('\n')
            for line in resource_lines:
                if 'version:' in line.lower():
                    info['version'] = line.split(':')[1].strip() if ':' in line else 'N/A'
                elif 'uptime:' in line.lower():
                    info['uptime'] = line.split(':')[1].strip() if ':' in line else 'N/A'
                elif 'cpu-load:' in line.lower():
                    info['cpu_load'] = line.split(':')[1].strip() if ':' in line else 'N/A'
            
            return info
            
        except Exception as e:
            print(f"Erro ao obter informações do sistema {name}: {e}")
            return {}
    
    def backup_config(self, name: str) -> Tuple[bool, str]:
        """Cria backup da configuração do dispositivo"""
        if not PARAMIKO_AVAILABLE or name not in self.devices:
            return False, "Dispositivo não disponível"
        
        config = self.devices[name]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                config['ip'],
                port=config['port'],
                username=config['user'],
                password=config['password'],
                timeout=10
            )
            
            # Criar backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"vpn_gateway_backup_{timestamp}"
            
            backup_cmd = f'/system backup save name={backup_name}'
            stdin, stdout, stderr = ssh.exec_command(backup_cmd, timeout=30)
            
            # Aguardar conclusão
            stdout.read()
            error_output = stderr.read().decode().strip()
            
            ssh.close()
            
            if error_output:
                return False, f"Erro no backup: {error_output}"
            
            return True, f"Backup criado: {backup_name}.backup"
            
        except Exception as e:
            return False, f"Erro ao criar backup: {str(e)}"
    
    def get_route_table(self, name: str) -> Tuple[bool, List[Dict]]:
        """Obtém tabela de rotas do dispositivo"""
        if not PARAMIKO_AVAILABLE or name not in self.devices:
            return False, []
        
        config = self.devices[name]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                config['ip'],
                port=config['port'],
                username=config['user'],
                password=config['password'],
                timeout=10
            )
            
            # Obter rotas VPN
            routes_cmd = '/ip route print where comment~"vpn-gateway"'
            stdin, stdout, stderr = ssh.exec_command(routes_cmd, timeout=10)
            routes_output = stdout.read().decode().strip()
            
            ssh.close()
            
            # Parse das rotas
            routes = []
            if routes_output:
                lines = routes_output.split('\n')
                for line in lines:
                    if 'dst-address' in line and 'gateway' in line:
                        # Parse básico da linha de rota
                        route_info = {'raw': line.strip()}
                        routes.append(route_info)
            
            return True, routes
            
        except Exception as e:
            print(f"Erro ao obter rotas de {name}: {e}")
            return False, []
    
    def get_statistics(self) -> Dict:
        """Obtém estatísticas gerais dos dispositivos"""
        total = len(self.devices)
        online = 0
        enabled = 0
        last_sync_times = []
        
        for name, config in self.devices.items():
            if config.get('enabled', True):
                enabled += 1
                
                # Teste rápido de conectividade
                is_online, _ = self.test_connection(config)
                if is_online:
                    online += 1
            
            if config.get('last_sync'):
                try:
                    sync_time = datetime.fromisoformat(config['last_sync'])
                    last_sync_times.append(sync_time)
                except:
                    pass
        
        # Última sincronização geral
        last_global_sync = "Nunca"
        if last_sync_times:
            latest_sync = max(last_sync_times)
            time_diff = datetime.now() - latest_sync
            if time_diff.total_seconds() < 3600:  # menos de 1 hora
                last_global_sync = f"{int(time_diff.total_seconds() // 60)}min atrás"
            elif time_diff.days == 0:
                last_global_sync = f"{int(time_diff.total_seconds() // 3600)}h atrás"
            else:
                last_global_sync = f"{time_diff.days}d atrás"
        
        return {
            'total_devices': total,
            'enabled_devices': enabled,
            'online_devices': online,
            'offline_devices': enabled - online,
            'last_sync': last_global_sync,
            'paramiko_available': PARAMIKO_AVAILABLE
        }