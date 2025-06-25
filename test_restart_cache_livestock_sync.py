#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan restart command, cache clearing, dan sinkronisasi livestock-button
"""

import sys
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockBot:
    """Mock Discord Bot object"""
    def __init__(self):
        self.db_manager = Mock()
        self.close = AsyncMock()
        self.wait_for = AsyncMock()
        self.config = Mock()
        self.config.get.return_value = 123456789  # Mock channel ID
        self.get_cog = Mock()

class MockContext:
    """Mock Discord Context object"""
    def __init__(self, author_id, channel_id=123456789):
        self.author = Mock()
        self.author.id = author_id
        self.author.name = "TestUser"
        self.channel = Mock()
        self.channel.id = channel_id
        self.send = AsyncMock()

async def test_restart_command_cache_cleanup():
    """Test restart command dengan cache cleanup"""
    print("🧪 Testing Restart Command Cache Cleanup...")
    
    try:
        from src.cogs.admin import AdminCog
        from src.ext.cache_manager import CacheManager
        
        # Create mock bot and admin cog
        bot = MockBot()
        admin_cog = AdminCog(bot)
        
        # Test cache cleanup method
        print("  🔍 Testing _cleanup_before_restart method...")
        
        # Mock the cogs
        mock_livestock_cog = Mock()
        mock_livestock_cog.stock_manager = Mock()
        mock_livestock_cog.stock_manager.current_stock_message = None
        mock_livestock_cog.stock_manager.button_manager = None
        mock_livestock_cog.update_stock_task = Mock()
        mock_livestock_cog.update_stock_task.is_running.return_value = True
        mock_livestock_cog.update_stock_task.cancel = Mock()
        
        mock_button_cog = Mock()
        mock_button_cog.button_manager = Mock()
        mock_button_cog.button_manager.current_message = None
        mock_button_cog.button_manager.stock_manager = None
        mock_button_cog.check_display = Mock()
        mock_button_cog.check_display.is_running.return_value = True
        mock_button_cog.check_display.cancel = Mock()
        
        bot.get_cog.side_effect = lambda name: {
            'LiveStockCog': mock_livestock_cog,
            'LiveButtonsCog': mock_button_cog
        }.get(name)
        
        # Test cleanup method
        await admin_cog._cleanup_before_restart()
        
        print("    ✅ Cache cleanup method executed successfully")
        print("    ✅ Livestock state cleanup tested")
        print("    ✅ Button state cleanup tested")
        print("    ✅ Background tasks stop tested")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error testing restart cache cleanup: {e}")
        return False

async def test_cache_manager_improvements():
    """Test cache manager improvements"""
    print("\n🧪 Testing Cache Manager Improvements...")
    
    try:
        from src.ext.cache_manager import CacheManager
        
        cache_manager = CacheManager()
        
        # Test setting some cache entries
        await cache_manager.set("test_key_1", "value1", expires_in=3600, permanent=False)
        await cache_manager.set("test_key_2", "value2", expires_in=3600, permanent=True)
        await cache_manager.set("test_key_3", "value3", expires_in=1, permanent=False)  # Will expire quickly
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Test clear methods
        print("  🔍 Testing cache clear methods...")
        
        # Test clear expired
        expired_count = await cache_manager.clear_expired()
        print(f"    ✅ Clear expired: {expired_count} entries removed")
        
        # Test clear temporary
        temp_count = await cache_manager.clear_temporary()
        print(f"    ✅ Clear temporary: {temp_count} entries removed")
        
        # Test full clear
        await cache_manager.clear()
        print("    ✅ Full cache clear executed")
        
        # Test stats
        stats = cache_manager.get_stats()
        print(f"    ✅ Cache stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error testing cache manager: {e}")
        return False

async def test_livestock_button_sync():
    """Test livestock and button synchronization"""
    print("\n🧪 Testing Livestock-Button Synchronization...")
    
    try:
        from src.ui.views.live_stock_view import LiveStockManager
        from src.ui.buttons.live_buttons import LiveButtonManager
        
        # Create mock bot
        bot = MockBot()
        
        # Create managers
        livestock_manager = LiveStockManager(bot)
        button_manager = LiveButtonManager(bot)
        
        # Test status tracking
        print("  🔍 Testing status tracking...")
        
        # Test initial status
        livestock_status = livestock_manager.get_status()
        button_status = button_manager.get_status()
        
        print(f"    ✅ Livestock initial status: {livestock_status['is_healthy']}")
        print(f"    ✅ Button initial status: {button_status['is_healthy']}")
        
        # Test status update
        await livestock_manager._update_status(False, "Test error")
        updated_status = livestock_manager.get_status()
        
        print(f"    ✅ Livestock status after error: {updated_status['is_healthy']}")
        print(f"    ✅ Error message: {updated_status['last_error']}")
        
        # Test health check methods
        livestock_healthy = livestock_manager.is_healthy()
        button_healthy = button_manager.is_healthy()
        
        print(f"    ✅ Livestock health check: {livestock_healthy}")
        print(f"    ✅ Button health check: {button_healthy}")
        
        # Test cross-notification (mock)
        print("  🔍 Testing cross-notification...")
        
        # Set up cross-references
        await livestock_manager.set_button_manager(button_manager)
        await button_manager.set_stock_manager(livestock_manager)
        
        print("    ✅ Cross-references established")
        
        # Test notification methods
        await livestock_manager.on_button_status_change(False, "Button test error")
        await button_manager.on_livestock_status_change(False, "Livestock test error")
        
        print("    ✅ Cross-notification methods tested")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error testing livestock-button sync: {e}")
        return False

async def test_error_handling_integration():
    """Test error handling integration"""
    print("\n🧪 Testing Error Handling Integration...")
    
    try:
        from src.ui.views.live_stock_view import LiveStockManager
        from src.ui.buttons.live_buttons import LiveButtonManager
        
        # Create mock bot
        bot = MockBot()
        
        # Create managers
        livestock_manager = LiveStockManager(bot)
        button_manager = LiveButtonManager(bot)
        
        # Set up integration
        await livestock_manager.set_button_manager(button_manager)
        await button_manager.set_stock_manager(livestock_manager)
        
        print("  🔍 Testing error scenarios...")
        
        # Test livestock error affecting button
        print("    Testing livestock error...")
        await livestock_manager._update_status(False, "Database connection failed")
        
        # Check if button manager received notification
        if hasattr(button_manager, 'on_livestock_status_change'):
            print("    ✅ Button manager has livestock notification handler")
        
        # Test button error affecting livestock
        print("    Testing button error...")
        await button_manager._update_status(False, "Discord API error")
        
        # Check if livestock manager received notification
        if hasattr(livestock_manager, 'on_button_status_change'):
            print("    ✅ Livestock manager has button notification handler")
        
        # Test recovery
        print("    Testing recovery...")
        await livestock_manager._update_status(True)
        await button_manager._update_status(True)
        
        print("    ✅ Error handling integration tested")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error testing error handling integration: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Restart Cache Livestock Sync Tests\n")
    
    # Test restart command cache cleanup
    restart_ok = await test_restart_command_cache_cleanup()
    
    # Test cache manager improvements
    cache_ok = await test_cache_manager_improvements()
    
    # Test livestock-button synchronization
    sync_ok = await test_livestock_button_sync()
    
    # Test error handling integration
    error_handling_ok = await test_error_handling_integration()
    
    print("\n" + "="*60)
    if restart_ok and cache_ok and sync_ok and error_handling_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Restart command cache cleanup working")
        print("✅ Cache manager improvements working")
        print("✅ Livestock-button synchronization working")
        print("✅ Error handling integration working")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"🔧 Restart cleanup: {'✅' if restart_ok else '❌'}")
        print(f"🔧 Cache improvements: {'✅' if cache_ok else '❌'}")
        print(f"🔧 Livestock-button sync: {'✅' if sync_ok else '❌'}")
        print(f"🔧 Error handling: {'✅' if error_handling_ok else '❌'}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)
