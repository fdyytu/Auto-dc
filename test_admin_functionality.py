#!/usr/bin/env python3
"""
Test script untuk memverifikasi functionality admin detection
Simulasi lengkap tanpa perlu token Discord
"""

import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from src.bot.config import config_manager
from src.cogs.admin import AdminCog
from src.cogs.debug import DebugCog

class MockRole:
    """Mock Discord Role object"""
    def __init__(self, role_id, name="TestRole"):
        self.id = role_id
        self.name = name

class MockUser:
    """Mock Discord User object"""
    def __init__(self, user_id, username="TestUser", role_ids=None):
        self.id = user_id
        self.name = username
        self.discriminator = "0001"
        self.roles = [MockRole(role_id, f"Role{role_id}") for role_id in (role_ids or [])]

class MockContext:
    """Mock Discord Context object"""
    def __init__(self, user, channel_id=123456789):
        self.author = user
        self.channel = Mock()
        self.channel.id = channel_id
        self.send = AsyncMock()

class MockBot:
    """Mock Discord Bot object"""
    def __init__(self):
        self.db_manager = Mock()
        self.config = config_manager.load_config()

async def test_admin_cog_functionality():
    """Test AdminCog functionality"""
    print("🧪 Testing AdminCog Functionality...")
    
    try:
        # Setup mock bot
        bot = MockBot()
        admin_cog = AdminCog(bot)
        
        # Get config values
        admin_id = bot.config.get('admin_id')
        admin_role_id = bot.config.get('roles', {}).get('admin')
        
        print(f"📋 Admin ID: {admin_id}")
        print(f"📋 Admin Role ID: {admin_role_id}")
        
        # Test cases
        test_cases = [
            {
                "name": "Valid Admin by ID",
                "user": MockUser(admin_id, "AdminUser"),
                "expected": True
            },
            {
                "name": "Valid Admin by Role",
                "user": MockUser(999999999, "RoleAdmin", [admin_role_id]),
                "expected": True
            },
            {
                "name": "Valid Admin by both ID and Role",
                "user": MockUser(admin_id, "SuperAdmin", [admin_role_id]),
                "expected": True
            },
            {
                "name": "Invalid User - No Admin Access",
                "user": MockUser(123456789, "RegularUser", [987654321]),
                "expected": False
            },
            {
                "name": "Invalid User - No Roles",
                "user": MockUser(123456789, "NoRoleUser"),
                "expected": False
            }
        ]
        
        # Run tests
        all_passed = True
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['name']}")
            
            # Create mock context
            ctx = MockContext(test_case['user'])
            
            # Test admin check
            try:
                result = await admin_cog.cog_check(ctx)
                
                if result == test_case['expected']:
                    print(f"   ✅ PASS: Expected {test_case['expected']}, got {result}")
                else:
                    print(f"   ❌ FAIL: Expected {test_case['expected']}, got {result}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ AdminCog test failed: {e}")
        return False

async def test_debug_cog_functionality():
    """Test DebugCog functionality"""
    print("\n🧪 Testing DebugCog Functionality...")
    
    try:
        # Setup mock bot
        bot = MockBot()
        debug_cog = DebugCog(bot)
        
        # Test debug admin command
        print("\n🔍 Testing debugadmin command...")
        test_user = MockUser(123456789, "TestUser", [987654321])
        ctx = MockContext(test_user)
        
        # Mock the send method to capture embed
        sent_embeds = []
        async def mock_send(embed=None, **kwargs):
            if embed:
                sent_embeds.append(embed)
        ctx.send = mock_send
        
        # Run debug admin command - call as bound method
        debug_admin_method = getattr(debug_cog, 'debug_admin')
        await debug_admin_method(ctx)
        
        if sent_embeds:
            embed = sent_embeds[0]
            print(f"   ✅ Debug embed created: {embed.title}")
            print(f"   ✅ Embed has {len(embed.fields)} fields")
        else:
            print("   ❌ No embed was sent")
            return False
        
        # Test config info command
        print("\n🔍 Testing configinfo command...")
        sent_embeds.clear()
        config_info_method = getattr(debug_cog, 'config_info')
        await config_info_method(ctx)
        
        if sent_embeds:
            embed = sent_embeds[0]
            print(f"   ✅ Config embed created: {embed.title}")
            print(f"   ✅ Embed has {len(embed.fields)} fields")
        else:
            print("   ❌ No config embed was sent")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ DebugCog test failed: {e}")
        return False

async def test_config_loading():
    """Test config loading"""
    print("\n🧪 Testing Config Loading...")
    
    try:
        config = config_manager.load_config()
        
        # Check required keys
        required_keys = ['admin_id', 'guild_id', 'roles']
        for key in required_keys:
            if key not in config:
                print(f"   ❌ Missing config key: {key}")
                return False
            print(f"   ✅ Config key present: {key}")
        
        # Check admin config specifically
        admin_id = config.get('admin_id')
        admin_role = config.get('roles', {}).get('admin')
        
        if not isinstance(admin_id, int):
            print(f"   ❌ admin_id should be int, got {type(admin_id)}")
            return False
        
        if not isinstance(admin_role, int):
            print(f"   ❌ admin role should be int, got {type(admin_role)}")
            return False
        
        print(f"   ✅ Admin ID: {admin_id} (type: {type(admin_id)})")
        print(f"   ✅ Admin Role: {admin_role} (type: {type(admin_role)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Config loading test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Admin Functionality Tests\n")
    
    # Run all tests
    config_ok = await test_config_loading()
    admin_ok = await test_admin_cog_functionality()
    debug_ok = await test_debug_cog_functionality()
    
    print("\n" + "="*60)
    
    if config_ok and admin_ok and debug_ok:
        print("🎉 ALL FUNCTIONALITY TESTS PASSED!")
        print("✅ Admin detection berfungsi dengan benar")
        print("✅ Debug commands berfungsi dengan benar")
        print("✅ Config loading berfungsi dengan benar")
        print("✅ Bot siap untuk production")
        return True
    else:
        print("❌ SOME FUNCTIONALITY TESTS FAILED!")
        print("🔧 Please check the failed components")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
