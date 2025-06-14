"""
Database package
Provides backward compatibility for existing ext modules
"""

from .connection import DatabaseManager
from .migrations import setup_database

# Backward compatibility untuk ext modules
_db_manager = None

def get_connection():
    """Backward compatibility function"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

# Export untuk compatibility
__all__ = ['DatabaseManager', 'setup_database', 'get_connection']
