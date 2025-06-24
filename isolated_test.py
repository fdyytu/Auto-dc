#!/usr/bin/env python3
"""
Isolated test untuk memverifikasi functionality services tanpa dependencies eksternal
"""

import sys
import os
import asyncio
import logging
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockRow:
    """Mock database row"""
    def __init__(self, **kwargs):
        self._data = kwargs
    
    def __getitem__(self, key):
        return self._data[key]
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()

def dict_from_row(row):
    """Convert mock row to dict"""
    return {key: row[key] for key in row.keys()}

class MockDatabaseManager:
    """Mock database manager untuk testing"""
    
    def __init__(self):
        self.users_data = [
            {
                'growid': 'TestUser123',
                'balance_wl': 1000,
                'balance_dl': 10,
                'balance_bgl': 1,
                'created_at': '2024-01-01T00:00:00',
                'updated_at': '2024-01-01T00:00:00'
            }
        ]
        
        self.products_data = [
            {
                'code': 'TEST001',
                'name': 'Test Product',
                'price': 100,
                'description': 'Test Description',
                'created_at': '2024-01-01T00:00:00',
                'updated_at': '2024-01-01T00:00:00'
            }
        ]
        
        self.stock_data = [
            {
                'id': 1,
                'product_code': 'TEST001',
                'content': 'test_content_123',
                'status': 'available',
                'added_by': 'admin',
                'buyer_id': None,
                'added_at': '2024-01-01T00:00:00',
                'updated_at': '2024-01-01T00:00:00'
            }
        ]
    
    async def execute_query(self, query, params=None):
        """Mock execute_query"""
        query_lower = query.lower().strip()
        
        # User queries
        if 'select * from users where growid = ?' in query_lower:
            growid = params[0] if params else None
            users = [u for u in self.users_data if u['growid'] == growid]
            return [MockRow(**user) for user in users] if users else []
        
        elif 'select * from users order by created_at desc' in query_lower:
            return [MockRow(**user) for user in self.users_data]
        
        # Product queries
        elif 'select * from products where code = ?' in query_lower:
            code = params[0] if params else None
            products = [p for p in self.products_data if p['code'] == code]
            return [MockRow(**product) for product in products] if products else []
        
        elif 'select * from products order by name' in query_lower:
            return [MockRow(**product) for product in self.products_data]
        
        # Stock queries
        elif 'select count(*) as count from stock' in query_lower:
            return [MockRow(count=len(self.stock_data))]
        
        elif 'select * from stock where product_code = ?' in query_lower:
            product_code = params[0] if params else None
            stocks = [s for s in self.stock_data if s['product_code'] == product_code]
            return [MockRow(**stock) for stock in stocks]
        
        # User-Discord mapping queries
        elif 'user_growid' in query_lower and 'discord_id' in query_lower:
            return []  # No mapping data for test
        
        return []
    
    async def execute_update(self, query, params=None):
        """Mock execute_update"""
        return True

async def test_base_service():
    """Test BaseService functionality"""
    try:
        logger.info("Testing BaseService...")
        
        from src.services.base_service import BaseService, ServiceResponse
        
        # Test ServiceResponse creation
        success_response = ServiceResponse.success_response(
            data={'test': 'data'},
            message='Test message'
        )
        
        assert success_response.success == True
        assert success_response.data == {'test': 'data'}
        assert success_response.message == 'Test message'
        assert success_response.error == ''
        logger.info("✓ ServiceResponse success creation works")
        
        # Test error response
        error_response = ServiceResponse.error_response(
            error='Test error',
            message='Error message'
        )
        
        assert error_response.success == False
        assert error_response.error == 'Test error'
        assert error_response.message == 'Error message'
        assert error_response.data is None
        logger.info("✓ ServiceResponse error creation works")
        
        # Test BaseService
        mock_db = MockDatabaseManager()
        base_service = BaseService(mock_db)
        assert base_service.db_manager == mock_db
        logger.info("✓ BaseService initialization works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ BaseService test failed: {e}")
        return False

async def test_user_service_isolated():
    """Test UserService functionality in isolation"""
    try:
        logger.info("Testing UserService in isolation...")
        
        from src.services.user_service import UserService
        from src.services.base_service import ServiceResponse
        
        # Create service with mock database
        mock_db = MockDatabaseManager()
        user_service = UserService(mock_db)
        
        # Test get_user_by_growid - found
        result = await user_service.get_user_by_growid('TestUser123')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert result.data['growid'] == 'TestUser123'
        assert result.data['balance_wl'] == 1000
        logger.info("✓ get_user_by_growid works")
        
        # Test get_user_by_growid - not found
        result = await user_service.get_user_by_growid('NonExistentUser')
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        assert 'tidak ditemukan' in result.message.lower()
        logger.info("✓ get_user_by_growid handles not found")
        
        # Test get_all_users
        result = await user_service.get_all_users()
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert len(result.data) == 1
        assert result.data[0]['growid'] == 'TestUser123'
        logger.info("✓ get_all_users works")
        
        # Test get_user_balance
        result = await user_service.get_user_balance('TestUser123')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert 'balance' in result.data
        assert result.data['balance']['wl'] == 1000
        logger.info("✓ get_user_balance works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ UserService isolated test failed: {e}")
        return False

