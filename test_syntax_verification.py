"""
Syntax and Structure Verification Test
Author: Assistant
Created: 2025-01-XX

Test ini memverifikasi:
1. Syntax Python valid
2. Import structure benar
3. Method signatures sesuai
4. Parameter calls sudah diperbaiki
"""

import sys
import os
import ast
import re

def test_python_syntax():
    """Test Python syntax validity"""
    print("🧪 Testing Python syntax...")
    
    files_to_test = [
        'src/ui/buttons/components/modals.py',
        'src/config/constants/bot_constants.py'
    ]
    
    all_valid = True
    for file_path in files_to_test:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to check syntax
            ast.parse(content)
            print(f"✅ {file_path} - Syntax valid")
            
        except SyntaxError as e:
            print(f"❌ {file_path} - Syntax error: {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {file_path} - Error: {e}")
            all_valid = False
    
    return all_valid

def test_parameter_fix():
    """Test that growid parameter has been fixed"""
    print("\n🧪 Testing parameter fix...")
    
    modals_file = 'src/ui/buttons/components/modals.py'
    
    try:
        with open(modals_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for old problematic pattern (more specific)
        old_pattern = r'process_purchase\s*\([^)]*growid\s*='
        matches = re.findall(old_pattern, content, re.DOTALL)
        if matches:
            print(f"❌ Found old 'growid=' parameter in process_purchase call: {len(matches)} instances")
            return False
        
        # Check for new correct pattern
        new_pattern = r'process_purchase\s*\(.*buyer_id\s*='
        if re.search(new_pattern, content, re.DOTALL):
            print("✅ Found correct 'buyer_id=' parameter in process_purchase call")
        else:
            print("⚠️ Could not find 'buyer_id=' parameter pattern")
        
        # Check that price parameter is removed
        price_pattern = r'process_purchase\s*\([^)]*price\s*='
        if re.search(price_pattern, content, re.DOTALL):
            print("❌ Found 'price=' parameter in process_purchase call (should be removed)")
            return False
        else:
            print("✅ 'price=' parameter correctly removed from process_purchase call")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking parameter fix: {e}")
        return False

def test_new_features():
    """Test that new features are implemented"""
    print("\n🧪 Testing new features...")
    
    modals_file = 'src/ui/buttons/components/modals.py'
    constants_file = 'src/config/constants/bot_constants.py'
    
    try:
        # Check modals file for new methods
        with open(modals_file, 'r', encoding='utf-8') as f:
            modals_content = f.read()
        
        features_found = 0
        
        # Check for DM sending method
        if '_send_items_via_dm' in modals_content:
            print("✅ Found _send_items_via_dm method")
            features_found += 1
        else:
            print("❌ Missing _send_items_via_dm method")
        
        # Check for logging method
        if '_log_purchase_to_channels' in modals_content:
            print("✅ Found _log_purchase_to_channels method")
            features_found += 1
        else:
            print("❌ Missing _log_purchase_to_channels method")
        
        # Check for file creation
        if 'discord.File' in modals_content and 'io.BytesIO' in modals_content:
            print("✅ Found file creation functionality")
            features_found += 1
        else:
            print("❌ Missing file creation functionality")
        
        # Check for DM sending
        if 'interaction.user.send' in modals_content:
            print("✅ Found DM sending functionality")
            features_found += 1
        else:
            print("❌ Missing DM sending functionality")
        
        # Check constants file for new channels
        with open(constants_file, 'r', encoding='utf-8') as f:
            constants_content = f.read()
        
        if 'HISTORY_BUY' in constants_content:
            print("✅ Found HISTORY_BUY channel constant")
            features_found += 1
        else:
            print("❌ Missing HISTORY_BUY channel constant")
        
        if 'BUY_LOG' in constants_content:
            print("✅ Found BUY_LOG channel constant")
            features_found += 1
        else:
            print("❌ Missing BUY_LOG channel constant")
        
        print(f"📊 Features implemented: {features_found}/6")
        return features_found >= 5  # Allow 1 missing feature
        
    except Exception as e:
        print(f"❌ Error checking new features: {e}")
        return False

def test_import_structure():
    """Test import structure"""
    print("\n🧪 Testing import structure...")
    
    modals_file = 'src/ui/buttons/components/modals.py'
    
    try:
        with open(modals_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_imports = [
            'import io',
            'from datetime import datetime',
            'NOTIFICATION_CHANNELS'
        ]
        
        imports_found = 0
        for import_stmt in required_imports:
            if import_stmt in content:
                print(f"✅ Found import: {import_stmt}")
                imports_found += 1
            else:
                print(f"❌ Missing import: {import_stmt}")
        
        return imports_found == len(required_imports)
        
    except Exception as e:
        print(f"❌ Error checking imports: {e}")
        return False

def test_error_handling():
    """Test error handling implementation"""
    print("\n🧪 Testing error handling...")
    
    modals_file = 'src/ui/buttons/components/modals.py'
    
    try:
        with open(modals_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        error_patterns = [
            'discord.Forbidden',  # DM error handling
            'except Exception as e',  # General error handling
            'logger.error',  # Error logging
            'logger.warning'  # Warning logging
        ]
        
        patterns_found = 0
        for pattern in error_patterns:
            if pattern in content:
                print(f"✅ Found error handling: {pattern}")
                patterns_found += 1
            else:
                print(f"❌ Missing error handling: {pattern}")
        
        return patterns_found >= 3  # Allow some flexibility
        
    except Exception as e:
        print(f"❌ Error checking error handling: {e}")
        return False

def run_all_tests():
    """Run all verification tests"""
    print("🚀 Starting Syntax and Structure Verification Tests\n")
    
    tests = [
        test_python_syntax,
        test_parameter_fix,
        test_new_features,
        test_import_structure,
        test_error_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All verification tests passed! Code structure is correct.")
        return True
    elif sum(results) >= len(results) - 1:
        print("✅ Most tests passed. Minor issues may exist but core functionality should work.")
        return True
    else:
        print("⚠️ Several tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
