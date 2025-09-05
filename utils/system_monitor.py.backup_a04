import psutil
import platform
import socket
import datetime
import os
import subprocess

def get_detailed_system_info():
    """Get comprehensive system information"""
    info = {
        'system': get_system_info(),
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'disk': get_disk_info(),
        'network': get_network_info(),
        'processes': get_process_info()
    }
    
    return info

def get_system_info():
    """Get basic system information"""
    try:
        return {
            'hostname': socket.gethostname(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()),
            'uptime': datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time()),
            'timezone': str(datetime.datetime.now().astimezone().tzinfo),
            'user': os.getenv('USER', 'unknown')
        }
    except Exception as e:
        return {'error': str(e)}

def get_cpu_info():
    """Get detailed CPU information"""
    try:
        cpu_freq = psutil.cpu_freq()
        
        return {
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'base_frequency': cpu_freq.current if cpu_freq else 0,
            'current_frequency': cpu_freq.current if cpu_freq else 0,
            'max_frequency': cpu_freq.max if cpu_freq else 0,
            'min_frequency': cpu_freq.min if cpu_freq else 0,
            'usage_percent': psutil.cpu_percent(interval=1),
            'usage_per_core': psutil.cpu_percent(interval=1, percpu=True),
            'model': get_cpu_model(),
            'architecture': platform.machine(),
            'cache_info': get_cpu_cache_info()
        }
    except Exception as e:
        return {'error': str(e)}

def get_cpu_model():
    """Get CPU model information"""
    try:
        if platform.system() == "Linux":
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        return line.split(':')[1].strip()
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        elif platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(key, "ProcessorNameString")[0]
    except Exception:
        pass
    
    return platform.processor() or "Unknown"

def get_cpu_cache_info():
    """Get CPU cache information (Linux only)"""
    cache_info = {}
    try:
        if platform.system() == "Linux":
            cache_path = "/sys/devices/system/cpu/cpu0/cache"
            if os.path.exists(cache_path):
                for cache_dir in os.listdir(cache_path):
                    index_path = os.path.join(cache_path, cache_dir)
                    if os.path.isdir(index_path):
                        try:
                            with open(os.path.join(index_path, 'level'), 'r') as f:
                                level = f.read().strip()
                            with open(os.path.join(index_path, 'size'), 'r') as f:
                                size = f.read().strip()
                            with open(os.path.join(index_path, 'type'), 'r') as f:
                                cache_type = f.read().strip()
                            
                            cache_info[f"L{level} {cache_type}"] = size
                        except Exception:
                            continue
    except Exception:
        pass
    
    return cache_info

def get_memory_info():
    """Get detailed memory information"""
    try:
        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'virtual': {
                'total': virtual.total,
                'available': virtual.available,
                'used': virtual.used,
                'free': virtual.free,
                'percent': virtual.percent,
                'active': getattr(virtual, 'active', 0),
                'inactive': getattr(virtual, 'inactive', 0),
                'buffers': getattr(virtual, 'buffers', 0),
                'cached': getattr(virtual, 'cached', 0),
                'shared': getattr(virtual, 'shared', 0)
            },
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'free': swap.free,
                'percent': swap.percent,
                'sin': swap.sin,
                'sout': swap.sout
            },
            'memory_type': get_memory_type()
        }
    except Exception as e:
        return {'error': str(e)}

def get_memory_type():
    """Get memory type information (Linux only)"""
    try:
        if platform.system() == "Linux":
            result = subprocess.run(['dmidecode', '--type', 'memory'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse dmidecode output for memory type
                for line in result.stdout.split('\n'):
                    if 'Type:' in line and 'Unknown' not in line:
                        return line.split(':')[1].strip()
    except Exception:
        pass
    
    return "Unknown"

def get_disk_info():
    """Get detailed disk information"""
    try:
        disk_info = {
            'partitions': [],
            'usage': {},
            'io_stats': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
        }
        
        # Get partition information
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partition_info = {
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': (usage.used / usage.total) * 100
                }
                disk_info['partitions'].append(partition_info)
                disk_info['usage'][partition.mountpoint] = usage._asdict()
            
            except PermissionError:
                continue
        
        return disk_info
    
    except Exception as e:
        return {'error': str(e)}

def get_network_info():
    """Get detailed network information"""
    try:
        network_info = {
            'interfaces': {},
            'stats': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
            'connections': [],
            'interface_stats': {}
        }
        
        # Get network interfaces
        for interface, addresses in psutil.net_if_addrs().items():
            network_info['interfaces'][interface] = [addr._asdict() for addr in addresses]
        
        # Get interface statistics
        for interface, stats in psutil.net_if_stats().items():
            network_info['interface_stats'][interface] = stats._asdict()
        
        # Get active connections (limited to first 20 for performance)
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections[:20]:
                if conn.status == 'ESTABLISHED':
                    network_info['connections'].append({
                        'fd': conn.fd,
                        'family': conn.family,
                        'type': conn.type,
                        'local_addr': conn.laddr._asdict() if conn.laddr else None,
                        'remote_addr': conn.raddr._asdict() if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid
                    })
        except Exception:
            pass
        
        return network_info
    
    except Exception as e:
        return {'error': str(e)}

def get_process_info(limit=20):
    """Get information about running processes"""
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                       'create_time', 'status', 'username']):
            try:
                pinfo = proc.info
                pinfo['create_time'] = datetime.datetime.fromtimestamp(pinfo['create_time'])
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage and limit results
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        return {
            'total_processes': len(psutil.pids()),
            'top_processes': processes[:limit],
            'process_count_by_status': get_process_count_by_status()
        }
    
    except Exception as e:
        return {'error': str(e)}

