"""
Bot Instance Model untuk Bot Rental System
Model untuk menangani instance bot per tenant
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class BotStatus(Enum):
    """Status bot instance"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class BotInstance:
    """Model untuk data bot instance"""
    id: Optional[int] = None
    tenant_id: str = ""
    bot_token: str = ""
    guild_id: str = ""
    status: BotStatus = BotStatus.STOPPED
    process_id: Optional[int] = None
    port: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    last_heartbeat: Optional[datetime] = None
    error_message: Optional[str] = None
    restart_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = BotStatus(self.status)
        if self.config is None:
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Dapatkan konfigurasi default bot"""
        return {
            "prefix": "!",
            "features": {
                "moderation": True,
                "music": False,
                "economy": True,
                "leveling": True,
                "tickets": True
            },
            "auto_restart": True,
            "max_restart_attempts": 3
        }
    
    def is_running(self) -> bool:
        """Cek apakah bot sedang berjalan"""
        return self.status == BotStatus.RUNNING
    
    def update_heartbeat(self):
        """Update heartbeat terakhir"""
        self.last_heartbeat = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_restart_count(self):
        """Increment restart counter"""
        self.restart_count += 1
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'bot_token': self.bot_token,
            'guild_id': self.guild_id,
            'status': self.status.value if isinstance(self.status, BotStatus) else self.status,
            'process_id': self.process_id,
            'port': self.port,
            'config': self.config,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'error_message': self.error_message,
            'restart_count': self.restart_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BotInstance':
        """Buat BotInstance dari dictionary"""
        return cls(
            id=data.get('id'),
            tenant_id=data.get('tenant_id', ''),
            bot_token=data.get('bot_token', ''),
            guild_id=data.get('guild_id', ''),
            status=BotStatus(data.get('status', 'stopped')),
            process_id=data.get('process_id'),
            port=data.get('port'),
            config=data.get('config'),
            last_heartbeat=datetime.fromisoformat(data['last_heartbeat']) if data.get('last_heartbeat') else None,
            error_message=data.get('error_message'),
            restart_count=data.get('restart_count', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
