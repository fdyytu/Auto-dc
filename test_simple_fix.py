#!/usr/bin/env python3
"""
Test sederhana untuk memverifikasi perbaikan di modals.py
"""

import re

def test_modals_fix():
    """Test apakah perbaikan di modals.py sudah benar"""
    try:
        with open('/home/user/workspace/src/ui/buttons/components/modals.py', 'r') as f:
            content = f.read()
        
        # Cari semua instance BalanceService initialization
        balance_service_patterns = re.findall(r'balance_service = BalanceService\((.*?)\)', content)
        
        print("🔍 Memeriksa inisialisasi BalanceService di modals.py...")
        print("=" * 60)
        
        correct_count = 0
        total_count = len(balance_service_patterns)
        
        for i, pattern in enumerate(balance_service_patterns, 1):
            print(f"Instance {i}: BalanceService({pattern})")
            if pattern.strip() == 'interaction.client':
                print("  ✅ BENAR - menggunakan interaction.client")
                correct_count += 1
            elif 'interaction.client.db_manager' in pattern:
                print("  ❌ SALAH - masih menggunakan interaction.client.db_manager")
            else:
                print(f"  ⚠️  TIDAK DIKENAL - pattern: {pattern}")
        
        print("=" * 60)
        print(f"Total instance: {total_count}")
        print(f"Instance yang benar: {correct_count}")
        print(f"Instance yang salah: {total_count - correct_count}")
        
        if correct_count == total_count and total_count > 0:
            print("🎉 SEMUA PERBAIKAN BERHASIL!")
            return True
        else:
            print("❌ MASIH ADA YANG PERLU DIPERBAIKI!")
            return False
            
    except Exception as e:
        print(f"❌ Error saat membaca file: {e}")
        return False

def test_import_statement():
    """Test apakah import statement sudah benar"""
    try:
        with open('/home/user/workspace/src/ui/buttons/components/modals.py', 'r') as f:
            content = f.read()
        
        print("\n🔍 Memeriksa import statement...")
        print("=" * 60)
        
        # Cari import statement
        import_pattern = re.search(r'from src\.services\.balance_service import.*', content)
        if import_pattern:
            print(f"Import statement: {import_pattern.group()}")
            if 'BalanceManagerService as BalanceService' in import_pattern.group():
                print("✅ Import statement sudah benar")
                return True
            else:
                print("❌ Import statement perlu diperbaiki")
                return False
        else:
            print("❌ Import statement tidak ditemukan")
            return False
            
    except Exception as e:
        print(f"❌ Error saat memeriksa import: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing perbaikan BalanceService di modals.py...")
    
    test1_passed = test_modals_fix()
    test2_passed = test_import_statement()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 SEMUA TEST BERHASIL! Perbaikan sudah benar.")
        print("\n📋 Ringkasan perbaikan:")
        print("- ✅ BalanceService diinisialisasi dengan interaction.client")
        print("- ✅ Import statement menggunakan alias yang benar")
        print("- ✅ Tidak ada lagi penggunaan interaction.client.db_manager")
        print("\n🚀 Error 'dict' object has no attribute 'SUCCESS'/'ERROR' seharusnya sudah teratasi!")
    else:
        print("❌ ADA TEST YANG GAGAL. Perlu perbaikan lebih lanjut.")
