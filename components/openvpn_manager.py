import subprocess
import psutil
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

class OpenVPNManager:
    """Gerenciador do serviço OpenVPN Client para gateway centralizado"""
    
    def __init__(self):
        self.service_name = "openvpn@client"
        self.interface = "tun0"
        self.config_file = Path("/srv/projects/shared/dashboard/config/openvpn_settings.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self.load_settings()
        
    def load_settings(self):
        """Carrega configurações salvas"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {
                "service_name": "openvpn@client",
                "interface": "tun0",
                "auto_start": True,
                "monitor_interval": 30
            }
            self.save_settings()
    
    def save_settings(self):
        """Salva configurações"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
        
    def get_status(self):
        """Verifica status da conexão VPN"""
        try:
            # Verificar se o serviço está ativo
            result = subprocess.run(
                ['systemctl', 'is-active', self.service_name],
                capture_output=True, text=True
            )
            
            if result.stdout.strip() == 'active':
                # Verificar se a interface existe e tem IP
                if self.interface in psutil.net_if_addrs():
                    vpn_ip = self.get_vpn_ip()
                    if vpn_ip and vpn_ip != "N/A":
                        return "connected"
                    else:
                        return "connecting"
                else:
                    return "starting"
            elif result.stdout.strip() == 'inactive':
                return "stopped"
            elif result.stdout.strip() == 'failed':
                return "error"
            else:
                return "unknown"
        except Exception as e:
            print(f"Erro ao verificar status: {e}")
            return "error"
    
    def get_vpn_ip(self):
        """Obtém IP da interface VPN"""
        try:
            addrs = psutil.net_if_addrs()
            if self.interface in addrs:
                for addr in addrs[self.interface]:
                    if addr.family == 2:  # IPv4
                        return addr.address
        except Exception as e:
            print(f"Erro ao obter IP VPN: {e}")
        return "N/A"
    
    def get_public_ip(self):
        """Obtém IP público através da VPN"""
        try:
            result = subprocess.run(
                ['curl', '-s', '--max-time', '5', 'ifconfig.me'],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        return "N/A"
    
    def start(self):
        """Inicia serviço OpenVPN"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', self.service_name],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Erro ao iniciar VPN: {e}")
            return False
    
    def stop(self):
        """Para serviço OpenVPN"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', self.service_name],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Erro ao parar VPN: {e}")
            return False
    
    def restart(self):
        """Reinicia serviço OpenVPN"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', self.service_name],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Erro ao reiniciar VPN: {e}")
            return False
    
    def get_uptime(self):
        """Obtém tempo de conexão"""
        try:
            result = subprocess.run(
                ['systemctl', 'show', self.service_name, '-p', 'ActiveEnterTimestamp'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Parse do timestamp: ActiveEnterTimestamp=Wed 2024-09-06 10:30:00 UTC
                timestamp_line = result.stdout.strip()
                if "=" in timestamp_line:
                    timestamp_str = timestamp_line.split("=")[1].strip()
                    if timestamp_str and timestamp_str != "0":
                        try:
                            # Tentar diferentes formatos de data
                            for fmt in ["%a %Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"]:
                                try:
                                    start_time = datetime.strptime(timestamp_str, fmt)
                                    uptime = datetime.now() - start_time
                                    
                                    # Formatar uptime
                                    days = uptime.days
                                    hours, remainder = divmod(uptime.seconds, 3600)
                                    minutes, _ = divmod(remainder, 60)
                                    
                                    if days > 0:
                                        return f"{days}d {hours}h {minutes}m"
                                    elif hours > 0:
                                        return f"{hours}h {minutes}m"
                                    else:
                                        return f"{minutes}m"
                                except ValueError:
                                    continue
                        except:
                            pass
        except Exception as e:
            print(f"Erro ao obter uptime: {e}")
        
        return "N/A"
    
    def get_statistics(self):
        """Obtém estatísticas da interface VPN"""
        try:
            stats = psutil.net_io_counters(pernic=True).get(self.interface)
            if stats:
                return {
                    'tx_bytes': f"{stats.bytes_sent / (1024**2):.1f} MB",
                    'rx_bytes': f"{stats.bytes_recv / (1024**2):.1f} MB",
                    'tx_packets': f"{stats.packets_sent:,}",
                    'rx_packets': f"{stats.packets_recv:,}",
                    'tx_errors': stats.errin,
                    'rx_errors': stats.errout
                }
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
        
        return {
            'tx_bytes': '0 MB', 'rx_bytes': '0 MB', 
            'tx_packets': '0', 'rx_packets': '0',
            'tx_errors': 0, 'rx_errors': 0
        }
    
    def get_speed(self):
        """Obtém velocidade e latência da conexão"""
        try:
            # Teste de velocidade simples com ping
            ping_result = subprocess.run(
                ['ping', '-c', '4', '8.8.8.8'],
                capture_output=True, text=True
            )
            
            if ping_result.returncode == 0:
                # Parse do resultado do ping
                lines = ping_result.stdout.split('\n')
                stats_line = [line for line in lines if 'packet loss' in line]
                if stats_line:
                    loss_match = re.search(r'(\d+)% packet loss', stats_line[0])
                    loss = loss_match.group(1) if loss_match else "0"
                else:
                    loss = "0"
                
                # Parse da latência
                rtt_line = [line for line in lines if 'rtt' in line or 'round-trip' in line]
                if rtt_line:
                    avg_match = re.search(r'avg = ([\d.]+)', rtt_line[0]) or re.search(r'avg/([\d.]+)', rtt_line[0])
                    latency = f"{avg_match.group(1)}" if avg_match else "N/A"
                else:
                    latency = "N/A"
            else:
                loss = "100"
                latency = "N/A"
            
            return {
                'download': 'N/A',  # Teste de velocidade completo requer ferramenta externa
                'upload': 'N/A',
                'latency': latency,
                'loss': loss
            }
        except Exception as e:
            print(f"Erro ao obter velocidade: {e}")
            return {
                'download': 'N/A', 'upload': 'N/A',
                'latency': 'N/A', 'loss': 'N/A'
            }
    
    def get_logs(self, lines=50):
        """Obtém logs do OpenVPN"""
        try:
            result = subprocess.run(
                ['sudo', 'journalctl', '-u', self.service_name, '-n', str(lines), '--no-pager'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Erro ao obter logs: {result.stderr}"
        except Exception as e:
            return f"Erro ao obter logs: {e}"
    
    def get_connection_info(self):
        """Obtém informações detalhadas da conexão"""
        try:
            info = {
                'status': self.get_status(),
                'local_ip': self.get_vpn_ip(),
                'public_ip': self.get_public_ip(),
                'uptime': self.get_uptime(),
                'interface': self.interface,
                'service': self.service_name
            }
            
            # Adicionar informações da interface se existir
            if self.interface in psutil.net_if_addrs():
                addrs = psutil.net_if_addrs()[self.interface]
                for addr in addrs:
                    if addr.family == 2:  # IPv4
                        info['netmask'] = addr.netmask
                        info['broadcast'] = addr.broadcast
                        break
            
            return info
        except Exception as e:
            print(f"Erro ao obter informações da conexão: {e}")
            return {}
    
    def enable_autostart(self):
        """Habilita início automático do serviço"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'enable', self.service_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self.settings['auto_start'] = True
                self.save_settings()
                return True
        except Exception as e:
            print(f"Erro ao habilitar autostart: {e}")
        return False
    
    def disable_autostart(self):
        """Desabilita início automático do serviço"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'disable', self.service_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self.settings['auto_start'] = False
                self.save_settings()
                return True
        except Exception as e:
            print(f"Erro ao desabilitar autostart: {e}")
        return False
    
    def is_autostart_enabled(self):
        """Verifica se o autostart está habilitado"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-enabled', self.service_name],
                capture_output=True, text=True
            )
            return result.stdout.strip() == 'enabled'
        except:
            return False