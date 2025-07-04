"""
Test script untuk donation service
"""

import sys
import os
sys.path.append('/home/user/workspace')
sys.path.append('/home/user/workspace/src')

# Mock discord objects untuk testing
class MockMessage:
    def __init__(self, content, embeds=None):
        self.content = content
        self.embeds = embeds or []
        self.channel = MockChannel()
        self.author = MockUser()

class MockChannel:
    def __init__(self):
        self.sent_messages = []
    
    async def send(self, message):
        self.sent_messages.append(message)
        print(f"Bot Response: {message}")

class MockUser:
    def __init__(self):
        self.bot = False

class MockBot:
    def __init__(self):
        self.config = {'id_donation_log': 1318806351228698680}

class MockBalanceManager:
    async def get_user(self, growid):
        # Mock response untuk testing
        if growid.lower() == 'fdy':
            from src.config.constants.bot_constants import Balance
            
            class MockUserData:
                def __init__(self):
                    self.balance = Balance(1000, 5, 2)  # 1000 WL, 5 DL, 2 BGL
            
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
        print(f"Balance updated for {growid}: {new_balance}")
        return True

# Test donation service
async def test_donation_service():
    print("Testing Donation Service...")
    
    from src.services.donation_service import DonationManager
    
    # Setup
    bot = MockBot()
    manager = DonationManager(bot)
    manager.balance_manager = MockBalanceManager()
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid donation message',
            'content': 'GrowID: Fdy\nDeposit: 1 Diamond Lock',
            'expected': 'Successfully filled'
        },
        {
            'name': 'Invalid GrowID',
            'content': 'GrowID: InvalidUser\nDeposit: 1 Diamond Lock',
            'expected': 'Failed to find growid'
        },
        {
            'name': 'Multiple items',
            'content': 'GrowID: Fdy\nDeposit: 5 World Lock, 2 Diamond Lock',
            'expected': 'Successfully filled'
        },
        {
            'name': 'Invalid format',
            'content': 'Random message without proper format',
            'expected': 'No response (ignored)'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        print(f"Input: {test_case['content']}")
        
        message = MockMessage(test_case['content'])
        await manager.process_donation_message(message)
        
        if message.channel.sent_messages:
            print(f"Expected: {test_case['expected']}")
            print("✅ Test completed")
        else:
            print("No response sent (message ignored)")
        
        print("-" * 50)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_donation_service())
