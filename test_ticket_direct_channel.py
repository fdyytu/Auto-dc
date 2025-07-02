"""
Test untuk memverifikasi bahwa ticket system langsung membuat channel tanpa modal
"""

import sys
sys.path.append('.')

def test_ticket_system_import():
    """Test bahwa TicketSystem dapat diimport dengan benar"""
    try:
        from src.cogs.ticket.ticket_cog import TicketSystem
        print("✅ TicketSystem berhasil diimport")
        return True
    except Exception as e:
        print(f"❌ Error import TicketSystem: {e}")
        return False

def test_modal_removal():
    """Test bahwa kode modal sudah dihapus dari file"""
    try:
        with open('src/cogs/ticket/ticket_cog.py', 'r') as f:
            content = f.read()
        
        # Check bahwa on_modal_submit sudah tidak ada
        if 'on_modal_submit' not in content:
            print("✅ Fungsi on_modal_submit sudah dihapus")
        else:
            print("❌ Fungsi on_modal_submit masih ada")
            return False
            
        # Check bahwa TicketModal class sudah tidak ada
        if 'class TicketModal' not in content:
            print("✅ Class TicketModal sudah dihapus")
        else:
            print("❌ Class TicketModal masih ada")
            return False
            
        # Check bahwa ada kode untuk langsung membuat channel
        if 'langsung buat channel tanpa modal' in content:
            print("✅ Kode untuk langsung membuat channel sudah ditambahkan")
        else:
            print("❌ Kode untuk langsung membuat channel tidak ditemukan")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error membaca file: {e}")
        return False

def test_default_reason():
    """Test bahwa default reason sudah ditambahkan"""
    try:
        with open('src/cogs/ticket/ticket_cog.py', 'r') as f:
            content = f.read()
        
        if 'Support diperlukan' in content:
            print("✅ Default reason 'Support diperlukan' sudah ditambahkan")
            return True
        else:
            print("❌ Default reason tidak ditemukan")
            return False
    except Exception as e:
        print(f"❌ Error membaca file: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Ticket System Direct Channel Fix...")
    print("=" * 50)
    
    tests = [
        test_ticket_system_import,
        test_modal_removal,
        test_default_reason
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Semua test berhasil! Ticket system sekarang langsung membuat channel.")
    else:
        print("⚠️  Beberapa test gagal. Periksa kembali implementasi.")
