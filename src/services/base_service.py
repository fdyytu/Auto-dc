"""
Base Service Module
Menyediakan base class dan response format yang konsisten untuk semua service
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import logging

@dataclass
class ServiceResponse:
    """Response wrapper yang konsisten untuk semua service operations"""
    success: bool
    data: Any = None
    message: str = ""
    error: str = ""
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert response ke dictionary"""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'error': self.error,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def success_response(cls, data: Any = None, message: str = "") -> 'ServiceResponse':
        """Buat response sukses"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, error: str, message: str = "") -> 'ServiceResponse':
        """Buat response error"""
        return cls(success=False, error=error, message=message)

class BaseService:
    """Base class untuk semua service"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _handle_exception(self, e: Exception, operation: str) -> ServiceResponse:
        """Handle exception dan return error response"""
        error_msg = f"Error in {operation}: {str(e)}"
        self.logger.error(error_msg)
        return ServiceResponse.error_response(
            error=str(e),
            message=f"Terjadi kesalahan saat {operation}"
        )