async def test_product_service_isolated():
    """Test ProductService functionality in isolation"""
    try:
        logger.info("Testing ProductService in isolation...")
        
        from src.services.product_service import ProductService
        from src.services.base_service import ServiceResponse
        
        # Create service with mock database
        mock_db = MockDatabaseManager()
        product_service = ProductService(mock_db)
        
        # Test get_product - found
        result = await product_service.get_product('TEST001')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert result.data['code'] == 'TEST001'
        assert result.data['name'] == 'Test Product'
        assert result.data['price'] == 100
        logger.info("✓ get_product works")
        
        # Test get_product - not found
        result = await product_service.get_product('NONEXISTENT')
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        assert 'tidak ditemukan' in result.message.lower()
        logger.info("✓ get_product handles not found")
        
        # Test get_all_products
        result = await product_service.get_all_products()
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert len(result.data) == 1
        assert result.data[0]['code'] == 'TEST001'
        logger.info("✓ get_all_products works")
        
        # Test get_product_stock_count
        result = await product_service.get_product_stock_count('TEST001')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert 'count' in result.data
        assert result.data['count'] == 1
        logger.info("✓ get_product_stock_count works")
        
        # Test input validation
        result = await product_service.create_product('', 'Invalid Product', 100)
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        assert 'tidak boleh kosong' in result.error.lower()
        logger.info("✓ create_product validation works")
        
        result = await product_service.create_product('VALID001', '', 100)
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        assert 'tidak boleh kosong' in result.error.lower()
        logger.info("✓ create_product name validation works")
        
        result = await product_service.create_product('VALID001', 'Valid Product', -100)
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        assert 'tidak boleh negatif' in result.error.lower()
        logger.info("✓ create_product price validation works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ProductService isolated test failed: {e}")
        return False

async def test_models_consistency():
    """Test models consistency and functionality"""
    try:
        logger.info("Testing models consistency...")
        
        # Test User model
        from src.database.models.user import User
        
        user = User(growid="TestUser456")
        user_dict = user.to_dict()
        
        assert 'growid' in user_dict
        assert 'balance_wl' in user_dict
        assert 'created_at' in user_dict
        assert user_dict['growid'] == "TestUser456"
        
        # Test from_dict
        user_from_dict = User.from_dict(user_dict)
        assert user_from_dict.growid == user.growid
        assert user_from_dict.balance_wl == user.balance_wl
        logger.info("✓ User model consistency works")
        
        # Test Product model
        from src.database.models.product import Product
        
        product = Product(code="PROD001", name="Test Product", price=500)
        product_dict = product.to_dict()
        
        assert 'code' in product_dict
        assert 'name' in product_dict
        assert 'price' in product_dict
        assert product_dict['code'] == "PROD001"
        assert product_dict['price'] == 500
        
        product_from_dict = Product.from_dict(product_dict)
        assert product_from_dict.code == product.code
        assert product_from_dict.name == product.name
        assert product_from_dict.price == product.price
        logger.info("✓ Product model consistency works")
        
        # Test Balance model
        from src.database.models.balance import Balance
        
        balance = Balance(wl=1000, dl=10, bgl=1)
        total_wl = balance.total_wl()
        formatted = balance.format()
        
        assert total_wl > 1000  # Should include DL and BGL conversion
        assert isinstance(formatted, str)
        assert "WL" in formatted
        logger.info("✓ Balance model functionality works")
        
        # Test Stock model
        from src.database.models.product import Stock, StockStatus
        
        stock = Stock(
            product_code="PROD001",
            content="test_content",
            added_by="admin",
            status=StockStatus.AVAILABLE
        )
        stock_dict = stock.to_dict()
        
        assert 'product_code' in stock_dict
        assert 'content' in stock_dict
        assert 'status' in stock_dict
        assert stock_dict['status'] == 'available'
        
        stock_from_dict = Stock.from_dict(stock_dict)
        assert stock_from_dict.product_code == stock.product_code
        assert stock_from_dict.content == stock.content
        assert stock_from_dict.status == stock.status
        logger.info("✓ Stock model consistency works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Models consistency test failed: {e}")
        return False

async def test_error_handling_isolated():
    """Test error handling in isolation"""
    try:
        logger.info("Testing error handling in isolation...")
        
        from src.services.user_service import UserService
        from src.services.product_service import ProductService
        
        # Create service with mock that throws exceptions
        class ErrorMockDB:
            async def execute_query(self, query, params=None):
                raise Exception("Database connection failed")
            
            async def execute_update(self, query, params=None):
                raise Exception("Database update failed")
        
        error_db = ErrorMockDB()
        user_service = UserService(error_db)
        product_service = ProductService(error_db)
        
        # Test error handling in UserService
        result = await user_service.get_user_by_growid('TestUser')
        assert result.success == False
        assert "Database connection failed" in result.error
        logger.info("✓ UserService error handling works")
        
        # Test error handling in ProductService
        result = await product_service.get_product('TEST001')
        assert result.success == False
        assert "Database connection failed" in result.error
        logger.info("✓ ProductService error handling works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error handling isolated test failed: {e}")
        return False

async def main():
    """Main isolated test function"""
    logger.info("Starting isolated functionality tests...")
    
    tests = [
        ("BaseService Tests", test_base_service),
        ("UserService Isolated Tests", test_user_service_isolated),
        ("ProductService Isolated Tests", test_product_service_isolated),
        ("Models Consistency Tests", test_models_consistency),
        ("Error Handling Isolated Tests", test_error_handling_isolated)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info(f"\n--- Isolated Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All isolated tests passed! Services functionality is verified.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
