"""
Subscription Model untuk Bot Rental System
Model untuk menangani langganan bot rental
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

class SubscriptionStatus(Enum):
    """Status langganan"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    SUSPENDED = "suspended"

class SubscriptionPlan(Enum):
    """Paket langganan"""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class Subscription:
    """Model untuk data langganan bot rental"""
    id: Optional[int] = None
    tenant_id: str = ""
    discord_id: str = ""
    plan: SubscriptionPlan = SubscriptionPlan.BASIC
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    bot_token: Optional[str] = None
    guild_id: Optional[str] = None
    features: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = SubscriptionStatus(self.status)
        if isinstance(self.plan, str):
            self.plan = SubscriptionPlan(self.plan)
        if self.features is None:
            self.features = self._get_default_features()
    
    def _get_default_features(self) -> dict:
        """Dapatkan fitur default berdasarkan plan"""
        features_map = {
            SubscriptionPlan.BASIC: {
                "max_commands": 50,
                "max_users": 100,
                "custom_prefix": False,
                "analytics": False,
                "priority_support": False
            },
            SubscriptionPlan.PREMIUM: {
                "max_commands": 200,
                "max_users": 500,
                "custom_prefix": True,
                "analytics": True,
                "priority_support": False
            },
            SubscriptionPlan.ENTERPRISE: {
                "max_commands": -1,  # unlimited
                "max_users": -1,     # unlimited
                "custom_prefix": True,
                "analytics": True,
                "priority_support": True
            }
        }
        return features_map.get(self.plan, features_map[SubscriptionPlan.BASIC])
    
    def is_active(self) -> bool:
        """Cek apakah langganan masih aktif"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        return True
    
    def days_remaining(self) -> int:
        """Hitung sisa hari langganan"""
        if not self.end_date:
            return -1
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    def extend_subscription(self, days: int):
        """Perpanjang langganan"""
        if self.end_date:
            self.end_date += timedelta(days=days)
        else:
            self.end_date = datetime.utcnow() + timedelta(days=days)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'discord_id': self.discord_id,
            'plan': self.plan.value if isinstance(self.plan, SubscriptionPlan) else self.plan,
            'status': self.status.value if isinstance(self.status, SubscriptionStatus) else self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'auto_renew': self.auto_renew,
            'bot_token': self.bot_token,
            'guild_id': self.guild_id,
            'features': self.features,
            'days_remaining': self.days_remaining(),
            'is_active': self.is_active(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Subscription':
        """Buat Subscription dari dictionary"""
        return cls(
            id=data.get('id'),
            tenant_id=data.get('tenant_id', ''),
            discord_id=data.get('discord_id', ''),
            plan=SubscriptionPlan(data.get('plan', 'basic')),
            status=SubscriptionStatus(data.get('status', 'pending')),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            auto_renew=data.get('auto_renew', True),
            bot_token=data.get('bot_token'),
            guild_id=data.get('guild_id'),
            features=data.get('features'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
