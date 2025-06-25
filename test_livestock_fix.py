#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan livestock button error
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unittest.mock import Mock, AsyncMock
from src.ui.views.live_stock_view import LiveStockManager
from src.config.logging_config import get_logger

class MockBot:
    def __init__(self):
        self.user = Mock()
        self.user.id = 12345
        self.config = {'id_live_stock': 123456789}
        self.db_manager = Mock()

class MockButtonManager:
    def __init__(self, should_fail=False, return_none=False):
        self.should_fail = should_fail
        self.return_none = return_none
        self.call_count = 0
        
    def create_view(self):
        self.call_count += 1
        if self.should_fail:
            if self.call_count <= 2:  # Fail first 2 attempts
                raise Exception("Mock button creation error")
            else:
                return Mock()  # Success on 3rd attempt
        elif self.return_none:
            return None
        else:
            return Mock()
    
    def is_healthy(self):
        return not self.should_fail
    
    async def on_livestock_status_change(self, is_healthy, error):
        pass

async def test_livestock_manager():
    """Test LiveStockManager dengan berbagai skenario"""
    logger = get_logger("TestLiveStock")
    
    print("🧪 Testing LiveStockManager fixes...")
    
    # Test 1: Normal operation dengan button manager sehat
    print("\n1️⃣ Test: Normal operation dengan button manager sehat")
    try:
        bot = MockBot()
        manager = LiveStockManager(bot)
        button_manager = MockButtonManager()
        await manager.set_button_manager(button_manager)
        
        # Test status update
        await manager._update_status(True)
        status = manager.get_status()
        assert status['is_healthy'] == True
        print("✅ Status update berhasil")
        
    except Exception as e:
        print(f"❌ Test 1 gagal: {e}")
    
    # Test 2: Button manager gagal membuat view (retry mechanism)
    print("\n2️⃣ Test: Button manager gagal membuat view (retry mechanism)")
    try:
        bot = MockBot()
        manager = LiveStockManager(bot)
        button_manager = MockButtonManager(should_fail=True)
        await manager.set_button_manager(button_manager)
        
        # Test retry mechanism
        await manager._update_status(False, "Test retry mechanism")
        status = manager.get_status()
        assert status['is_healthy'] == False
        assert "Test retry mechanism" in status['last_error']
        print("✅ Retry mechanism dan error handling berhasil")
        
    except Exception as e:
        print(f"❌ Test 2 gagal: {e}")
    
    # Test 3: Button manager return None
    print("\n3️⃣ Test: Button manager return None")
    try:
        bot = MockBot()
        manager = LiveStockManager(bot)
        button_manager = MockButtonManager(return_none=True)
        await manager.set_button_manager(button_manager)
        
        await manager._update_status(False, "Button manager return None")
        status = manager.get_status()
        assert status['is_healthy'] == False
        print("✅ Handling button manager None berhasil")
        
    except Exception as e:
        print(f"❌ Test 3 gagal: {e}")
    
    # Test 4: Tanpa button manager
    print("\n4️⃣ Test: Tanpa button manager")
    try:
        bot = MockBot()
        manager = LiveStockManager(bot)
        # Tidak set button manager
        
        await manager._update_status(True)
        status = manager.get_status()
        assert status['is_healthy'] == True
        print("✅ Operation tanpa button manager berhasil")
        
    except Exception as e:
        print(f"❌ Test 4 gagal: {e}")
    
    print("\n🎉 Semua test selesai!")

if __name__ == "__main__":
    asyncio.run(test_livestock_manager())
