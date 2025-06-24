"""
World Model
Representasi data world dalam sistem
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class World:
    """Model untuk data world"""
    world_name: str
    owner_name: str
    bot_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'world_name': self.world_name,
            'owner_name': self.owner_name,
            'bot_name': self.bot_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'World':
        """Buat World dari dictionary"""
        return cls(
            world_name=data['world_name'],
            owner_name=data['owner_name'],
            bot_name=data['bot_name'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            is_active=data.get('is_active', True)
        )
