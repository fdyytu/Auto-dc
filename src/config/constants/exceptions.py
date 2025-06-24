"""
Custom exceptions dan configuration constants
Author: fdyytu
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-10 10:09:16 UTC
"""

# Custom Exceptions
class TransactionError(Exception):
    """Base exception for transaction related errors"""
    pass

class InsufficientBalanceError(TransactionError):
    """Raised when user has insufficient balance"""
    pass

class OutOfStockError(TransactionError):
    """Raised when item is out of stock"""
    pass

# Product Manager Exceptions
class ProductError(Exception):
    """Base exception for product related errors"""
    pass

class ProductNotFoundError(ProductError):
    """Raised when product is not found"""
    pass

class InvalidProductCodeError(ProductError):
    """Raised when product code is invalid"""
    pass

class StockLimitError(ProductError):
    """Raised when stock limit is reached"""
    pass

class LockError(Exception):
    """Raised when lock acquisition fails"""
    pass

# Database Settings
class Database:
    TIMEOUT = 5
    MAX_CONNECTIONS = 5
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1
    BACKUP_INTERVAL = 86400  # 24 hours

# Paths Configuration
class PATHS:
    CONFIG = "config.json"
    LOGS = "logs/"
    DATABASE = "database.db"
    BACKUP = "backups/"
    TEMP = "temp/"

# Logging Configuration
class LOGGING:
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    MAX_BYTES = 5 * 1024 * 1024  # 5MB
    BACKUP_COUNT = 5

# Notification Channel IDs
class NOTIFICATION_CHANNELS:
    """Channel IDs untuk notifikasi sistem"""
    TRANSACTIONS = 1348580531519881246
    PRODUCT_LOGS = 1348580616647610399
    STOCK_LOGS = 1348580676202528839
    ADMIN_LOGS = 1348580745433710625
    ERROR_LOGS = 1348581120723128390
    SHOP = 1319281983796547595

    @classmethod
    def get(cls, channel_type: str, default=None):
        """Get channel ID by type"""
        try:
            return getattr(cls, channel_type.upper(), default)
        except AttributeError:
            return default
