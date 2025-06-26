#!/usr/bin/env python3
"""
Test Script untuk Admin Refactor
Memverifikasi semua perbaikan yang telah dilakukan
"""

import sys
import os
import importlib.util
from pathlib import Path

def test_file_structure():
    """Test struktur file admin yang baru"""
    print("🏗️  Testing file structure...")
    
    required_files = [
        'src/cogs/admin.py',
        'src/cogs/admin_base.py',
        'src/cogs/admin_store.py', 
        'src/cogs/admin_balance.py',
        'src/cogs/admin_system.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path} exists")
        else:
            print(f"  ❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_file_sizes():
    """Test ukuran file sesuai requirement"""
    print("\n📏 Testing file sizes...")
    
    files_to_check = {
        'src/cogs/admin.py': 50,           # Main entry point
        'src/cogs/admin_base.py': 100,     # Base class
        'src/cogs/admin_store.py': 150,    # Store management
        'src/cogs/admin_balance.py': 100,  # Balance management
        'src/cogs/admin_system.py': 150    # System management
    }
    
    all_good = True
    for file_path, max_lines in files_to_check.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = len(f.readlines())
            
            if lines <= max_lines:
                print(f"  ✅ {file_path}: {lines} lines (≤{max_lines})")
            else:
                print(f"  ⚠️  {file_path}: {lines} lines (>{max_lines})")
                all_good = False
        else:
            print(f"  ❌ {file_path}: File not found")
            all_good = False
    
    return all_good

def test_imports():
    """Test apakah semua file bisa diimport"""
    print("\n📦 Testing imports...")
    
    files_to_import = [
        ('src/cogs/admin_base.py', 'admin_base'),
        ('src/cogs/admin_store.py', 'admin_store'),
        ('src/cogs/admin_balance.py', 'admin_balance'),
        ('src/cogs/admin_system.py', 'admin_system')
    ]
    
    all_imported = True
    for file_path, module_name in files_to_import:
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            print(f"  ✅ {module_name} imported successfully")
        except Exception as e:
            print(f"  ❌ {module_name} import failed: {e}")
            all_imported = False
    
    return all_imported

def test_addbal_command():
    """Test implementasi command addbal"""
    print("\n💰 Testing addbal command...")
    
    try:
        with open('src/cogs/admin_balance.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('@commands.command(name="addbal")', 'Command decorator'),
            ('async def add_balance(', 'Function definition'),
            ('growid: str', 'GrowID parameter'),
            ('amount: str', 'Amount parameter'),
            ('balance_type: str', 'Balance type parameter'),
            ('validate_amount', 'Input validation'),
            ('WL', 'WL balance support'),
            ('DL', 'DL balance support'),
            ('BGL', 'BGL balance support'),
            ('try:', 'Error handling')
        ]
        
        all_found = True
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} missing")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ❌ Error reading admin_balance.py: {e}")
        return False

def test_growid_case_fix():
    """Test perbaikan grow id case preservation"""
    print("\n🔤 Testing grow ID case preservation...")
    
    files_to_check = [
        'src/ui/modals/register_modal.py',
        'src/ui/buttons/components/modals.py'
    ]
    
    all_fixed = True
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if '.upper()' in content:
                print(f"  ❌ {file_path}: Still contains .upper()")
                all_fixed = False
            else:
                print(f"  ✅ {file_path}: .upper() removed")
                
        except Exception as e:
            print(f"  ❌ Error reading {file_path}: {e}")
            all_fixed = False
    
    return all_fixed

def test_validators():
    """Test validator yang sudah diperbaiki"""
    print("\n🧪 Testing validators...")
    
    try:
        sys.path.append('.')
        from src.utils.validators import input_validator
        
        # Test validate_amount (yang baru ditambahkan)
        test_cases = [
            ('1000', True),
            ('500', True), 
            ('0', False),
            ('-100', False),
            ('abc', False)
        ]
        
        all_passed = True
        for test_input, expected in test_cases:
            result = input_validator.validate_amount(test_input)
            passed = bool(result) == expected
            
            if passed:
                print(f"  ✅ validate_amount('{test_input}') = {result}")
            else:
                print(f"  ❌ validate_amount('{test_input}') = {result} (expected {expected})")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ Error testing validators: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Admin Refactor Tests\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("File Sizes", test_file_sizes),
        ("Imports", test_imports),
        ("AddBal Command", test_addbal_command),
        ("Grow ID Case Fix", test_growid_case_fix),
        ("Validators", test_validators)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Admin refactor completed successfully.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
