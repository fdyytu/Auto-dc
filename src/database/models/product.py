"""
Product dan Stock Models
Representasi data produk dan stok dalam sistem
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class StockStatus(Enum):
    """Status stok"""
    AVAILABLE = "available"
    SOLD = "sold"
    DELETED = "deleted"

@dataclass
class Product:
    """Model untuk data produk"""
    code: str
    name: str
    price: int
    description: Optional[str] = None
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
            'code': self.code,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """Buat Product dari dictionary"""
        return cls(
            code=data['code'],
            name=data['name'],
            price=data['price'],
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )

@dataclass
class Stock:
    """Model untuk data stok"""
    id: Optional[int] = None
    product_code: str = ""
    content: str = ""
    status: StockStatus = StockStatus.AVAILABLE
    added_by: str = ""
    buyer_id: Optional[str] = None
    seller_id: Optional[str] = None
    added_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.added_at is None:
            self.added_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = StockStatus(self.status)
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'id': self.id,
            'product_code': self.product_code,
            'content': self.content,
            'status': self.status.value if isinstance(self.status, StockStatus) else self.status,
            'added_by': self.added_by,
            'buyer_id': self.buyer_id,
            'seller_id': self.seller_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Stock':
        """Buat Stock dari dictionary"""
        return cls(
            id=data.get('id'),
            product_code=data.get('product_code', ''),
            content=data.get('content', ''),
            status=StockStatus(data.get('status', 'available')),
            added_by=data.get('added_by', ''),
            buyer_id=data.get('buyer_id'),
            seller_id=data.get('seller_id'),
            added_at=datetime.fromisoformat(data['added_at']) if data.get('added_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
