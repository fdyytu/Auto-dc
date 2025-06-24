#!/usr/bin/env python3
"""
Comprehensive test untuk memverifikasi functionality services
"""

import sys
import os
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockDatabaseManager:
    """Mock database manager untuk testing"""
    
    def __init__(self):
        self.data = {
            'users': [
                {
                    'growid': 'TestUser123',
                    'balance_wl': 1000,
                    'balance_dl': 10,
                    'balance_bgl': 1,
                    'created_at': '2024-01-01T00:00:00',
                    'updated_at': '2024-01-01T00:00:00'
                }
            ],
            'products': [
                {
                    'code': 'TEST001',
                    'name': 'Test Product',
                    'price': 100,
                    'description': 'Test Description',
                    'created_at': '2024-01-01T00:00:00',
                    'updated_at': '2024-01-01T00:00:00'
                }
            ],
            'stock': [
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
        }
    
    async def execute_query(self, query, params=None):
        """Mock execute_query"""
        query_lower = query.lower()
        
        if 'select * from users where growid = ?' in query_lower:
            growid = params[0] if params else None
            users = [u for u in self.data['users'] if u['growid'] == growid]
            return [MagicMock(**user) for user in users] if users else []
        
        elif 'select * from products where code = ?' in query_lower:
            code = params[0] if params else None
            products = [p for p in self.data['products'] if p['code'] == code]
            return [MagicMock(**product) for product in products] if products else []
        
        elif 'select * from products order by name' in query_lower:
            return [MagicMock(**product) for product in self.data['products']]
        
        elif 'select * from users order by created_at desc' in query_lower:
            return [MagicMock(**user) for user in self.data['users']]
        
        elif 'select count(*) as count from stock' in query_lower:
            return [MagicMock(count=len(self.data['stock']))]
        
        return []
    
    async def execute_update(self, query, params=None):
        """Mock execute_update"""
        return True

async def test_user_service():
    """Test UserService functionality"""
    try:
        logger.info("Testing UserService...")
        
        from src.services.user_service import UserService
        from src.services.base_service import ServiceResponse
        
        # Create service with mock database
        mock_db = MockDatabaseManager()
        user_service = UserService(mock_db)
        
        # Test get_user_by_growid
        result = await user_service.get_user_by_growid('TestUser123')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert result.data['growid'] == 'TestUser123'
        logger.info("✓ get_user_by_growid works")
        
        # Test get_user_by_growid - not found
        result = await user_service.get_user_by_growid('NonExistentUser')
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        logger.info("✓ get_user_by_growid handles not found")
        
        # Test get_all_users
        result = await user_service.get_all_users()
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert len(result.data) > 0
        logger.info("✓ get_all_users works")
        
        # Test get_user_balance
        result = await user_service.get_user_balance('TestUser123')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert 'balance' in result.data
        logger.info("✓ get_user_balance works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ UserService test failed: {e}")
        return False

async def test_product_service():
    """Test ProductService functionality"""
    try:
        logger.info("Testing ProductService...")
        
        from src.services.product_service import ProductService
        from src.services.base_service import ServiceResponse
        
        # Create service with mock database
        mock_db = MockDatabaseManager()
        product_service = ProductService(mock_db)
        
        # Test get_product
        result = await product_service.get_product('TEST001')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert result.data['code'] == 'TEST001'
        logger.info("✓ get_product works")
        
        # Test get_product - not found
        result = await product_service.get_product('NONEXISTENT')
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        logger.info("✓ get_product handles not found")
        
        # Test get_all_products
        result = await product_service.get_all_products()
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert len(result.data) > 0
        logger.info("✓ get_all_products works")
        
        # Test get_product_stock_count
        result = await product_service.get_product_stock_count('TEST001')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert 'count' in result.data
        logger.info("✓ get_product_stock_count works")
        
        # Test create_product validation
        result = await product_service.create_product('', 'Invalid Product', 100)
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        logger.info("✓ create_product validation works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ProductService test failed: {e}")
        return False

async def test_level_service():
    """Test LevelService functionality"""
    try:
        logger.info("Testing LevelService...")
        
        from src.services.level_service import LevelService
        from src.services.base_service import ServiceResponse
        
        # Create service with mock database
        mock_db = MockDatabaseManager()
        level_service = LevelService(mock_db)
        
        # Test get_user_level - not found (should trigger error)
        result = await level_service.get_user_level('user123', 'guild123')
        assert isinstance(result, ServiceResponse)
        assert result.success == False
        logger.info("✓ get_user_level handles not found")
        
        # Test get_level_rewards - empty
        result = await level_service.get_level_rewards('guild123')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert result.data == []
        logger.info("✓ get_level_rewards handles empty")
        
        # Test get_guild_leaderboard - empty
        result = await level_service.get_guild_leaderboard('guild123')
        assert isinstance(result, ServiceResponse)
        assert result.success == True
        assert result.data == []
        logger.info("✓ get_guild_leaderboard handles empty")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ LevelService test failed: {e}")
        return False

async def test_service_response():
    """Test ServiceResponse functionality in detail"""
    try:
        logger.info("Testing ServiceResponse in detail...")
        
        from src.services.base_service import ServiceResponse
        from datetime import datetime
        
        # Test success response with complex data
        complex_data = {
            'user': {'id': 1, 'name': 'Test'},
            'items': [1, 2, 3],
            'metadata': {'count': 3}
        }
        
        response = ServiceResponse.success_response(
            data=complex_data,
            message="Complex data test"
        )
        
        assert response.success == True
        assert response.data == complex_data
        assert response.message == "Complex data test"
        assert response.error == ""
        assert isinstance(response.timestamp, datetime)
        logger.info("✓ Complex success response works")
        
        # Test error response
        error_response = ServiceResponse.error_response(
            error="Validation failed",
            message="Input validation error"
        )
        
        assert error_response.success == False
        assert error_response.error == "Validation failed"
        assert error_response.message == "Input validation error"
        assert error_response.data is None
        logger.info("✓ Error response works")
        
        # Test to_dict conversion
        response_dict = response.to_dict()
        assert isinstance(response_dict, dict)
        assert response_dict['success'] == True
        assert response_dict['data'] == complex_data
        assert 'timestamp' in response_dict
        assert isinstance(response_dict['timestamp'], str)
        logger.info("✓ to_dict conversion works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ServiceResponse detailed test failed: {e}")
        return False

async def test_model_integration():
    """Test integration between models and services"""
    try:
        logger.info("Testing model integration...")
        
        # Test User model integration
        from src.database.models.user import User
        from src.services.base_service import ServiceResponse
        
        user = User(growid="IntegrationTest")
        user_dict = user.to_dict()
        
        # Simulate service response with user data
        response = ServiceResponse.success_response(
            data=user_dict,
            message="User data retrieved"
        )
        
        # Verify we can reconstruct user from response
        reconstructed_user = User.from_dict(response.data)
        assert reconstructed_user.growid == user.growid
        assert reconstructed_user.balance_wl == user.balance_wl
        logger.info("✓ User model integration works")
        
        # Test Product model integration
        from src.database.models.product import Product
        
        product = Product(code="INTEGRATION001", name="Integration Test", price=500)
        product_dict = product.to_dict()
        
        response = ServiceResponse.success_response(
            data=product_dict,
            message="Product data retrieved"
        )
        
        reconstructed_product = Product.from_dict(response.data)
        assert reconstructed_product.code == product.code
        assert reconstructed_product.name == product.name
        assert reconstructed_product.price == product.price
        logger.info("✓ Product model integration works")
        
        # Test Balance model integration
        from src.database.models.balance import Balance
        
        balance = Balance(wl=1000, dl=10, bgl=1)
        total_wl = balance.total_wl()
        formatted = balance.format()
        
        assert total_wl > 1000  # Should include DL and BGL conversion
        assert isinstance(formatted, str)
        assert "WL" in formatted
        logger.info("✓ Balance model integration works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Model integration test failed: {e}")
        return False

async def test_error_handling():
    """Test error handling across services"""
    try:
        logger.info("Testing error handling...")
        
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
        logger.error(f"✗ Error handling test failed: {e}")
        return False

async def main():
    """Main comprehensive test function"""
    logger.info("Starting comprehensive functionality tests...")
    
    tests = [
        ("UserService Tests", test_user_service),
        ("ProductService Tests", test_product_service),
        ("LevelService Tests", test_level_service),
        ("ServiceResponse Detailed Tests", test_service_response),
        ("Model Integration Tests", test_model_integration),
        ("Error Handling Tests", test_error_handling)
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
    
    logger.info(f"\n--- Comprehensive Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All comprehensive tests passed! Services are fully functional.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