def get_process_count_by_status():
    """Get count of processes by status"""
    status_count = {}
    try:
        for proc in psutil.process_iter(['status']):
            try:
                status = proc.info['status']
                status_count[status] = status_count.get(status, 0) + 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    
    return status_count

def get_system_load():
    """Get system load averages (Unix only)"""
    try:
        if hasattr(os, 'getloadavg'):
            load1, load5, load15 = os.getloadavg()
            return {
                '1_minute': load1,
                '5_minute': load5,
                '15_minute': load15
            }
    except (AttributeError, OSError):
        pass
    
    return {}

def get_temperature_sensors():
    """Get temperature sensor readings"""
    try:
        if hasattr(psutil, 'sensors_temperatures'):
            temps = psutil.sensors_temperatures()
            temperature_info = {}
            
            for name, entries in temps.items():
                temperature_info[name] = []
                for entry in entries:
                    temperature_info[name].append({
                        'label': entry.label or name,
                        'current': entry.current,
                        'high': entry.high,
                        'critical': entry.critical
                    })
            
            return temperature_info
    except (AttributeError, Exception):
        pass
    
    return {}

def get_battery_info():
    """Get battery information (for laptops)"""
    try:
        if hasattr(psutil, 'sensors_battery'):
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'percent': battery.percent,
                    'secsleft': battery.secsleft,
                    'power_plugged': battery.power_plugged
                }
    except (AttributeError, Exception):
        pass
    
    return {}

def get_users_info():
    """Get information about logged in users"""
    try:
        users = []
        for user in psutil.users():
            users.append({
                'name': user.name,
                'terminal': user.terminal,
                'host': user.host,
                'started': datetime.datetime.fromtimestamp(user.started) if user.started else None,
                'pid': user.pid
            })
        
        return users
    except Exception as e:
        return {'error': str(e)}

def monitor_system_realtime(duration=60, interval=1):
    """Monitor system metrics in real-time"""
    metrics_history = {
        'timestamps': [],
        'cpu_percent': [],
        'memory_percent': [],
        'disk_io': [],
        'network_io': []
    }
    
    start_time = datetime.datetime.now()
    
    try:
        while (datetime.datetime.now() - start_time).seconds < duration:
            timestamp = datetime.datetime.now()
            
            # Collect metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_rate = disk_io.read_bytes + disk_io.write_bytes if disk_io else 0
            
            # Network I/O
            net_io = psutil.net_io_counters()
            net_io_rate = net_io.bytes_sent + net_io.bytes_recv if net_io else 0
            
            # Store metrics
            metrics_history['timestamps'].append(timestamp)
            metrics_history['cpu_percent'].append(cpu_percent)
            metrics_history['memory_percent'].append(memory_percent)
            metrics_history['disk_io'].append(disk_io_rate)
            metrics_history['network_io'].append(net_io_rate)
            
            # Wait for next interval
            import time
            time.sleep(interval)
    
    except KeyboardInterrupt:
        pass
    
    return metrics_history

def get_system_health_score():
    """Calculate a system health score based on various metrics"""
    try:
        score = 100  # Start with perfect score
        
        # CPU usage penalty
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            score -= 30
        elif cpu_percent > 70:
            score -= 15
        elif cpu_percent > 50:
            score -= 5
        
        # Memory usage penalty
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 95:
            score -= 25
        elif memory_percent > 85:
            score -= 15
        elif memory_percent > 70:
            score -= 5
        
        # Disk usage penalty
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_percent = (usage.used / usage.total) * 100
                if disk_percent > 95:
                    score -= 20
                elif disk_percent > 85:
                    score -= 10
                elif disk_percent > 75:
                    score -= 5
            except PermissionError:
                continue
        
        # Load average penalty (Unix only)
        try:
            if hasattr(os, 'getloadavg'):
                load1, _, _ = os.getloadavg()
                cpu_count = psutil.cpu_count()
                if load1 > cpu_count * 2:
                    score -= 15
                elif load1 > cpu_count:
                    score -= 8
        except (AttributeError, OSError):
            pass
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        return {
            'score': score,
            'status': get_health_status(score),
            'recommendations': get_health_recommendations(score)
        }
    
    except Exception as e:
        return {'error': str(e), 'score': 0, 'status': 'Unknown'}

def get_health_status(score):
    """Get health status based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Fair"
    elif score >= 50:
        return "Poor"
    else:
        return "Critical"

def get_health_recommendations(score):
    """Get health recommendations based on score"""
    recommendations = []
    
    if score < 90:
        # Check specific issues
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 70:
            recommendations.append("High CPU usage detected. Consider closing unnecessary applications.")
        
        if memory_percent > 80:
            recommendations.append("High memory usage detected. Consider freeing up RAM.")
        
        # Check disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_percent = (usage.used / usage.total) * 100
                if disk_percent > 80:
                    recommendations.append(f"High disk usage on {partition.mountpoint}. Consider cleaning up files.")
            except PermissionError:
                continue
    
    if not recommendations:
        recommendations.append("System is running well. No immediate action required.")
    
    return recommendations