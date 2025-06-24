#!/usr/bin/env python3
"""
Test script untuk memverifikasi konsistensi services dengan models
"""

import sys
import os
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_imports():
    """Test import semua services"""
    try:
        logger.info("Testing imports...")
        
        # Test base service
        from src.services.base_service import BaseService, ServiceResponse
        logger.info("✓ BaseService imported successfully")
        
        # Test user service
        from src.services.user_service import UserService
        logger.info("✓ UserService imported successfully")
        
        # Test product service
        from src.services.product_service import ProductService
        logger.info("✓ ProductService imported successfully")
        
        # Test level service
        from src.services.level_service import LevelService
        logger.info("✓ LevelService imported successfully")
        
        # Test world service
        from src.services.world_service import WorldService
        logger.info("✓ WorldService imported successfully")
        
        # Test cache service
        from src.services.cache_service import CacheManager
        logger.info("✓ CacheManager imported successfully")
        
        # Test admin service
        from src.services.admin_service import AdminService
        logger.info("✓ AdminService imported successfully")
        
        # Test services __init__
        from src.services import (
            BaseService, ServiceResponse, UserService, ProductService,
            LevelService, WorldService, CacheManager, AdminService
        )
        logger.info("✓ Services __init__ imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

async def test_models():
    """Test import semua models"""
    try:
        logger.info("Testing model imports...")
        
        # Test user models
        from src.database.models.user import User, UserGrowID
        logger.info("✓ User models imported successfully")
        
        # Test product models
        from src.database.models.product import Product, Stock, StockStatus
        logger.info("✓ Product models imported successfully")
        
        # Test transaction models
        from src.database.models.transaction import Transaction, TransactionType, TransactionStatus
        logger.info("✓ Transaction models imported successfully")
        
        # Test level models
        from src.database.models.level import Level, LevelReward, LevelSettings
        logger.info("✓ Level models imported successfully")
        
        # Test balance model
        from src.database.models.balance import Balance
        logger.info("✓ Balance model imported successfully")
        
        # Test world model
        from src.database.models.world import World
        logger.info("✓ World model imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Model import failed: {e}")
        return False

async def test_service_response():
    """Test ServiceResponse functionality"""
    try:
        logger.info("Testing ServiceResponse...")
        
        from src.services.base_service import ServiceResponse
        
        # Test success response
        success_response = ServiceResponse.success_response(
            data={"test": "data"}, 
            message="Test success"
        )
        assert success_response.success == True
        assert success_response.data == {"test": "data"}
        assert success_response.message == "Test success"
        logger.info("✓ Success response works")
        
        # Test error response
        error_response = ServiceResponse.error_response(
            error="Test error",
            message="Test error message"
        )
        assert error_response.success == False
        assert error_response.error == "Test error"
        assert error_response.message == "Test error message"
        logger.info("✓ Error response works")
        
        # Test to_dict
        response_dict = success_response.to_dict()
        assert isinstance(response_dict, dict)
        assert 'success' in response_dict
        assert 'timestamp' in response_dict
        logger.info("✓ to_dict() works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ServiceResponse test failed: {e}")
        return False

async def test_model_consistency():
    """Test model to_dict and from_dict consistency"""
    try:
        logger.info("Testing model consistency...")
        
        # Test User model
        from src.database.models.user import User
        user = User(growid="TestUser123")
        user_dict = user.to_dict()
        user_from_dict = User.from_dict(user_dict)
        assert user.growid == user_from_dict.growid
        logger.info("✓ User model consistency")
        
        # Test Product model
        from src.database.models.product import Product
        product = Product(code="TEST001", name="Test Product", price=1000)
        product_dict = product.to_dict()
        product_from_dict = Product.from_dict(product_dict)
        assert product.code == product_from_dict.code
        assert product.name == product_from_dict.name
        assert product.price == product_from_dict.price
        logger.info("✓ Product model consistency")
        
        # Test Balance model
        from src.database.models.balance import Balance
        balance = Balance(wl=1000, dl=10, bgl=1)
        total_wl = balance.total_wl()
        assert total_wl == 1000 + (10 * 100) + (1 * 10000)  # Assuming rates
        logger.info("✓ Balance model consistency")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Model consistency test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("Starting service consistency tests...")
    
    tests = [
        ("Import Tests", test_imports),
        ("Model Tests", test_models),
        ("ServiceResponse Tests", test_service_response),
        ("Model Consistency Tests", test_model_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Services are consistent with models.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
