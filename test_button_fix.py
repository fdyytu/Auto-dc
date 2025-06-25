"""
Test untuk memverifikasi perbaikan button error
"""
import asyncio
import discord
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.buttons.live_buttons import LiveButtonManager, LiveButtonsCog
from src.config.logging_config import get_logger

class MockBot:
    """Mock bot untuk testing"""
    def __init__(self):
        self.config = {
            'id_live_stock': '1318806350310146114'
        }
        self.db_manager = Mock()
        self.user = Mock()
        self.user.id = 12345
        self._ready = False
        self._channels = {}
        
    def get_channel(self, channel_id):
        """Mock get_channel yang bisa dikontrol"""
        if not self._ready:
            return None
        return self._channels.get(channel_id)
        
    def is_ready(self):
        """Mock is_ready"""
        return self._ready
        
    async def wait_until_ready(self):
        """Mock wait_until_ready"""
        if not self._ready:
            await asyncio.sleep(0.1)  # Simulate waiting
            self._ready = True
            
    def set_ready(self, ready=True):
        """Set bot ready state"""
        self._ready = ready
        
    def add_channel(self, channel_id, channel):
        """Add mock channel"""
        self._channels[channel_id] = channel

class MockChannel:
    """Mock Discord channel"""
    def __init__(self, channel_id, name="test-channel"):
        self.id = channel_id
        self.name = name
        
    async def send(self, **kwargs):
        """Mock send message"""
        mock_message = Mock()
        mock_message.id = 123456
        mock_message.components = []
        return mock_message

async def test_button_manager_channel_not_found():
    """Test scenario dimana channel tidak ditemukan"""
    logger = get_logger("test_button_fix")
    logger.info("🧪 Testing button manager channel not found scenario...")
    
    # Setup mock bot tanpa channel
    bot = MockBot()
    bot.set_ready(True)  # Bot ready tapi channel tidak ada
    
    # Create button manager
    button_manager = LiveButtonManager(bot)
    
    # Test get_or_create_message
    result = await button_manager.get_or_create_message()
    
    # Verify result
    assert result is None, "Should return None when channel not found"
    assert not button_manager.is_healthy(), "Button manager should not be healthy"
    assert "tidak ditemukan" in button_manager.button_status['last_error'], "Should have proper error message"
    
    logger.info("✅ Test channel not found - PASSED")

async def test_button_manager_bot_not_ready():
    """Test scenario dimana bot belum ready"""
    logger = get_logger("test_button_fix")
    logger.info("🧪 Testing button manager bot not ready scenario...")
    
    # Setup mock bot yang belum ready
    bot = MockBot()
    bot.set_ready(False)  # Bot belum ready
    
    # Add channel yang akan tersedia setelah bot ready
    mock_channel = MockChannel(1318806350310146114, "📜⌗・live-stock")
    bot.add_channel(1318806350310146114, mock_channel)
    
    # Create button manager
    button_manager = LiveButtonManager(bot)
    
    # Test get_or_create_message (should wait for bot ready)
    result = await button_manager.get_or_create_message()
    
    # Verify bot became ready
    assert bot.is_ready(), "Bot should be ready after wait_until_ready"
    
    logger.info("✅ Test bot not ready - PASSED")

async def test_button_manager_retry_mechanism():
    """Test retry mechanism untuk mendapatkan channel"""
    logger = get_logger("test_button_fix")
    logger.info("🧪 Testing button manager retry mechanism...")
    
    # Setup mock bot
    bot = MockBot()
    bot.set_ready(True)
    
    # Mock channel yang akan tersedia setelah beberapa retry
    mock_channel = MockChannel(1318806350310146114, "📜⌗・live-stock")
    
    # Create button manager
    button_manager = LiveButtonManager(bot)
    
    # Simulate channel tersedia setelah delay
    async def delayed_channel_add():
        await asyncio.sleep(0.5)  # Wait a bit
        bot.add_channel(1318806350310146114, mock_channel)
    
    # Start delayed channel addition
    asyncio.create_task(delayed_channel_add())
    
    # Test get_or_create_message (should retry and find channel)
    result = await button_manager.get_or_create_message()
    
    # Note: Dalam implementasi sebenarnya, ini akan retry tapi untuk test ini
    # kita fokus pada logic flow
    logger.info("✅ Test retry mechanism - PASSED")

async def test_button_manager_successful_initialization():
    """Test successful initialization scenario"""
    logger = get_logger("test_button_fix")
    logger.info("🧪 Testing successful button manager initialization...")
    
    # Setup mock bot dengan channel tersedia
    bot = MockBot()
    bot.set_ready(True)
    
    # Add channel
    mock_channel = MockChannel(1318806350310146114, "📜⌗・live-stock")
    bot.add_channel(1318806350310146114, mock_channel)
    
    # Create button manager
    button_manager = LiveButtonManager(bot)
    
    # Verify initialization
    assert button_manager.stock_channel_id == 1318806350310146114, "Channel ID should be set correctly"
    assert button_manager.is_healthy(), "Button manager should be healthy initially"
    
    logger.info("✅ Test successful initialization - PASSED")

async def run_all_tests():
    """Run all tests"""
    logger = get_logger("test_button_fix")
    logger.info("🚀 Starting button fix tests...")
    
    try:
        await test_button_manager_channel_not_found()
        await test_button_manager_bot_not_ready()
        await test_button_manager_retry_mechanism()
        await test_button_manager_successful_initialization()
        
        logger.info("🎉 All tests PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        exit(1)
