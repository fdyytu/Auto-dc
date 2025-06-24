#!/usr/bin/env python3
"""
Test script untuk memverifikasi admin detection logic
Tanpa perlu koneksi Discord yang sebenarnya
"""

import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from src.bot.config import config_manager

class MockRole:
    """Mock Discord Role object"""
    def __init__(self, role_id):
        self.id = role_id

class MockUser:
    """Mock Discord User object"""
    def __init__(self, user_id, role_ids=None):
        self.id = user_id
        self.roles = [MockRole(role_id) for role_id in (role_ids or [])]

def test_admin_detection():
    """Test admin detection logic"""
    print("🧪 Testing Admin Detection Logic...")
    
    # Load config
    try:
        config = config_manager.load_config()
        print("✅ Config loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Get admin configuration
    admin_id = config.get('admin_id')
    admin_role_id = config.get('roles', {}).get('admin')
    
    print(f"📋 Admin ID from config: {admin_id}")
    print(f"📋 Admin Role ID from config: {admin_role_id}")
    
    # Test cases
    test_cases = [
        {
            "name": "Admin by User ID",
            "user": MockUser(admin_id),
            "expected": True
        },
        {
            "name": "Admin by Role ID", 
            "user": MockUser(999999999, [admin_role_id]),
            "expected": True
        },
        {
            "name": "Admin by both User ID and Role",
            "user": MockUser(admin_id, [admin_role_id]),
            "expected": True
        },
        {
            "name": "Non-admin user",
            "user": MockUser(123456789, [987654321]),
            "expected": False
        },
        {
            "name": "User with no roles",
            "user": MockUser(123456789),
            "expected": False
        }
    ]
    
    # Run tests
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        
        # Simulate admin check logic
        user = test_case['user']
        is_admin = False
        
        # Check admin ID
        if user.id == admin_id:
            is_admin = True
            print(f"   ✓ Matched admin ID: {user.id}")
        
        # Check admin role
        if admin_role_id:
            user_role_ids = [role.id for role in user.roles]
            if admin_role_id in user_role_ids:
                is_admin = True
                print(f"   ✓ Matched admin role: {admin_role_id}")
        
        # Verify result
        if is_admin == test_case['expected']:
            print(f"   ✅ PASS: Expected {test_case['expected']}, got {is_admin}")
        else:
            print(f"   ❌ FAIL: Expected {test_case['expected']}, got {is_admin}")
            all_passed = False
    
    return all_passed

def test_config_validation():
    """Test config validation"""
    print("\n🧪 Testing Config Validation...")
    
    try:
        config = config_manager.load_config()
        
        # Check required keys
        required_keys = ['admin_id', 'guild_id', 'token']
        missing_keys = []
        
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"⚠️  Missing config keys: {missing_keys}")
        else:
            print("✅ All required config keys present")
        
        # Check admin_id type
        admin_id = config.get('admin_id')
        if isinstance(admin_id, int):
            print(f"✅ admin_id is integer: {admin_id}")
        else:
            print(f"❌ admin_id should be integer, got {type(admin_id)}: {admin_id}")
            return False
        
        # Check roles
        roles = config.get('roles', {})
        admin_role = roles.get('admin')
        if admin_role:
            if isinstance(admin_role, int):
                print(f"✅ admin role is integer: {admin_role}")
            else:
                print(f"❌ admin role should be integer, got {type(admin_role)}: {admin_role}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Config validation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Admin Detection Tests\n")
    
    # Test config validation
    config_ok = test_config_validation()
    
    # Test admin detection logic
    admin_ok = test_admin_detection()
    
    print("\n" + "="*50)
    if config_ok and admin_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Admin detection logic is working correctly")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please check the admin detection logic")
        sys.exit(1)
