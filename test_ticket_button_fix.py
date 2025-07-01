#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan tombol ticket
"""

import sys
import os
sys.path.append('/home/user/workspace')

def test_imports():
    """Test import semua modul ticket"""
    try:
        from src.cogs.ticket.ticket_cog import TicketSystem
        from src.cogs.ticket.views.ticket_view import TicketView, TicketControlView, TicketConfirmView
        print("✅ Semua import berhasil")
        return True
    except Exception as e:
        print(f"❌ Error import: {e}")
        return False

def test_view_creation():
    """Test pembuatan view instances"""
    try:
        from src.cogs.ticket.views.ticket_view import TicketView, TicketControlView, TicketConfirmView
        
        # Test TicketControlView
        control_view = TicketControlView()
        print(f"✅ TicketControlView berhasil dibuat dengan timeout: {control_view.timeout}")
        
        # Test TicketView
        ticket_view = TicketView(12345)
        print(f"✅ TicketView berhasil dibuat dengan ticket_id: {ticket_view.ticket_id}")
        
        # Test TicketConfirmView
        confirm_view = TicketConfirmView()
        print(f"✅ TicketConfirmView berhasil dibuat dengan timeout: {confirm_view.timeout}")
        
        return True
    except Exception as e:
        print(f"❌ Error membuat view: {e}")
        return False

def test_button_custom_ids():
    """Test custom_id pada tombol"""
    try:
        from src.cogs.ticket.views.ticket_view import TicketView, TicketControlView
        
        # Test TicketControlView button
        control_view = TicketControlView()
        create_button = None
        for item in control_view.children:
            if hasattr(item, 'custom_id') and item.custom_id == 'create_ticket':
                create_button = item
                break
        
        if create_button:
            print(f"✅ Create ticket button ditemukan dengan custom_id: {create_button.custom_id}")
        else:
            print("❌ Create ticket button tidak ditemukan")
            return False
        
        # Test TicketView button
        ticket_view = TicketView(12345)
        close_button = None
        for item in ticket_view.children:
            if hasattr(item, 'custom_id') and item.custom_id.startswith('close_ticket_'):
                close_button = item
                break
        
        if close_button:
            print(f"✅ Close ticket button ditemukan dengan custom_id: {close_button.custom_id}")
        else:
            print("❌ Close ticket button tidak ditemukan")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing custom_ids: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Memulai test perbaikan tombol ticket...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("View Creation Test", test_view_creation),
        ("Button Custom ID Test", test_button_custom_ids)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Semua test berhasil! Perbaikan tombol ticket siap digunakan.")
        return True
    else:
        print("⚠️  Beberapa test gagal. Perlu perbaikan lebih lanjut.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
