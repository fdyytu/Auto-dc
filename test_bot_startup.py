"""
Bot Startup Test
Author: Assistant
Created: 2025-01-XX

Test ini memverifikasi bahwa bot dapat dijalankan tanpa error import
"""

import sys
import os

def test_bot_imports():
    """Test that bot can import all required modules"""
    print("🧪 Testing bot imports...")
    
    # Add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        # Test core imports
        print("  📦 Testing core imports...")
        from src.config.constants import bot_constants
        print("    ✅ bot_constants imported")
        
        from src.services import transaction_service
        print("    ✅ transaction_service imported")
        
        from src.ui.buttons.components import modals
        print("    ✅ modals imported")
        
        # Test specific classes
        print("  📦 Testing specific classes...")
        from src.ui.buttons.components.modals import QuantityModal, BuyModal, RegisterModal
        print("    ✅ Modal classes imported")
        
        from src.config.constants.bot_constants import NOTIFICATION_CHANNELS, COLORS, MESSAGES
        print("    ✅ Constants imported")
        
        # Test instantiation
        print("  📦 Testing class instantiation...")
        quantity_modal = QuantityModal("TEST", 10)
        print("    ✅ QuantityModal instantiated")
        
        buy_modal = BuyModal()
        print("    ✅ BuyModal instantiated")
        
        register_modal = RegisterModal()
        print("    ✅ RegisterModal instantiated")
        
        print("✅ All bot imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_channel_constants():
    """Test that channel constants are properly defined"""
    print("\n🧪 Testing channel constants...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from src.config.constants.bot_constants import NOTIFICATION_CHANNELS
        
        # Check required channels
        required_channels = ['HISTORY_BUY', 'BUY_LOG', 'TRANSACTIONS', 'SHOP']
        
        for channel in required_channels:
            if hasattr(NOTIFICATION_CHANNELS, channel):
                channel_id = getattr(NOTIFICATION_CHANNELS, channel)
                print(f"    ✅ {channel}: {channel_id}")
            else:
                print(f"    ❌ Missing channel: {channel}")
                return False
        
        print("✅ All required channels defined!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing channels: {e}")
        return False

def test_method_signatures():
    """Test that method signatures are correct"""
    print("\n🧪 Testing method signatures...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from src.ui.buttons.components.modals import QuantityModal, BuyModal
        
        # Test QuantityModal methods
        quantity_modal = QuantityModal("TEST", 10)
        
        if hasattr(quantity_modal, '_send_items_via_dm'):
            print("    ✅ QuantityModal._send_items_via_dm exists")
        else:
            print("    ❌ QuantityModal._send_items_via_dm missing")
            return False
            
        if hasattr(quantity_modal, '_log_purchase_to_channels'):
            print("    ✅ QuantityModal._log_purchase_to_channels exists")
        else:
            print("    ❌ QuantityModal._log_purchase_to_channels missing")
            return False
        
        # Test BuyModal methods
        buy_modal = BuyModal()
        
        if hasattr(buy_modal, '_send_items_via_dm'):
            print("    ✅ BuyModal._send_items_via_dm exists")
        else:
            print("    ❌ BuyModal._send_items_via_dm missing")
            return False
            
        if hasattr(buy_modal, '_log_purchase_to_channels'):
            print("    ✅ BuyModal._log_purchase_to_channels exists")
        else:
            print("    ❌ BuyModal._log_purchase_to_channels missing")
            return False
        
        print("✅ All method signatures correct!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing method signatures: {e}")
        return False

def run_startup_tests():
    """Run all startup tests"""
    print("🚀 Starting Bot Startup Tests\n")
    
    tests = [
        test_bot_imports,
        test_channel_constants,
        test_method_signatures
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print(f"\n📊 Startup Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All startup tests passed! Bot should start without import errors.")
        return True
    else:
        print("⚠️ Some startup tests failed. Bot may have import issues.")
        return False

if __name__ == "__main__":
    success = run_startup_tests()
    sys.exit(0 if success else 1)
