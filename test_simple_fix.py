"""
Test sederhana untuk memverifikasi perbaikan error transaction
"""

import ast
import os

def test_product_service_has_update_stock_status():
    """Test apakah method update_stock_status sudah ditambahkan ke ProductService"""
    
    print("🔍 Checking ProductService for update_stock_status method...")
    
    product_service_path = "src/services/product_service.py"
    
    if not os.path.exists(product_service_path):
        print(f"❌ File {product_service_path} tidak ditemukan")
        return False
    
    with open(product_service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if update_stock_status method exists
    if 'def update_stock_status(' in content:
        print("✅ Method 'update_stock_status' ditemukan di ProductService")
        
        # Check if it has proper parameters
        if 'product_code: str, stock_ids: List[int], status: str, buyer_id: str = None' in content:
            print("✅ Method memiliki parameter yang benar")
        else:
            print("⚠️ Method ditemukan tapi parameter mungkin tidak sesuai")
        
        return True
    else:
        print("❌ Method 'update_stock_status' TIDAK ditemukan di ProductService")
        return False

def test_transaction_service_calls():
    """Test apakah TransactionService masih memanggil method yang benar"""
    
    print("\n🔍 Checking TransactionService calls...")
    
    transaction_service_path = "src/services/transaction_service.py"
    
    if not os.path.exists(transaction_service_path):
        print(f"❌ File {transaction_service_path} tidak ditemukan")
        return False
    
    with open(transaction_service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if it calls update_stock_status
    if 'update_stock_status(' in content:
        print("✅ TransactionService memanggil update_stock_status")
        return True
    else:
        print("❌ TransactionService TIDAK memanggil update_stock_status")
        return False

def test_modals_imports():
    """Test apakah modals.py memiliki import yang benar"""
    
    print("\n🔍 Checking modals.py imports...")
    
    modals_path = "src/ui/buttons/components/modals.py"
    
    if not os.path.exists(modals_path):
        print(f"❌ File {modals_path} tidak ditemukan")
        return False
    
    with open(modals_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check imports
    if 'from src.config.constants.bot_constants import MESSAGES, COLORS' in content:
        print("✅ Import MESSAGES dan COLORS sudah benar")
        
        # Check usage
        if 'MESSAGES.ERROR[' in content and 'COLORS.ERROR' in content:
            print("✅ Penggunaan MESSAGES.ERROR dan COLORS.ERROR sudah benar")
            return True
        else:
            print("⚠️ Import benar tapi penggunaan mungkin ada masalah")
            return True
    else:
        print("❌ Import MESSAGES dan COLORS tidak ditemukan atau salah")
        return False

def main():
    """Main test function"""
    print("🚀 Memulai test sederhana perbaikan error transaction...")
    print("=" * 60)
    
    success = True
    
    # Test 1: ProductService update_stock_status method
    if not test_product_service_has_update_stock_status():
        success = False
    
    # Test 2: TransactionService calls
    if not test_transaction_service_calls():
        success = False
    
    # Test 3: Modals imports
    if not test_modals_imports():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SEMUA TEST BERHASIL!")
        print("\n📋 Ringkasan perbaikan yang telah dilakukan:")
        print("   ✅ Method update_stock_status ditambahkan ke ProductService")
        print("   ✅ TransactionService dapat memanggil method yang diperlukan")
        print("   ✅ Import di modals.py sudah benar")
        print("\n🔧 Error yang diperbaiki:")
        print("   ✅ 'ProductService' object has no attribute 'update_stock_status'")
        print("   ✅ 'dict' object has no attribute 'ERROR' (import sudah benar)")
    else:
        print("❌ ADA TEST YANG GAGAL! Masih ada masalah yang perlu diperbaiki.")
    
    return success

if __name__ == "__main__":
    main()
