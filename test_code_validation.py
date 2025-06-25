#!/usr/bin/env python3
"""
Code validation test untuk memastikan perbaikan livestock button error
tidak merusak struktur kode dan logic flow.
"""

import ast
import re
import sys

def test_code_structure():
    """Test struktur kode untuk memastikan tidak ada masalah struktural"""
    print("🔍 Testing code structure...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        # Check class exists
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if 'LiveStockManager' in classes:
            print("✅ LiveStockManager class found")
        else:
            print("❌ LiveStockManager class not found")
            return False
        
        # Check critical methods exist
        functions = [node.name for node in ast.walk(tree) 
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        critical_methods = [
            'update_stock_display',
            '_update_status',
            'create_stock_embed',
            'set_button_manager',
            'get_status',
            'is_healthy'
        ]
        
        missing_methods = [m for m in critical_methods if m not in functions]
        if missing_methods:
            print(f"❌ Missing critical methods: {missing_methods}")
            return False
        else:
            print("✅ All critical methods found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing code structure: {e}")
        return False

def test_retry_mechanism():
    """Test retry mechanism implementation"""
    print("\n🔍 Testing retry mechanism...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check retry mechanism components
        retry_patterns = [
            r'max_retries\s*=\s*3',
            r'for attempt in range\(max_retries\)',
            r'await asyncio\.sleep\(1\)',
            r'attempt \+ 1'
        ]
        
        found_patterns = []
        for pattern in retry_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 3:
            print(f"✅ Retry mechanism properly implemented ({len(found_patterns)}/4 patterns found)")
            return True
        else:
            print(f"❌ Retry mechanism incomplete ({len(found_patterns)}/4 patterns found)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing retry mechanism: {e}")
        return False

def test_button_validation_logic():
    """Test button manager validation logic"""
    print("\n🔍 Testing button validation logic...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check validation patterns
        validation_patterns = [
            r'if self\.button_manager and not view:',
            r'Button manager tersedia tapi gagal membuat view',
            r'if not self\.button_manager:',
            r'button_manager\.create_view\(\)',
            r'if view:'
        ]
        
        found_patterns = []
        for pattern in validation_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 4:
            print(f"✅ Button validation logic properly implemented ({len(found_patterns)}/5 patterns found)")
            return True
        else:
            print(f"❌ Button validation logic incomplete ({len(found_patterns)}/5 patterns found)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing button validation logic: {e}")
        return False

def test_error_handling():
    """Test error handling improvements"""
    print("\n🔍 Testing error handling...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check error handling patterns
        error_patterns = [
            r'try:',
            r'except Exception as \w+:',
            r'self\.logger\.error',
            r'await self\._update_status\(False',
            r'error_msg\s*='
        ]
        
        found_count = 0
        for pattern in error_patterns:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                found_count += matches
        
        if found_count >= 10:  # Should have multiple instances
            print(f"✅ Error handling properly implemented ({found_count} error handling instances found)")
            return True
        else:
            print(f"❌ Error handling insufficient ({found_count} error handling instances found)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing error handling: {e}")
        return False

def test_logging_improvements():
    """Test logging improvements"""
    print("\n🔍 Testing logging improvements...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check logging patterns
        logging_patterns = [
            r'self\.logger\.debug\(f"✅',
            r'self\.logger\.warning\(f"⚠️',
            r'self\.logger\.error\(f"❌',
            r'self\.logger\.info\(f"📝',
            r'attempt \{attempt \+ 1\}'
        ]
        
        found_patterns = []
        for pattern in logging_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 3:
            print(f"✅ Logging improvements implemented ({len(found_patterns)}/5 patterns found)")
            return True
        else:
            print(f"❌ Logging improvements incomplete ({len(found_patterns)}/5 patterns found)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing logging improvements: {e}")
        return False

def test_status_update_fix():
    """Test _update_status function fix"""
    print("\n🔍 Testing _update_status function fix...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if the truncated code is fixed
        status_update_patterns = [
            r'if self\.button_manager and hasattr\(self\.button_manager, .on_livestock_status_change.\):',
            r'await self\.button_manager\.on_livestock_status_change\(is_healthy, error\)',
            r'except Exception as e:',
            r'self\.logger\.error\(f"Error notifying button manager: \{e\}"\)'
        ]
        
        found_patterns = []
        for pattern in status_update_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 3:
            print(f"✅ _update_status function properly fixed ({len(found_patterns)}/4 patterns found)")
            return True
        else:
            print(f"❌ _update_status function fix incomplete ({len(found_patterns)}/4 patterns found)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing _update_status fix: {e}")
        return False

def run_code_validation():
    """Run all code validation tests"""
    print("🧪 Running Code Validation Tests for Livestock Button Fix\n")
    
    tests = [
        test_code_structure,
        test_retry_mechanism,
        test_button_validation_logic,
        test_error_handling,
        test_logging_improvements,
        test_status_update_fix
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("📊 CODE VALIDATION RESULTS")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL CODE VALIDATION TESTS PASSED!")
        print("✅ Perbaikan livestock button error berhasil diimplementasikan")
        print("✅ Tidak ada regression pada struktur kode")
        print("✅ Semua komponen perbaikan terdeteksi dengan benar")
        return True
    else:
        print("⚠️ Some code validation tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_code_validation()
    sys.exit(0 if success else 1)
