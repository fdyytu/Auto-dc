"""
Test cases untuk services
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

class TestServices(unittest.TestCase):
    """Test cases untuk service modules"""
    
    def test_import_services(self):
        """Test import services modules"""
        try:
            from src.services import user_service
            from src.services import product_service
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import services: {e}")
    
    def test_import_database(self):
        """Test import database modules"""
        try:
            from src.database import models
            from src.database import repositories
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import database modules: {e}")

if __name__ == "__main__":
    unittest.main()
