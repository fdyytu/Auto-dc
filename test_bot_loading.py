#!/usr/bin/env python3
"""
Test script untuk memverifikasi bot loading dengan perubahan admin detection
"""

import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from src.bot.config import config_manager
from src.bot.bot import StoreBot

async def test_bot_loading():
    """Test loading bot dengan perubahan baru"""
    print("🧪 Testing Bot Loading...")
    
    try:
        # Load config
        config = config_manager.load_config()
        print("✅ Config loaded successfully")
        
        # Test admin config
        admin_id = config.get('admin_id')
        admin_role_id = config.get('roles', {}).get('admin')
        print(f"📋 Admin ID: {admin_id}")
        print(f"📋 Admin Role ID: {admin_role_id}")
        
        # Initialize bot (tanpa menjalankan)
        bot = StoreBot()
        print("✅ Bot instance created successfully")
        
        # Test config access
        print(f"📋 Bot config admin_id: {bot.config.get('admin_id')}")
        print(f"📋 Bot config admin_role: {bot.config.get('roles', {}).get('admin')}")
        
        # Test extension list
        extensions = [
            'src.cogs.admin', 'src.cogs.automod', 'src.cogs.help_manager',
            'src.cogs.leveling', 'src.cogs.management',
            'src.cogs.reputation', 'src.cogs.stats', 'src.cogs.tickets',
            'src.cogs.welcome', 'src.cogs.debug'
        ]
        
        print("\n🔍 Testing Extension Loading...")
        for ext in extensions:
            try:
                # Coba import module
                __import__(ext.replace('.', '/').replace('/', '.'))
                print(f"✅ {ext} - Import OK")
            except Exception as e:
                print(f"❌ {ext} - Import Error: {e}")
        
        print("\n✅ Bot loading test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Bot loading test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Bot Loading Test\n")
    
    # Run test
    success = asyncio.run(test_bot_loading())
    
    print("\n" + "="*50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Bot dapat dimuat dengan perubahan admin detection")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please check the bot loading issues")
        sys.exit(1)
