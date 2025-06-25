#!/usr/bin/env python3
"""
Test Script untuk Live Stock Buttons Fix
Author: Assistant
Created: 2025-01-XX

Script ini untuk testing perbaikan masalah tombol live stock:
1. Tombol muncul bersama live stock
2. Update tombol jika sudah ada
3. Tidak mengirim embed baru jika tombol sudah ada
4. Logging error yang lebih baik
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_live_stock.log')
    ]
)

logger = logging.getLogger("LiveStockTest")

async def test_live_stock_integration():
    """Test integrasi live stock dan buttons"""
    logger.info("🧪 Memulai test integrasi live stock dan buttons...")
    
    try:
        # Import modules
        from src.ui.views.live_stock_view import LiveStockManager
        from src.ui.buttons.live_buttons import LiveButtonManager
        from src.database.manager import DatabaseManager
        
        logger.info("✅ Import modules berhasil")
        
        # Mock bot object untuk testing
        class MockBot:
            def __init__(self):
                self.config = {
                    'id_live_stock': '1318806350310146114',
                    'token': 'test_token'
                }
                self.db_manager = DatabaseManager()
                self.user = MockUser()
                
            def get_channel(self, channel_id):
                return MockChannel(channel_id)
                
        class MockUser:
            def __init__(self):
                self.id = 123456789
                self.name = "TestBot"
                
        class MockChannel:
            def __init__(self, channel_id):
                self.id = channel_id
                self.name = f"test-channel-{channel_id}"
                
            async def send(self, **kwargs):
                logger.info(f"📤 Mock channel.send called with: {kwargs.keys()}")
                return MockMessage()
                
            async def history(self, limit=50):
                # Mock empty history
                return []
                
        class MockMessage:
            def __init__(self):
                self.id = 987654321
                self.author = MockUser()
                self.embeds = []
                self.components = []
                
            async def edit(self, **kwargs):
                logger.info(f"✏️ Mock message.edit called with: {kwargs.keys()}")
                if 'embed' in kwargs:
                    logger.info("  - Embed updated")
                if 'view' in kwargs:
                    logger.info("  - View/buttons updated")
                    
            async def fetch(self):
                return self
        
        # Create mock bot
        bot = MockBot()
        logger.info("✅ Mock bot created")
        
        # Test LiveStockManager
        logger.info("🧪 Testing LiveStockManager...")
        stock_manager = LiveStockManager(bot)
        await stock_manager.initialize()
        logger.info("✅ LiveStockManager initialized")
        
        # Test LiveButtonManager
        logger.info("🧪 Testing LiveButtonManager...")
        button_manager = LiveButtonManager(bot)
        logger.info("✅ LiveButtonManager initialized")
        
        # Test integration
        logger.info("🧪 Testing integration...")
        await button_manager.set_stock_manager(stock_manager)
        await stock_manager.set_button_manager(button_manager)
        logger.info("✅ Integration setup complete")
        
        # Test create view
        logger.info("🧪 Testing view creation...")
        view = button_manager.create_view()
        logger.info(f"✅ View created with {len(view.children)} buttons")
        
        # Test stock embed creation
        logger.info("🧪 Testing stock embed creation...")
        embed = await stock_manager.create_stock_embed()
        logger.info(f"✅ Stock embed created: {embed.title}")
        
        # Test update stock display
        logger.info("🧪 Testing update stock display...")
        result = await stock_manager.update_stock_display()
        logger.info(f"✅ Update stock display result: {result}")
        
        # Test button health report
        logger.info("🧪 Testing button health report...")
        health_report = button_manager.get_button_health_report()
        logger.info(f"✅ Button health report generated")
        
        logger.info("🎉 Semua test berhasil!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test gagal: {e}", exc_info=True)
        return False

async def test_logging_functionality():
    """Test logging functionality"""
    logger.info("🧪 Testing logging functionality...")
    
    try:
        from src.config.logging_config import get_logger
        
        # Test different loggers
        test_logger = get_logger("TestLogger")
        test_logger.info("✅ Test info message")
        test_logger.warning("⚠️ Test warning message")
        test_logger.error("❌ Test error message")
        
        logger.info("✅ Logging functionality test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Logging test failed: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Memulai test suite untuk Live Stock Buttons Fix")
    logger.info(f"📅 Test dimulai pada: {datetime.now()}")
    
    tests = [
        ("Logging Functionality", test_logging_functionality),
        ("Live Stock Integration", test_live_stock_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}", exc_info=True)
    
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 TEST SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"✅ Passed: {passed}/{total}")
    logger.info(f"❌ Failed: {total - passed}/{total}")
    logger.info(f"📅 Test selesai pada: {datetime.now()}")
    
    if passed == total:
        logger.info("🎉 SEMUA TEST BERHASIL!")
        return True
    else:
        logger.error("💥 ADA TEST YANG GAGAL!")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ Test dihentikan oleh user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test crashed: {e}", exc_info=True)
        sys.exit(1)
