"""
Payment Model untuk Bot Rental System
Model untuk menangani transaksi pembayaran
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class PaymentStatus(Enum):
    """Status pembayaran"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    """Metode pembayaran"""
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"

@dataclass
class Payment:
    """Model untuk data pembayaran"""
    id: Optional[int] = None
    tenant_id: str = ""
    discord_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    method: PaymentMethod = PaymentMethod.CREDIT_CARD
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str] = None
    gateway_response: Optional[dict] = None
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = PaymentStatus(self.status)
        if isinstance(self.method, str):
            self.method = PaymentMethod(self.method)
    
    def is_completed(self) -> bool:
        """Cek apakah pembayaran sudah selesai"""
        return self.status == PaymentStatus.COMPLETED
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'discord_id': self.discord_id,
            'amount': self.amount,
            'currency': self.currency,
            'method': self.method.value if isinstance(self.method, PaymentMethod) else self.method,
            'status': self.status.value if isinstance(self.status, PaymentStatus) else self.status,
            'transaction_id': self.transaction_id,
            'gateway_response': self.gateway_response,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Payment':
        """Buat Payment dari dictionary"""
        return cls(
            id=data.get('id'),
            tenant_id=data.get('tenant_id', ''),
            discord_id=data.get('discord_id', ''),
            amount=data.get('amount', 0.0),
            currency=data.get('currency', 'USD'),
            method=PaymentMethod(data.get('method', 'credit_card')),
            status=PaymentStatus(data.get('status', 'pending')),
            transaction_id=data.get('transaction_id'),
            gateway_response=data.get('gateway_response'),
            description=data.get('description', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
