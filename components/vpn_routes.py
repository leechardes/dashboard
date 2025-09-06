import subprocess
import json
import ipaddress
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class VPNRoutes:
    """Gerenciador de rotas VPN para gateway OpenVPN"""
    
    def __init__(self):
        self.config_file = Path("/srv/projects/shared/dashboard/config/vpn_routes.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self.interface = "tun0"
        self.gateway_ip = "10.0.10.7"  # IP do servidor que atua como gateway
        self.routes = []
        self.load_routes()
    
    def load_routes(self):
        """Carrega rotas salvas do arquivo de configuração"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                    self.routes = data.get('routes', [])
                    self.gateway_ip = data.get('gateway_ip', self.gateway_ip)
                    self.interface = data.get('interface', self.interface)
            except Exception as e:
                print(f"Erro ao carregar rotas: {e}")
                self.routes = []
        else:
            # Configuração inicial com redes comuns
            self.routes = [
                {
                    'network': '192.168.1.0/24',
                    'gateway': self.gateway_ip,
                    'description': 'Rede casa exemplo',
                    'enabled': True,
                    'created': datetime.now().isoformat(),
                    'last_sync': None
                },
                {
                    'network': '192.168.2.0/24', 
                    'gateway': self.gateway_ip,
                    'description': 'Rede escritório exemplo',
                    'enabled': True,
                    'created': datetime.now().isoformat(),
                    'last_sync': None
                }
            ]
            self.save_routes()
    
    def save_routes(self):
        """Salva rotas no arquivo de configuração"""
        try:
            data = {
                'routes': self.routes,
                'gateway_ip': self.gateway_ip,
                'interface': self.interface,
                'last_update': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar rotas: {e}")
    
    def validate_network(self, network: str) -> Tuple[bool, str]:
        """Valida formato de rede CIDR"""
        try:
            net = ipaddress.ip_network(network, strict=False)
            
            # Verificar se não é uma rede reservada problemática
            if net.is_loopback:
                return False, "Rede de loopback não permitida"
            
            if net.is_link_local:
                return False, "Rede link-local não permitida"
            
            # Verificar se não é a própria rede VPN
            if str(net).startswith('10.8.') or str(net).startswith('10.9.'):
                return False, "Rede VPN não pode ser roteada através de si mesma"
            
            return True, "Rede válida"
            
        except ValueError as e:
            return False, f"Formato CIDR inválido: {str(e)}"
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"
    
    def add_route(self, network: str, description: str = "", enabled: bool = True) -> Tuple[bool, str]:
        """Adiciona nova rota ao sistema"""
        # Validar rede
        is_valid, validation_msg = self.validate_network(network)
        if not is_valid:
            return False, validation_msg
        
        # Verificar se já existe
        for route in self.routes:
            if route['network'] == network:
                return False, f"Rota {network} já existe"
        
        # Obter gateway atual da VPN
        current_gateway = self.get_vpn_gateway()
        if not current_gateway:
            return False, "Interface VPN não encontrada ou gateway não detectado"
        
        try:
            # Adicionar rota no sistema Linux
            add_result = self._add_system_route(network, current_gateway)
            if not add_result[0]:
                return False, f"Falha ao adicionar rota no sistema: {add_result[1]}"
            
            # Configurar regras de firewall
            firewall_result = self._add_firewall_rules(network)
            if not firewall_result[0]:
                # Se firewall falhar, remover rota do sistema
                self._remove_system_route(network)
                return False, f"Falha ao configurar firewall: {firewall_result[1]}"
            
            # Salvar na configuração
            new_route = {
                'network': network,
                'gateway': current_gateway,
                'description': description or f"Rota para {network}",
                'enabled': enabled,
                'created': datetime.now().isoformat(),
                'last_sync': None,
                'system_added': True
            }
            
            self.routes.append(new_route)
            self.save_routes()
            
            return True, f"Rota {network} adicionada com sucesso"
            
        except Exception as e:
            return False, f"Erro ao adicionar rota: {str(e)}"
    
    def remove_route(self, network: str) -> Tuple[bool, str]:
        """Remove uma rota do sistema"""
        # Encontrar rota
        route_to_remove = None
        for i, route in enumerate(self.routes):
            if route['network'] == network:
                route_to_remove = (i, route)
                break
        
        if not route_to_remove:
            return False, f"Rota {network} não encontrada"
        
        index, route = route_to_remove
        
        try:
            # Remover do sistema Linux
            system_result = self._remove_system_route(network)
            
            # Remover regras de firewall
            firewall_result = self._remove_firewall_rules(network)
            
            # Remover da configuração
            del self.routes[index]
            self.save_routes()
            
            # Preparar mensagem de resultado
            messages = []
            if not system_result[0]:
                messages.append(f"Sistema: {system_result[1]}")
            if not firewall_result[0]:
                messages.append(f"Firewall: {firewall_result[1]}")
            
            if messages:
                return True, f"Rota removida da configuração. Avisos: {'; '.join(messages)}"
            else:
                return True, f"Rota {network} removida completamente"
                
        except Exception as e:
            return False, f"Erro ao remover rota: {str(e)}"
    
    def toggle_route(self, network: str) -> Tuple[bool, str]:
        """Ativa/desativa uma rota"""
        for route in self.routes:
            if route['network'] == network:
                route['enabled'] = not route['enabled']
                
                if route['enabled']:
                    # Reativar rota
                    gateway = self.get_vpn_gateway()
                    if gateway:
                        result = self._add_system_route(network, gateway)
                        self._add_firewall_rules(network)
                        route['gateway'] = gateway
                        
                        self.save_routes()
                        status = "ativada" if result[0] else f"ativada na config (sistema: {result[1]})"
                        return True, f"Rota {network} {status}"
                    else:
                        route['enabled'] = False  # Reverter se não conseguir ativar
                        return False, "VPN não conectada - rota mantida desabilitada"
                else:
                    # Desativar rota
                    self._remove_system_route(network)
                    self._remove_firewall_rules(network)
                    self.save_routes()
                    return True, f"Rota {network} desativada"
        
        return False, f"Rota {network} não encontrada"
    
    def get_active_routes(self) -> List[Dict]:
        """Retorna apenas rotas ativas"""
        return [route for route in self.routes if route.get('enabled', True)]
    
    def get_all_routes(self) -> List[Dict]:
        """Retorna todas as rotas configuradas"""
        return self.routes.copy()
    
    def get_vpn_gateway(self) -> Optional[str]:
        """Obtém gateway atual da VPN"""
        try:
            # Método 1: Verificar rotas da interface tun0
            result = subprocess.run(
                ['ip', 'route', 'show', 'dev', self.interface],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                
                # Procurar por linha com 'via'
                for line in lines:
                    if 'via' in line:
                        parts = line.split()
                        via_index = parts.index('via')
                        if via_index + 1 < len(parts):
                            gateway = parts[via_index + 1]
                            # Validar se é IP válido
                            ipaddress.ip_address(gateway)
                            return gateway
                
                # Se não encontrar 'via', pegar primeiro IP da primeira linha
                if lines:
                    first_line = lines[0].strip()
                    if first_line:
                        # Tentar extrair IP do formato "10.8.0.1/30" ou "10.8.0.0/30"
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', first_line)
                        if ip_match:
                            potential_gw = ip_match.group(1)
                            # Se termina em .1, provavelmente é o gateway
                            if potential_gw.endswith('.1'):
                                return potential_gw
                            # Senão, tentar .1 da mesma rede
                            parts = potential_gw.split('.')
                            parts[-1] = '1'
                            return '.'.join(parts)
            
            # Método 2: Verificar rota padrão através do tun0
            result2 = subprocess.run(
                ['ip', 'route', 'show', '0.0.0.0/1', 'dev', self.interface],
                capture_output=True, text=True, timeout=5
            )
            
            if result2.returncode == 0 and result2.stdout:
                via_match = re.search(r'via (\d+\.\d+\.\d+\.\d+)', result2.stdout)
                if via_match:
                    return via_match.group(1)
            
            # Método 3: Fallback para gateway comum do OpenVPN
            return "10.8.0.1"
            
        except Exception as e:
            print(f"Erro ao obter gateway VPN: {e}")
            return None
    
    def _add_system_route(self, network: str, gateway: str) -> Tuple[bool, str]:
        """Adiciona rota no sistema Linux"""
        try:
            cmd = ['sudo', 'ip', 'route', 'add', network, 'via', gateway, 'dev', self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return True, "Rota adicionada ao sistema"
            elif "File exists" in result.stderr:
                return True, "Rota já existe no sistema"
            else:
                return False, result.stderr.strip() or "Erro desconhecido"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout ao adicionar rota"
        except Exception as e:
            return False, str(e)
    
    def _remove_system_route(self, network: str) -> Tuple[bool, str]:
        """Remove rota do sistema Linux"""
        try:
            cmd = ['sudo', 'ip', 'route', 'del', network]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return True, "Rota removida do sistema"
            elif "No such process" in result.stderr or "not found" in result.stderr:
                return True, "Rota não estava presente no sistema"
            else:
                return False, result.stderr.strip() or "Erro desconhecido"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout ao remover rota"
        except Exception as e:
            return False, str(e)
    
    def _add_firewall_rules(self, network: str) -> Tuple[bool, str]:
        """Adiciona regras de firewall para a rede"""
        try:
            # Regra de MASQUERADE para NAT
            masq_cmd = [
                'sudo', 'iptables', '-t', 'nat', '-C', 'POSTROUTING',
                '-s', network, '-o', self.interface, '-j', 'MASQUERADE'
            ]
            
            # Verificar se regra já existe
            check_result = subprocess.run(masq_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                # Regra não existe, adicionar
                add_cmd = masq_cmd.copy()
                add_cmd[5] = '-A'  # Trocar -C por -A
                
                add_result = subprocess.run(add_cmd, capture_output=True, text=True, timeout=10)
                
                if add_result.returncode != 0:
                    return False, f"Erro ao adicionar MASQUERADE: {add_result.stderr}"
            
            # Regra de FORWARD para permitir tráfego
            forward_cmd = [
                'sudo', 'iptables', '-C', 'FORWARD',
                '-s', network, '-o', self.interface, '-j', 'ACCEPT'
            ]
            
            check_forward = subprocess.run(forward_cmd, capture_output=True, text=True)
            
            if check_forward.returncode != 0:
                add_forward = forward_cmd.copy()
                add_forward[3] = '-A'
                
                forward_result = subprocess.run(add_forward, capture_output=True, text=True, timeout=10)
                
                if forward_result.returncode != 0:
                    return False, f"Erro ao adicionar FORWARD: {forward_result.stderr}"
            
            return True, "Regras de firewall configuradas"
            
        except Exception as e:
            return False, str(e)
    
    def _remove_firewall_rules(self, network: str) -> Tuple[bool, str]:
        """Remove regras de firewall para a rede"""
        try:
            errors = []
            
            # Remover MASQUERADE
            masq_cmd = [
                'sudo', 'iptables', '-t', 'nat', '-D', 'POSTROUTING',
                '-s', network, '-o', self.interface, '-j', 'MASQUERADE'
            ]
            
            masq_result = subprocess.run(masq_cmd, capture_output=True, text=True)
            if masq_result.returncode != 0 and "does not exist" not in masq_result.stderr:
                errors.append(f"MASQUERADE: {masq_result.stderr}")
            
            # Remover FORWARD
            forward_cmd = [
                'sudo', 'iptables', '-D', 'FORWARD',
                '-s', network, '-o', self.interface, '-j', 'ACCEPT'
            ]
            
            forward_result = subprocess.run(forward_cmd, capture_output=True, text=True)
            if forward_result.returncode != 0 and "does not exist" not in forward_result.stderr:
                errors.append(f"FORWARD: {forward_result.stderr}")
            
            if errors:
                return False, "; ".join(errors)
            
            return True, "Regras de firewall removidas"
            
        except Exception as e:
            return False, str(e)
    
    def apply_firewall_base_rules(self) -> Tuple[bool, str]:
        """Aplica regras básicas de firewall para funcionamento do gateway"""
        try:
            commands = [
                # Habilitar IP forwarding
                ['sudo', 'sysctl', '-w', 'net.ipv4.ip_forward=1'],
                
                # Permitir forward da VPN
                ['sudo', 'iptables', '-A', 'FORWARD', '-i', self.interface, '-j', 'ACCEPT'],
                ['sudo', 'iptables', '-A', 'FORWARD', '-o', self.interface, '-j', 'ACCEPT'],
                
                # NAT geral para VPN
                ['sudo', 'iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', self.interface, '-j', 'MASQUERADE']
            ]
            
            results = []
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        results.append(f"✓ {' '.join(cmd[2:])}")
                    else:
                        # Verificar se é erro por regra já existir
                        if "exist" in result.stderr.lower() or "duplicate" in result.stderr.lower():
                            results.append(f"○ {' '.join(cmd[2:])} (já existe)")
                        else:
                            results.append(f"✗ {' '.join(cmd[2:])}: {result.stderr.strip()}")
                
                except subprocess.TimeoutExpired:
                    results.append(f"✗ {' '.join(cmd[2:])}: Timeout")
                except Exception as e:
                    results.append(f"✗ {' '.join(cmd[2:])}: {str(e)}")
            
            return True, "\n".join(results)
            
        except Exception as e:
            return False, f"Erro ao aplicar regras básicas: {str(e)}"
    
    def get_system_routes(self) -> List[Dict]:
        """Obtém rotas ativas no sistema relacionadas à VPN"""
        try:
            result = subprocess.run(
                ['ip', 'route', 'show', 'dev', self.interface],
                capture_output=True, text=True, timeout=5
            )
            
            system_routes = []
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        # Parse básico da linha de rota
                        parts = line.split()
                        if parts:
                            network = parts[0] if '/' in parts[0] else f"{parts[0]}/32"
                            route_info = {
                                'network': network,
                                'raw_line': line.strip(),
                                'interface': self.interface
                            }
                            
                            # Extrair gateway se presente
                            if 'via' in parts:
                                via_index = parts.index('via')
                                if via_index + 1 < len(parts):
                                    route_info['gateway'] = parts[via_index + 1]
                            
                            system_routes.append(route_info)
            
            return system_routes
            
        except Exception as e:
            print(f"Erro ao obter rotas do sistema: {e}")
            return []
    
    def sync_with_system(self) -> Tuple[bool, str]:
        """Sincroniza configuração com rotas ativas no sistema"""
        try:
            system_routes = self.get_system_routes()
            gateway = self.get_vpn_gateway()
            
            if not gateway:
                return False, "Gateway VPN não detectado"
            
            applied = 0
            errors = []
            
            # Aplicar rotas habilitadas que não estão no sistema
            for route in self.get_active_routes():
                network = route['network']
                
                # Verificar se rota já existe no sistema
                exists = any(sr['network'] == network for sr in system_routes)
                
                if not exists:
                    result = self._add_system_route(network, gateway)
                    if result[0]:
                        applied += 1
                        route['last_sync'] = datetime.now().isoformat()
                    else:
                        errors.append(f"{network}: {result[1]}")
            
            # Salvar mudanças
            if applied > 0:
                self.save_routes()
            
            status_msg = f"Sincronizado: {applied} rotas aplicadas"
            if errors:
                status_msg += f". Erros: {len(errors)}"
                return False, status_msg
            
            return True, status_msg
            
        except Exception as e:
            return False, f"Erro na sincronização: {str(e)}"
    
    def get_statistics(self) -> Dict:
        """Obtém estatísticas das rotas"""
        total_routes = len(self.routes)
        active_routes = len(self.get_active_routes())
        system_routes = self.get_system_routes()
        
        # Verificar rotas em conflito ou faltando
        active_networks = {r['network'] for r in self.get_active_routes()}
        system_networks = {r['network'] for r in system_routes}
        
        missing_in_system = active_networks - system_networks
        extra_in_system = system_networks - active_networks
        
        return {
            'total_routes': total_routes,
            'active_routes': active_routes,
            'inactive_routes': total_routes - active_routes,
            'system_routes': len(system_routes),
            'missing_in_system': len(missing_in_system),
            'extra_in_system': len(extra_in_system),
            'vpn_gateway': self.get_vpn_gateway() or 'N/A',
            'vpn_interface': self.interface,
            'config_file': str(self.config_file)
        }