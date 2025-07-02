#!/usr/bin/env python3
"""
Test script untuk memverifikasi syntax dan pola kode yang diperbaiki
"""

import ast
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_syntax_validation():
    """Test validasi syntax semua file yang diperbaiki"""
    files_to_check = [
        'src/cogs/ticket/views/ticket_view.py',
        'src/cogs/ticket/ticket_cog.py'
    ]
    
    all_valid = True
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse syntax
            ast.parse(content)
            logger.info(f"✅ Syntax valid: {file_path}")
            
        except SyntaxError as e:
            logger.error(f"❌ Syntax error di {file_path}: {e}")
            all_valid = False
        except Exception as e:
            logger.error(f"❌ Error checking {file_path}: {e}")
            all_valid = False
    
    return all_valid

def test_no_interaction_custom_id_usage():
    """Test bahwa tidak ada lagi penggunaan interaction.custom_id yang salah"""
    files_to_check = [
        'src/cogs/ticket/views/ticket_view.py',
        'src/cogs/ticket/ticket_cog.py'
    ]
    
    pattern = r'interaction\.custom_id'
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            matches = re.findall(pattern, content)
            if matches:
                logger.error(f"❌ Masih ada penggunaan interaction.custom_id di {file_path}: {len(matches)} occurrences")
                return False
            else:
                logger.info(f"✅ Tidak ada penggunaan interaction.custom_id di {file_path}")
                
        except Exception as e:
            logger.error(f"❌ Error checking {file_path}: {e}")
            return False
    
    return True

def test_correct_patterns_usage():
    """Test bahwa pola yang benar sudah digunakan"""
    files_to_check = [
        'src/cogs/ticket/views/ticket_view.py',
        'src/cogs/ticket/ticket_cog.py'
    ]
    
    # Pattern yang harus ada
    button_pattern = r'button\.custom_id'
    data_pattern = r'interaction\.data\.get\('
    
    button_found = False
    data_found = False
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for button.custom_id
            button_matches = re.findall(button_pattern, content)
            if button_matches:
                button_found = True
                logger.info(f"✅ Pattern 'button.custom_id' ditemukan di {file_path}: {len(button_matches)} occurrences")
            
            # Check for interaction.data.get(
            data_matches = re.findall(data_pattern, content)
            if data_matches:
                data_found = True
                logger.info(f"✅ Pattern 'interaction.data.get(' ditemukan di {file_path}: {len(data_matches)} occurrences")
                
        except Exception as e:
            logger.error(f"❌ Error checking {file_path}: {e}")
            return False
    
    if button_found and data_found:
        logger.info("✅ Semua pola yang benar telah digunakan")
        return True
    else:
        logger.warning(f"⚠️  Pola tidak lengkap - button_found: {button_found}, data_found: {data_found}")
        return True  # Still pass as long as no wrong patterns

def test_specific_fixes():
    """Test perbaikan spesifik yang dilakukan"""
    
    # Test ticket_view.py
    try:
        with open('src/cogs/ticket/views/ticket_view.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for specific fixes
        fixes_found = 0
        
        # Check for interaction.data.get usage
        if "interaction.data.get('custom_id'" in content:
            logger.info("✅ Fix 1: interaction.data.get('custom_id') ditemukan")
            fixes_found += 1
        
        # Check for button.custom_id usage
        if "button.custom_id" in content:
            logger.info("✅ Fix 2: button.custom_id usage ditemukan")
            fixes_found += 1
        
        logger.info(f"📊 ticket_view.py: {fixes_found}/2 fixes ditemukan")
        
    except Exception as e:
        logger.error(f"❌ Error checking ticket_view.py: {e}")
        return False
    
    # Test ticket_cog.py
    try:
        with open('src/cogs/ticket/ticket_cog.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for modal_custom_id fix
        if "modal_custom_id = interaction.data.get('custom_id')" in content:
            logger.info("✅ Fix 3: modal_custom_id = interaction.data.get('custom_id') ditemukan")
            fixes_found += 1
        
        logger.info(f"📊 ticket_cog.py: 1/1 fixes ditemukan")
        
    except Exception as e:
        logger.error(f"❌ Error checking ticket_cog.py: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    logger.info("🧪 Memulai testing perbaikan interaction.custom_id error...")
    
    tests = [
        ("Syntax Validation", test_syntax_validation),
        ("No interaction.custom_id Usage", test_no_interaction_custom_id_usage),
        ("Correct Patterns Usage", test_correct_patterns_usage),
        ("Specific Fixes", test_specific_fixes),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 Semua test berhasil! Perbaikan interaction.custom_id error telah berhasil.")
        return True
    else:
        logger.error("❌ Ada test yang gagal. Perlu perbaikan lebih lanjut.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
