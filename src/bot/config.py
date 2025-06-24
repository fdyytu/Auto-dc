"""
Configuration Manager
Menangani loading dan validasi konfigurasi bot
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manager untuk konfigurasi bot"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._required_keys = [
            'token', 'guild_id', 'admin_id', 'id_live_stock',
            'id_log_purch', 'id_donation_log', 'id_history_buy'
        ]
    
    def load_config(self) -> Dict[str, Any]:
        """Load dan validasi konfigurasi"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file tidak ditemukan: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            # Override token from environment variable if available
            env_token = os.getenv('DISCORD_TOKEN')
            if env_token:
                self._config['token'] = env_token
                logger.info("Token dimuat dari environment variable")
            
            self._validate_config()
            logger.info("Konfigurasi berhasil dimuat")
            return self._config
            
        except Exception as e:
            logger.error(f"Gagal memuat konfigurasi: {e}")
            raise
    
    def _validate_config(self) -> None:
        """Validasi konfigurasi yang diperlukan"""
        missing_keys = [key for key in self._required_keys if key not in self._config]
        if missing_keys:
            raise KeyError(f"Kunci konfigurasi yang hilang: {', '.join(missing_keys)}")
        
        # Validasi tipe data untuk keys utama
        int_keys = ['guild_id', 'admin_id', 'id_live_stock', 'id_log_purch', 
                   'id_donation_log', 'id_history_buy']
        
        for key in int_keys:
            if key in self._config:
                try:
                    self._config[key] = int(self._config[key])
                except (ValueError, TypeError):
                    raise ValueError(f"Konfigurasi {key} harus berupa integer")
        
        # Validasi dan konversi roles
        if 'roles' in self._config:
            roles = self._config['roles']
            for role_name, role_id in roles.items():
                try:
                    self._config['roles'][role_name] = int(role_id)
                except (ValueError, TypeError):
                    raise ValueError(f"Role {role_name} harus berupa integer")
        
        # Validasi dan konversi channels
        if 'channels' in self._config:
            channels = self._config['channels']
            for channel_name, channel_id in channels.items():
                try:
                    self._config['channels'][channel_name] = int(channel_id)
                except (ValueError, TypeError):
                    raise ValueError(f"Channel {channel_name} harus berupa integer")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Ambil nilai konfigurasi"""
        return self._config.get(key, default)
    
    def get_channels(self) -> Dict[str, int]:
        """Ambil konfigurasi channel"""
        return self._config.get('channels', {})
    
    def get_roles(self) -> Dict[str, int]:
        """Ambil konfigurasi role"""
        return self._config.get('roles', {})
    
    def get_cooldowns(self) -> Dict[str, int]:
        """Ambil konfigurasi cooldown"""
        return self._config.get('cooldowns', {})
    
    def get_permissions(self) -> Dict[str, List[str]]:
        """Ambil konfigurasi permission"""
        return self._config.get('permissions', {})
    
    def get_automod(self) -> Dict[str, Any]:
        """Ambil konfigurasi automod"""
        return self._config.get('automod', {})

# Instance global
config_manager = ConfigManager()
