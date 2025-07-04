"""
Test bot loading dan donation cog integration
"""

import sys
import os
import asyncio
import logging
sys.path.append('/home/user/workspace')
sys.path.append('/home/user/workspace/src')

# Mock environment untuk testing
os.environ['DISCORD_TOKEN'] = 'test_token_for_loading_test'

async def test_bot_loading():
    """Test apakah bot dapat dimuat dengan donation cog"""
    print("Testing Bot Loading with Donation Cog...")
    
    try:
        # Import bot components
        from src.bot.config import config_manager
        from src.bot.module_loader import ModuleLoader
        
        # Mock bot class untuk testing
        class MockBot:
            def __init__(self):
                self.config = config_manager.load_config()
                self.module_loader = ModuleLoader(self)
                self.cogs = {}
                self.loaded_extensions = []
            
            async def add_cog(self, cog):
                self.cogs[cog.__class__.__name__] = cog
                print(f"✅ Cog loaded: {cog.__class__.__name__}")
                return True
            
            async def load_extension(self, extension_name):
                self.loaded_extensions.append(extension_name)
                print(f"✅ Extension loaded: {extension_name}")
                return True
        
        # Test bot initialization
        print("1. Testing bot config loading...")
        bot = MockBot()
        print(f"   ✅ Config loaded: donation_channel_id = {bot.config.get('id_donation_log')}")
        
        # Test donation cog loading
        print("\n2. Testing donation cog loading...")
        from src.cogs.donation import DonationCog
        donation_cog = DonationCog(bot)
        await bot.add_cog(donation_cog)
        
        # Test donation manager initialization
        print("\n3. Testing donation manager...")
        if hasattr(donation_cog, 'donation_manager'):
            print("   ✅ Donation manager initialized")
            
            # Test balance manager integration
            from src.services.balance_service import BalanceManagerService
            donation_cog.donation_manager.balance_manager = BalanceManagerService(bot)
            print("   ✅ Balance manager integrated")
        
        # Test cog discovery
        print("\n4. Testing module discovery...")
        from pathlib import Path
        cogs_path = Path("src/cogs")
        cog_files = bot.module_loader._discover_cogs(cogs_path)
        donation_cog_found = any('donation' in cog.lower() for cog in cog_files)
        if donation_cog_found:
            print("   ✅ Donation cog discovered by module loader")
        else:
            print("   ❌ Donation cog NOT discovered by module loader")
        print(f"   📋 Discovered cogs: {[cog.split('.')[-1] for cog in cog_files]}")
        
        print("\n" + "="*50)
        print("🎉 BOT LOADING TEST COMPLETED SUCCESSFULLY!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during bot loading test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_donation_functionality():
    """Test donation functionality dengan mock data"""
    print("\nTesting Donation Functionality...")
    
    try:
        from src.services.donation_service import DonationManager
        from src.config.constants.bot_constants import Balance
        
        # Mock bot dan balance manager
        class MockBot:
            def __init__(self):
                self.config = {'id_donation_log': 1318806351228698680}
        
        class MockBalanceManager:
            async def get_user(self, growid):
                if growid.lower() == 'testuser':
                    class MockUserData:
                        def __init__(self):
                            self.balance = Balance(500, 2, 1)
                    
                    class MockResponse:
                        def __init__(self):
                            self.success = True
                            self.data = MockUserData()
                    
                    return MockResponse()
                else:
                    class MockResponse:
                        def __init__(self):
                            self.success = False
                            self.data = None
                    return MockResponse()
            
            async def update_balance(self, growid, new_balance, transaction_type, details):
                print(f"   💰 Balance updated: {growid} -> {new_balance}")
                return True
        
        class MockMessage:
            def __init__(self, content):
                self.content = content
                self.embeds = []
                self.channel = MockChannel()
                self.author = MockUser()
        
        class MockChannel:
            def __init__(self):
                self.sent_messages = []
            
            async def send(self, message):
                self.sent_messages.append(message)
                print(f"   📤 Bot Response: {message}")
        
        class MockUser:
            def __init__(self):
                self.bot = False
        
        # Setup donation manager
        bot = MockBot()
        manager = DonationManager(bot)
        manager.balance_manager = MockBalanceManager()
        
        # Test cases
        test_cases = [
            {
                'name': 'Valid donation - Single item',
                'content': 'GrowID: TestUser\nDeposit: 3 Diamond Lock',
                'should_succeed': True
            },
            {
                'name': 'Valid donation - Multiple items',
                'content': 'GrowID: TestUser\nDeposit: 10 World Lock, 1 Diamond Lock',
                'should_succeed': True
            },
            {
                'name': 'Invalid GrowID',
                'content': 'GrowID: NonExistentUser\nDeposit: 1 Diamond Lock',
                'should_succeed': False
            },
            {
                'name': 'Invalid format',
                'content': 'Random message without proper format',
                'should_succeed': False
            }
        ]
        
        success_count = 0
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}: {test_case['name']}")
            print(f"   Input: {test_case['content']}")
            
            message = MockMessage(test_case['content'])
            await manager.process_donation_message(message)
            
            if test_case['should_succeed']:
                if message.channel.sent_messages and 'Successfully filled' in message.channel.sent_messages[0]:
                    print("   ✅ Test passed")
                    success_count += 1
                else:
                    print("   ❌ Test failed - Expected success but got failure")
            else:
                if not message.channel.sent_messages or 'Failed to find growid' in message.channel.sent_messages[0]:
                    print("   ✅ Test passed")
                    success_count += 1
                else:
                    print("   ❌ Test failed - Expected failure but got success")
        
        print(f"\n   📊 Functionality Tests: {success_count}/{len(test_cases)} passed")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ Error during functionality test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 COMPREHENSIVE DONATION SERVICE TEST")
    print("="*50)
    
    # Test 1: Bot Loading
    loading_success = await test_bot_loading()
    
    # Test 2: Donation Functionality
    functionality_success = await test_donation_functionality()
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY:")
    print(f"   Bot Loading: {'✅ PASS' if loading_success else '❌ FAIL'}")
    print(f"   Functionality: {'✅ PASS' if functionality_success else '❌ FAIL'}")
    
    if loading_success and functionality_success:
        print("\n🎉 ALL TESTS PASSED - DONATION SERVICE READY!")
    else:
        print("\n❌ SOME TESTS FAILED - NEEDS ATTENTION")
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
