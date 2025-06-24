"""
User Model
Representasi data user dalam sistem
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """Model untuk data user"""
    growid: str
    balance_wl: int = 0
    balance_dl: int = 0
    balance_bgl: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def total_wl(self) -> int:
        """Convert semua balance ke WL"""
        return self.balance_wl + (self.balance_dl * 100) + (self.balance_bgl * 10000)
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'growid': self.growid,
            'balance_wl': self.balance_wl,
            'balance_dl': self.balance_dl,
            'balance_bgl': self.balance_bgl,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Buat User dari dictionary"""
        return cls(
            growid=data['growid'],
            balance_wl=data.get('balance_wl', 0),
            balance_dl=data.get('balance_dl', 0),
            balance_bgl=data.get('balance_bgl', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )

@dataclass
class UserGrowID:
    """Model untuk mapping Discord ID ke GrowID"""
    discord_id: str
    growid: str
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            'discord_id': self.discord_id,
            'growid': self.growid,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserGrowID':
        return cls(
            discord_id=data['discord_id'],
            growid=data['growid'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )
