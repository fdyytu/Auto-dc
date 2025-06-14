"""
Transaction Model
Representasi data transaksi dalam sistem
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class TransactionStatus(Enum):
    """Status transaksi"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class TransactionType(Enum):
    """Tipe transaksi"""
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

@dataclass
class Transaction:
    """Model untuk data transaksi"""
    id: Optional[int] = None
    buyer_id: str = ""
    seller_id: Optional[str] = None
    product_code: Optional[str] = None
    quantity: int = 1
    total_price: int = 0
    transaction_type: TransactionType = TransactionType.PURCHASE
    status: TransactionStatus = TransactionStatus.PENDING
    details: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = TransactionStatus(self.status)
        if isinstance(self.transaction_type, str):
            self.transaction_type = TransactionType(self.transaction_type)
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'id': self.id,
            'buyer_id': self.buyer_id,
            'seller_id': self.seller_id,
            'product_code': self.product_code,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'transaction_type': self.transaction_type.value if isinstance(self.transaction_type, TransactionType) else self.transaction_type,
            'status': self.status.value if isinstance(self.status, TransactionStatus) else self.status,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Buat Transaction dari dictionary"""
        return cls(
            id=data.get('id'),
            buyer_id=data.get('buyer_id', ''),
            seller_id=data.get('seller_id'),
            product_code=data.get('product_code'),
            quantity=data.get('quantity', 1),
            total_price=data.get('total_price', 0),
            transaction_type=TransactionType(data.get('transaction_type', 'purchase')),
            status=TransactionStatus(data.get('status', 'pending')),
            details=data.get('details'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
