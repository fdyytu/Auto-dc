"""
Tenant Model untuk Sistem Multi-Tenant
Model untuk konfigurasi dan manajemen tenant
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json

class TenantStatus(Enum):
    """Status tenant"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    MAINTENANCE = "maintenance"

class SubscriptionPlan(Enum):
    """Plan subscription tenant"""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class Tenant:
    """Model untuk data tenant"""
    id: Optional[int] = None
    tenant_id: str = ""
    discord_id: str = ""
    guild_id: str = ""
    name: str = ""
    status: TenantStatus = TenantStatus.ACTIVE
    plan: SubscriptionPlan = SubscriptionPlan.BASIC
    features: Optional[Dict[str, Any]] = None
    channels: Optional[Dict[str, str]] = None
    permissions: Optional[Dict[str, bool]] = None
    bot_config: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = TenantStatus(self.status)
        if isinstance(self.plan, str):
            self.plan = SubscriptionPlan(self.plan)
        if self.features is None:
            self.features = self._get_default_features()
        if self.channels is None:
            self.channels = {}
        if self.permissions is None:
            self.permissions = self._get_default_permissions()
        if self.bot_config is None:
            self.bot_config = self._get_default_bot_config()
    
    def _get_default_features(self) -> Dict[str, Any]:
        """Dapatkan fitur default berdasarkan plan"""
        base_features = {
            "shop": True,
            "leveling": True,
            "reputation": True,
            "tickets": True,
            "automod": False,
            "live_stock": True,
            "admin_commands": True
        }
        
        if self.plan == SubscriptionPlan.PREMIUM:
            base_features.update({
                "automod": True,
                "custom_commands": True,
                "analytics": True
            })
        elif self.plan == SubscriptionPlan.ENTERPRISE:
            base_features.update({
                "automod": True,
                "custom_commands": True,
                "analytics": True,
                "api_access": True,
                "priority_support": True
            })
        
        return base_features
    
    def _get_default_permissions(self) -> Dict[str, bool]:
        """Dapatkan permissions default"""
        return {
            "manage_products": True,
            "manage_users": True,
            "view_analytics": self.plan != SubscriptionPlan.BASIC,
            "custom_config": self.plan == SubscriptionPlan.ENTERPRISE
        }
    
    def _get_default_bot_config(self) -> Dict[str, Any]:
        """Dapatkan konfigurasi bot default"""
        return {
            "prefix": "!",
            "language": "id",
            "timezone": "Asia/Jakarta",
            "auto_restart": True,
            "max_restart_attempts": 3
        }
