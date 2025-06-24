"""
Enums dan data models untuk aplikasi
Author: fdyytu
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-10 10:09:16 UTC
"""

from enum import Enum, auto
from typing import Dict, Union, List

# Transaction Types
class TransactionType(Enum):
    PURCHASE = "purchase"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DONATION = "donation"
    ADMIN_ADD = "admin_add"
    ADMIN_REMOVE = "admin_remove"
    ADMIN_RESET = "admin_reset"
    REFUND = "refund"
    TRANSFER = "transfer"

# Status untuk database
class Status(Enum):
    AVAILABLE = "available"  # Status di database
    SOLD = "sold"          # Status di database
    DELETED = "deleted"    # Status di database

# Stock Class
class Stock:
    def __init__(self, product_code: str, quantity: int = 0, data: List[str] = None):
        self.product_code = product_code
        self.quantity = max(0, quantity)
        self.data = data or []
        self.MAX_QUANTITY = 10000
        self.MIN_QUANTITY = 0

    def add_stock(self, items: List[str]) -> int:
        """Add stock items and return new quantity"""
        if not items:
            return self.quantity
        
        # Filter out empty items
        valid_items = [item.strip() for item in items if item.strip()]
        
        # Check if adding would exceed max quantity
        new_total = self.quantity + len(valid_items)
        if new_total > self.MAX_QUANTITY:
            # Only add what we can
            can_add = self.MAX_QUANTITY - self.quantity
            valid_items = valid_items[:can_add]
        
        self.data.extend(valid_items)
        self.quantity = len(self.data)
        return self.quantity

    def remove_stock(self, amount: int = 1) -> List[str]:
        """Remove stock items and return removed items"""
        if amount <= 0 or self.quantity == 0:
            return []
        
        # Don't remove more than available
        actual_amount = min(amount, self.quantity)
        removed_items = self.data[:actual_amount]
        self.data = self.data[actual_amount:]
        self.quantity = len(self.data)
        
        return removed_items

    def get_stock_preview(self, count: int = 3) -> List[str]:
        """Get preview of stock items"""
        return self.data[:min(count, len(self.data))]

    def is_available(self) -> bool:
        """Check if stock is available"""
        return self.quantity > 0

    def validate(self) -> bool:
        """Validate stock data"""
        return (
            isinstance(self.product_code, str) and
            self.product_code.strip() != "" and
            isinstance(self.quantity, int) and
            self.MIN_QUANTITY <= self.quantity <= self.MAX_QUANTITY and
            isinstance(self.data, list) and
            len(self.data) == self.quantity
        )

    def __str__(self):
        return f"Stock({self.product_code}: {self.quantity} items)"

    def __repr__(self):
        return self.__str__()

# Permission Levels
class PERMISSIONS:
    """Permission levels untuk product manager"""
    VIEW = 0      # Can view products and stock
    PURCHASE = 1  # Can purchase products
    STOCK = 2     # Can manage stock
    ADMIN = 3     # Can manage products and settings
    OWNER = 4     # Full access

# Currency Rates
CURRENCY_RATES = {
    'WL': 1,      # World Lock = 1 WL
    'DL': 100,    # Diamond Lock = 100 WL
    'BGL': 10000  # Blue Gem Lock = 10,000 WL
}

# File Size Settings
MAX_STOCK_FILE_SIZE = 5 * 1024 * 1024  # 5MB max file size for stock files
MAX_ATTACHMENT_SIZE = 8 * 1024 * 1024  # 8MB max attachment size
MAX_EMBED_SIZE = 6000  # Discord embed character limit

# Valid Stock Formats
VALID_STOCK_FORMATS = ['txt']  # Format file yang diizinkan untuk stock
