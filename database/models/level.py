"""
Level Model
Representasi data level dalam sistem
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Level:
    """Model untuk data level user"""
    user_id: str
    guild_id: str
    level: int = 0
    xp: int = 0
    total_xp: int = 0
    messages: int = 0
    last_message: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.last_message is None:
            self.last_message = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'user_id': self.user_id,
            'guild_id': self.guild_id,
            'level': self.level,
            'xp': self.xp,
            'total_xp': self.total_xp,
            'messages': self.messages,
            'last_message': self.last_message.isoformat() if self.last_message else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Level':
        """Buat Level dari dictionary"""
        return cls(
            user_id=data['user_id'],
            guild_id=data['guild_id'],
            level=data.get('level', 0),
            xp=data.get('xp', 0),
            total_xp=data.get('total_xp', 0),
            messages=data.get('messages', 0),
            last_message=datetime.fromisoformat(data['last_message']) if data.get('last_message') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )

@dataclass
class LevelReward:
    """Model untuk reward level"""
    guild_id: str
    level: int
    role_id: str
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'guild_id': self.guild_id,
            'level': self.level,
            'role_id': self.role_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LevelReward':
        """Buat LevelReward dari dictionary"""
        return cls(
            guild_id=data['guild_id'],
            level=data['level'],
            role_id=data['role_id'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )

@dataclass
class LevelSettings:
    """Model untuk pengaturan level"""
    guild_id: str
    enabled: bool = True
    announcement_channel: Optional[str] = None
    min_xp: int = 15
    max_xp: int = 25
    cooldown: int = 60
    stack_rewards: bool = True
    ignored_channels: str = ""
    ignored_roles: str = ""
    double_xp_roles: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'guild_id': self.guild_id,
            'enabled': self.enabled,
            'announcement_channel': self.announcement_channel,
            'min_xp': self.min_xp,
            'max_xp': self.max_xp,
            'cooldown': self.cooldown,
            'stack_rewards': self.stack_rewards,
            'ignored_channels': self.ignored_channels,
            'ignored_roles': self.ignored_roles,
            'double_xp_roles': self.double_xp_roles,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LevelSettings':
        """Buat LevelSettings dari dictionary"""
        return cls(
            guild_id=data['guild_id'],
            enabled=data.get('enabled', True),
            announcement_channel=data.get('announcement_channel'),
            min_xp=data.get('min_xp', 15),
            max_xp=data.get('max_xp', 25),
            cooldown=data.get('cooldown', 60),
            stack_rewards=data.get('stack_rewards', True),
            ignored_channels=data.get('ignored_channels', ''),
            ignored_roles=data.get('ignored_roles', ''),
            double_xp_roles=data.get('double_xp_roles', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
