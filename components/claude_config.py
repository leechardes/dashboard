"""
Claude Configuration Component
Responsável por gerenciar configurações do Claude Manager.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any
import copy

# Configurar logging
logger = logging.getLogger(__name__)

class ClaudeConfig:
    """Classe para gerenciar configurações do Claude Manager"""
    
    def __init__(self):
        self.config_file = "/srv/projects/shared/dashboard/config/claude_limits.json"
        self.config_dir = os.path.dirname(self.config_file)
        self._ensure_config_dir()
        self.config = self._load_or_create_default_config()
    
    def _ensure_config_dir(self):
        """Garante que o diretório de configuração existe"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Erro ao criar diretório de configuração: {e}")
    
    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "global_settings": {
                "default_memory_limit_mb": 8192,
                "max_process_age_hours": 24,
                "auto_cleanup_enabled": False,
                "auto_cleanup_interval_minutes": 60,
                "orphan_cleanup_enabled": False,
                "alert_memory_threshold_mb": 6144,
                "alert_cpu_threshold_percent": 80,
                "max_processes_per_user": 10,
                "enable_notifications": True,
                "log_retention_days": 7,
                "alert_instead_of_kill": True,
                "send_terminal_alerts": True
            },
            "user_limits": {
                "default": {
                    "memory_limit_mb": 8192,
                    "max_processes": 5,
                    "max_runtime_hours": 24,
                    "priority": "normal",
                    "alert_on_long_running": True,
                    "alert_after_hours": 4
                }
            },
            "monitoring": {
                "refresh_interval_seconds": 5,
                "history_retention_hours": 24,
                "enable_metrics_collection": True,
                "alert_on_memory_spike": True,
                "alert_on_orphan_process": True
            },
            "security": {
                "require_confirmation_for_kill_all": True,
                "require_confirmation_for_user_kill": True,
                "enable_action_logging": True,
                "restrict_user_access": False,
                "allowed_users": []
            },
            "ui": {
                "theme": "light",
                "auto_refresh_enabled": True,
                "show_advanced_metrics": True,
                "items_per_page": 50,
                "default_sort": "memory_desc"
            }
        }
    
    def _load_or_create_default_config(self) -> Dict:
        """Carrega configuração existente ou cria uma padrão"""
        try:
            if os.path.exists(self.config_file):
                return self.load_config()
            else:
                default_config = self._get_default_config()
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Erro ao carregar/criar configuração: {e}")
            return self._get_default_config()
    
    def load_config(self) -> Dict:
        """Carrega configuração do arquivo JSON"""
        try:
            if not os.path.exists(self.config_file):
                logger.info("Arquivo de configuração não existe, criando padrão")
                default_config = self._get_default_config()
                self.save_config(default_config)
                return default_config
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validar e mesclar com configuração padrão se necessário
            config = self._validate_and_merge_config(config)
            
            logger.info("Configuração carregada com sucesso")
            return config
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            logger.info("Retornando configuração padrão")
            return self._get_default_config()
    
    def save_config(self, config: Dict) -> bool:
        """Salva configuração no arquivo JSON"""
        try:
            self._ensure_config_dir()
            
            # Atualizar timestamp de última modificação
            config = copy.deepcopy(config)
            config["last_updated"] = datetime.now().isoformat()
            
            # Criar backup da configuração existente se existir
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                try:
                    with open(self.config_file, 'r') as src, open(backup_file, 'w') as dst:
                        dst.write(src.read())
                except:
                    pass  # Falha no backup não deve impedir salvar nova config
            
            # Salvar nova configuração
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.config = config
            logger.info("Configuração salva com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            return False
    
    def _validate_and_merge_config(self, loaded_config: Dict) -> Dict:
        """Valida configuração carregada e mescla com padrões se necessário"""
        try:
            default_config = self._get_default_config()
            
            # Função recursiva para mesclar configurações
            def merge_configs(default: Dict, loaded: Dict) -> Dict:
                result = copy.deepcopy(default)
                
                for key, value in loaded.items():
                    if key in result:
                        if isinstance(value, dict) and isinstance(result[key], dict):
                            result[key] = merge_configs(result[key], value)
                        else:
                            result[key] = value
                    else:
                        # Permitir novas chaves que não estão no padrão
                        result[key] = value
                
                return result
            
            merged_config = merge_configs(default_config, loaded_config)
            
            # Validações específicas
            self._validate_config_values(merged_config)
            
            return merged_config
            
        except Exception as e:
            logger.error(f"Erro na validação da configuração: {e}")
            return self._get_default_config()
    
    def _validate_config_values(self, config: Dict):
        """Valida valores específicos da configuração"""
        try:
            # Validar valores numéricos
            global_settings = config.get("global_settings", {})
            
            # Garantir valores mínimos
            if global_settings.get("default_memory_limit_mb", 0) < 64:
                global_settings["default_memory_limit_mb"] = 64
                
            if global_settings.get("max_process_age_hours", 0) < 1:
                global_settings["max_process_age_hours"] = 1
                
            if global_settings.get("auto_cleanup_interval_minutes", 0) < 5:
                global_settings["auto_cleanup_interval_minutes"] = 5
            
            # Validar configurações de monitoramento
            monitoring = config.get("monitoring", {})
            if monitoring.get("refresh_interval_seconds", 0) < 1:
                monitoring["refresh_interval_seconds"] = 1
                
        except Exception as e:
            logger.error(f"Erro na validação de valores: {e}")
    
    def get_user_limit(self, username: str) -> Dict:
        """Retorna configurações de limite para um usuário específico"""
        try:
            user_limits = self.config.get("user_limits", {})
            
            # Se usuário tem configuração específica, retornar ela
            if username in user_limits:
                return user_limits[username]
            
            # Senão, retornar configuração padrão
            return user_limits.get("default", {
                "memory_limit_mb": 8192,
                "max_processes": 5,
                "max_runtime_hours": 24,
                "priority": "normal",
                "alert_on_long_running": True,
                "alert_after_hours": 4
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter limite do usuário {username}: {e}")
            return {"memory_limit_mb": 8192, "max_processes": 5, "max_runtime_hours": 24, "priority": "normal"}
    
    def set_user_limit(self, username: str, memory_mb: int, max_processes: int = None, 
                       max_runtime_hours: int = None, priority: str = "normal") -> bool:
        """Define limite de recursos para um usuário"""
        try:
            if "user_limits" not in self.config:
                self.config["user_limits"] = {}
            
            # Obter configuração atual do usuário ou padrão
            current_config = self.get_user_limit(username)
            
            # Atualizar apenas os valores fornecidos
            new_config = {
                "memory_limit_mb": max(64, memory_mb),  # Mínimo 64MB
                "max_processes": max_processes if max_processes is not None else current_config.get("max_processes", 5),
                "max_runtime_hours": max_runtime_hours if max_runtime_hours is not None else current_config.get("max_runtime_hours", 4),
                "priority": priority if priority in ["low", "normal", "high"] else "normal"
            }
            
            self.config["user_limits"][username] = new_config
            
            success = self.save_config(self.config)
            if success:
                logger.info(f"Limite atualizado para usuário {username}: {new_config}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao definir limite para usuário {username}: {e}")
            return False
    
    def remove_user_limit(self, username: str) -> bool:
        """Remove configuração específica de um usuário (volta ao padrão)"""
        try:
            if username == "default":
                return False  # Não pode remover configuração padrão
            
            user_limits = self.config.get("user_limits", {})
            if username in user_limits:
                del user_limits[username]
                success = self.save_config(self.config)
                if success:
                    logger.info(f"Configuração removida para usuário {username}")
                return success
            
            return True  # Usuário já não tinha configuração específica
            
        except Exception as e:
            logger.error(f"Erro ao remover configuração do usuário {username}: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reseta todas as configurações para o padrão, mantendo apenas default"""
        try:
            # Pegar configuração default atual
            default_config = self.config.get("user_limits", {}).get("default", {})
            
            # Criar nova configuração apenas com default
            self.config = self._get_default_config()
            
            # Preservar configuração default se existir
            if default_config:
                self.config["user_limits"]["default"] = default_config
            
            # Salvar
            success = self.save_config(self.config)
            if success:
                logger.info("Configurações resetadas para padrão")
            return success
            
        except Exception as e:
            logger.error(f"Erro ao resetar configurações: {e}")
            return False
    
    def get_global_setting(self, setting_name: str) -> Any:
        """Retorna valor de uma configuração global"""
        try:
            return self.config.get("global_settings", {}).get(setting_name)
        except Exception as e:
            logger.error(f"Erro ao obter configuração global {setting_name}: {e}")
            return None
    
    def set_global_setting(self, setting_name: str, value: Any) -> bool:
        """Define valor de uma configuração global"""
        try:
            if "global_settings" not in self.config:
                self.config["global_settings"] = {}
            
            self.config["global_settings"][setting_name] = value
            success = self.save_config(self.config)
            
            if success:
                logger.info(f"Configuração global atualizada - {setting_name}: {value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao definir configuração global {setting_name}: {e}")
            return False
    
    def get_all_user_limits(self) -> Dict:
        """Retorna todas as configurações de usuários"""
        return self.config.get("user_limits", {})
    
    def get_monitoring_config(self) -> Dict:
        """Retorna configurações de monitoramento"""
        return self.config.get("monitoring", {})
    
    def get_security_config(self) -> Dict:
        """Retorna configurações de segurança"""
        return self.config.get("security", {})
    
    def get_ui_config(self) -> Dict:
        """Retorna configurações de interface"""
        return self.config.get("ui", {})
    
    def export_config(self) -> str:
        """Exporta configuração como JSON string"""
        try:
            return json.dumps(self.config, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao exportar configuração: {e}")
            return "{}"
    
    def import_config(self, config_json: str) -> bool:
        """Importa configuração de JSON string"""
        try:
            imported_config = json.loads(config_json)
            validated_config = self._validate_and_merge_config(imported_config)
            success = self.save_config(validated_config)
            
            if success:
                logger.info("Configuração importada com sucesso")
            
            return success
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON de configuração: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao importar configuração: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """Reseta configuração para valores padrão"""
        try:
            default_config = self._get_default_config()
            success = self.save_config(default_config)
            
            if success:
                logger.info("Configuração resetada para padrão")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao resetar configuração: {e}")
            return False
    
    def backup_config(self, backup_path: Optional[str] = None) -> bool:
        """Cria backup da configuração atual"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.config_file}.backup_{timestamp}"
            
            with open(self.config_file, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            
            logger.info(f"Backup criado: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return False

# Instância global da configuração
claude_config = ClaudeConfig()