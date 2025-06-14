"""
Logging Manager (DEPRECATED)
Menangani setup dan konfigurasi logging untuk bot

DEPRECATED: Use config.logging_config instead for centralized logging
"""

import logging
import warnings
from config.logging_config import logging_manager as centralized_manager

# Deprecation warning
warnings.warn(
    "core.logging is deprecated. Use config.logging_config instead.",
    DeprecationWarning,
    stacklevel=2
)

# Redirect to centralized logging manager
logging_manager = centralized_manager

# Backward compatibility
class LoggingManager:
    """Deprecated LoggingManager - redirects to centralized version"""
    
    def __init__(self):
        warnings.warn(
            "core.logging.LoggingManager is deprecated. Use config.logging_config.CentralizedLoggingManager instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._manager = centralized_manager
    
    def setup_logging(self, level: int = logging.INFO) -> bool:
        return self._manager.setup_logging(level)
    
    def get_logger(self, name: str) -> logging.Logger:
        return self._manager.get_logger(name)
    
    def create_module_logger(self, module_name: str) -> logging.Logger:
        return self._manager.create_module_logger(module_name)
