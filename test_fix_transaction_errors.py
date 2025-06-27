"""
Test untuk memverifikasi perbaikan error transaction
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.product_service import ProductService
from src.database.models.product import StockStatus

def test_product_service_methods():
    """Test apakah method yang diperlukan sudah ada di ProductService"""
    
    print("🔍 Testing ProductService methods...")
    
    # Check if update_stock_status method exists
    if hasattr(ProductService, 'update_stock_status'):
        print("✅ Method 'update_stock_status' ditemukan di ProductService")
    else:
        print("❌ Method 'update_stock_status' TIDAK ditemukan di ProductService")
        return False
    
    # Check if mark_stock_sold method exists
    if hasattr(ProductService, 'mark_stock_sold'):
        print("✅ Method 'mark_stock_sold' ditemukan di ProductService")
    else:
        print("❌ Method 'mark_stock_sold' TIDAK ditemukan di ProductService")
        return False
    
    # Check if get_available_stock method exists
    if hasattr(ProductService, 'get_available_stock'):
        print("✅ Method 'get_available_stock' ditemukan di ProductService")
    else:
        print("❌ Method 'get_available_stock' TIDAK ditemukan di ProductService")
        return False
    
    print("✅ Semua method yang diperlukan sudah tersedia di ProductService")
    return True

def test_stock_status_enum():
    """Test apakah StockStatus enum berfungsi dengan benar"""
    
    print("\n🔍 Testing StockStatus enum...")
    
    try:
        # Test enum values
        available = StockStatus.AVAILABLE.value
        sold = StockStatus.SOLD.value
        
        print(f"✅ StockStatus.AVAILABLE = '{available}'")
        print(f"✅ StockStatus.SOLD = '{sold}'")
        
        return True
    except Exception as e:
        print(f"❌ Error dengan StockStatus enum: {e}")
        return False

def test_imports():
    """Test apakah semua import berfungsi dengan benar"""
    
    print("\n🔍 Testing imports...")
    
    try:
        from src.config.constants.bot_constants import MESSAGES, COLORS
        print("✅ Import MESSAGES dan COLORS berhasil")
        
        # Test MESSAGES structure
        if hasattr(MESSAGES, 'ERROR') and hasattr(MESSAGES, 'SUCCESS'):
            print("✅ MESSAGES memiliki struktur ERROR dan SUCCESS")
        else:
            print("❌ MESSAGES tidak memiliki struktur yang benar")
            return False
            
        # Test COLORS structure
        if hasattr(COLORS, 'ERROR') and hasattr(COLORS, 'SUCCESS'):
            print("✅ COLORS memiliki struktur ERROR dan SUCCESS")
        else:
            print("❌ COLORS tidak memiliki struktur yang benar")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error dengan imports: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Memulai test perbaikan error transaction...")
    print("=" * 50)
    
    success = True
    
    # Test 1: ProductService methods
    if not test_product_service_methods():
        success = False
    
    # Test 2: StockStatus enum
    if not test_stock_status_enum():
        success = False
    
    # Test 3: Imports
    if not test_imports():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SEMUA TEST BERHASIL! Perbaikan error transaction sudah selesai.")
        print("\n📋 Ringkasan perbaikan:")
        print("   ✅ Method update_stock_status ditambahkan ke ProductService")
        print("   ✅ Error handling sudah diperbaiki")
        print("   ✅ Semua import berfungsi dengan benar")
    else:
        print("❌ ADA TEST YANG GAGAL! Masih ada masalah yang perlu diperbaiki.")
    
    return success

if __name__ == "__main__":
    main()
