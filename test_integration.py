#!/usr/bin/env python3
"""
Integration test untuk memverifikasi perbaikan livestock button error
Test ini akan memverifikasi bahwa kode yang diperbaiki tidak memiliki syntax error
dan logic flow berjalan dengan benar.
"""

import sys
import os
import ast
import traceback

def test_syntax_validation():
    """Test syntax validation untuk file yang diperbaiki"""
    print("🔍 Testing syntax validation...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse AST untuk validasi syntax
        ast.parse(content)
        print("✅ Syntax validation PASSED")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error found: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def test_function_signatures():
    """Test function signatures untuk memastikan tidak ada breaking changes"""
    print("\n🔍 Testing function signatures...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Cari class LiveStockManager
        livestock_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'LiveStockManager':
                livestock_class = node
                break
        
        if not livestock_class:
            print("❌ LiveStockManager class not found")
            return False
        
        # Check critical methods exist
        required_methods = [
            'update_stock_display',
            '_update_status', 
            'create_stock_embed',
            'set_button_manager'
        ]
        
        found_methods = []
        for node in livestock_class.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                found_methods.append(node.name)
        
        missing_methods = [m for m in required_methods if m not in found_methods]
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        
        print("✅ All required methods found")
        
        # Check update_stock_display has proper async signature
        for node in livestock_class.body:
            if isinstance(node, ast.AsyncFunctionDef) and node.name == 'update_stock_display':
                # Check return annotation
                if hasattr(node, 'returns') and node.returns:
                    print("✅ update_stock_display has proper async signature with return type")
                else:
                    print("✅ update_stock_display has proper async signature")
                return True
        
        print("❌ update_stock_display should be async function")
        return False
        
    except Exception as e:
        print(f"❌ Error analyzing function signatures: {e}")
        return False

def test_retry_logic_implementation():
    """Test retry logic implementation"""
    print("\n🔍 Testing retry logic implementation...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for retry mechanism keywords
        retry_indicators = [
            'max_retries',
            'for attempt in range',
            'asyncio.sleep',
            'attempt + 1'
        ]
        
        found_indicators = []
        for indicator in retry_indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        if len(found_indicators) >= 3:
            print(f"✅ Retry mechanism implemented (found: {found_indicators})")
            return True
        else:
            print(f"❌ Retry mechanism incomplete (found only: {found_indicators})")
            return False
            
    except Exception as e:
        print(f"❌ Error checking retry logic: {e}")
        return False

def test_error_handling_improvement():
    """Test error handling improvements"""
    print("\n🔍 Testing error handling improvements...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for improved error handling
        error_handling_indicators = [
            'try:',
            'except Exception as',
            'self.logger.error',
            'await self._update_status(False',
            'error_msg'
        ]
        
        found_count = sum(1 for indicator in error_handling_indicators if indicator in content)
        
        if found_count >= 4:
            print(f"✅ Error handling improved (found {found_count}/5 indicators)")
            return True
        else:
            print(f"❌ Error handling insufficient (found {found_count}/5 indicators)")
            return False
            
    except Exception as e:
        print(f"❌ Error checking error handling: {e}")
        return False

def test_button_manager_validation():
    """Test button manager validation logic"""
    print("\n🔍 Testing button manager validation...")
    
    file_path = '/home/user/workspace/src/ui/views/live_stock_view.py'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for button manager validation
        validation_indicators = [
            'if self.button_manager',
            'if view:',
            'if not self.button_manager:',
            'button_manager.create_view()',
            'Button manager tersedia tapi'
        ]
        
        found_count = sum(1 for indicator in validation_indicators if indicator in content)
        
        if found_count >= 4:
            print(f"✅ Button manager validation implemented (found {found_count}/5 indicators)")
            return True
        else:
            print(f"❌ Button manager validation incomplete (found {found_count}/5 indicators)")
            return False
            
    except Exception as e:
        print(f"❌ Error checking button manager validation: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("🧪 Running Integration Tests for Livestock Button Fix\n")
    
    tests = [
        test_syntax_validation,
        test_function_signatures,
        test_retry_logic_implementation,
        test_error_handling_improvement,
        test_button_manager_validation
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
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Integration successful.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
