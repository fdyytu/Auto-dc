"""
Tenant Product Model untuk Isolasi Stock per Tenant
Model untuk produk dan stock yang terisolasi per tenant
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class TenantStockStatus(Enum):
    """Status stock tenant"""
    AVAILABLE = "available"
    SOLD = "sold"
    RESERVED = "reserved"
    DELETED = "deleted"

@dataclass
class TenantProduct:
    """Model untuk produk per tenant"""
    id: Optional[int] = None
    tenant_id: str = ""
    code: str = ""
    name: str = ""
    price: int = 0
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
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
            'id': self.id,
            'tenant_id': self.tenant_id,
            'code': self.code,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class TenantStock:
    """Model untuk stock per tenant"""
    id: Optional[int] = None
    tenant_id: str = ""
    product_code: str = ""
    content: str = ""
    status: TenantStockStatus = TenantStockStatus.AVAILABLE
    added_by: str = ""
    buyer_id: Optional[str] = None
    seller_id: Optional[str] = None
    purchase_price: Optional[int] = None
    added_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.added_at is None:
            self.added_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = TenantStockStatus(self.status)
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'product_code': self.product_code,
            'content': self.content,
            'status': self.status.value if isinstance(self.status, TenantStockStatus) else self.status,
            'added_by': self.added_by,
            'buyer_id': self.buyer_id,
            'seller_id': self.seller_id,
            'purchase_price': self.purchase_price,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
