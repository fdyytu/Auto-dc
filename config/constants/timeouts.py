"""
Version tracking dan timeout settings
Author: fdyytu
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-10 10:09:16 UTC
"""

from datetime import timedelta

# Version Tracking
class VERSION:
    """Version tracking for components"""
    LIVE_STOCK = "1.0.0"
    LIVE_BUTTONS = "1.0.0"
    PRODUCT = "1.0.0"
    BALANCE = "1.0.0"
    TRANSACTION = "1.0.0"
    ADMIN = "1.0.0"

# System Timeouts
class TIMEOUTS:
    """System timeout settings"""
    INITIALIZATION = 30  # 30 seconds
    LOCK_ACQUISITION = 3  # 3 seconds
    SERVICE_CALL = 5    # 5 seconds
    CACHE_OPERATION = 2 # 2 seconds
    SYNC_RETRY = 5     # 5 seconds retry interval
    MAX_RETRIES = 3    # Maximum number of retries

# Live System Status States
class LIVE_STATUS:
    """Live system status states"""
    INITIALIZING = "initializing"
    READY = "ready"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    SYNCING = "syncing"
    RECOVERING = "recovering"
    SHUTDOWN = "shutdown"

# Cog Loading Status
COG_LOADED = {
    'PRODUCT': 'product_manager_loaded',
    'BALANCE': 'balance_manager_loaded',
    'TRANSACTION': 'transaction_manager_loaded',
    'LIVE_STOCK': 'live_stock_loaded', 
    'LIVE_BUTTONS': 'live_buttons_loaded',
    'ADMIN': 'admin_service_loaded'
}

# Update Intervals
class UPDATE_INTERVAL:
    LIVE_STOCK = 55.0    # Update live stock every 55 seconds
    BUTTONS = 30.0       # Update buttons every 30 seconds
    CACHE = 300.0        # Cache timeout 5 minutes
    STATUS = 15.0        # Status update every 15 seconds

# Cache Settings
class CACHE_TIMEOUT:
    SHORT = timedelta(minutes=5)      # 5 menit
    MEDIUM = timedelta(hours=1)       # 1 jam
    LONG = timedelta(days=1)          # 24 jam
    PERMANENT = timedelta(days=3650)  # 10 tahun (effectively permanent)

    @classmethod
    def get_seconds(cls, timeout: timedelta) -> int:
        """Convert timedelta ke detik"""
        return int(timeout.total_seconds())

# Command Cooldowns
class CommandCooldown:
    DEFAULT = 3
    PURCHASE = 5
    ADMIN = 2
    DONATE = 10
