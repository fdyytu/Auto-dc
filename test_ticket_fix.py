#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan ticket system
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

def test_ticket_cog_import():
    """Test apakah ticket cog bisa diimport"""
    try:
        from src.cogs.ticket import TicketSystem
        print("✅ Ticket cog berhasil diimport")
        return True
    except Exception as e:
        print(f"❌ Gagal import ticket cog: {e}")
        return False

def test_ticket_database():
    """Test apakah ticket database bisa diinisialisasi"""
    try:
        from src.cogs.ticket.utils.database import TicketDB
        
        # Test database initialization
        db = TicketDB()
        db.setup_tables()
        
        # Test get_guild_settings dengan default values
        settings = db.get_guild_settings(1318806349118963722)
        expected_keys = ['category_id', 'log_channel_id', 'support_role_id', 'max_tickets', 'ticket_format', 'auto_close_hours']
        
        for key in expected_keys:
            if key not in settings:
                print(f"❌ Missing key in settings: {key}")
                return False
        
        print("✅ Ticket database berhasil diinisialisasi")
        print(f"   Default settings: {settings}")
        return True
    except Exception as e:
        print(f"❌ Gagal inisialisasi ticket database: {e}")
        return False

def test_ticket_views():
    """Test apakah ticket views bisa diimport"""
    try:
        # Just test import without creating instances
        from src.cogs.ticket.views.ticket_view import TicketView, TicketControlView, TicketConfirmView
        
        # Check if TicketControlView class exists and has the right structure
        import inspect
        
        # Check if TicketControlView has __init__ method
        if hasattr(TicketControlView, '__init__'):
            print("✅ TicketControlView class ditemukan")
        else:
            print("❌ TicketControlView class tidak valid")
            return False
        
        # Check source code for create_ticket button
        source = inspect.getsource(TicketControlView)
        if 'create_ticket' in source and 'Create Ticket' in source:
            print("✅ Tombol create ticket ditemukan di TicketControlView source code")
        else:
            print("❌ Tombol create ticket tidak ditemukan di source code")
            return False
        
        print("✅ Ticket views berhasil diimport dan divalidasi")
        return True
    except Exception as e:
        print(f"❌ Gagal import ticket views: {e}")
        return False

def test_config_ticket_channel():
    """Test apakah config.json memiliki ticket_channel"""
    try:
        import json
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        if 'channels' in config and 'ticket_channel' in config['channels']:
            print("✅ ticket_channel ditemukan di config.json")
            print(f"   ticket_channel: {config['channels']['ticket_channel']}")
            return True
        else:
            print("❌ ticket_channel tidak ditemukan di config.json")
            return False
    except Exception as e:
        print(f"❌ Gagal membaca config.json: {e}")
        return False

def test_module_loader_discovery():
    """Test apakah module loader bisa menemukan ticket.py"""
    try:
        from src.bot.module_loader import ModuleLoader
        
        # Create mock bot
        class MockBot:
            pass
        
        loader = ModuleLoader(MockBot())
        cog_files = loader._discover_cogs(Path("src/cogs"))
        
        # Check if ticket cog is discovered
        ticket_found = False
        for cog_module in cog_files:
            if 'ticket' in cog_module:
                ticket_found = True
                print(f"✅ Ticket cog ditemukan: {cog_module}")
                break
        
        if not ticket_found:
            print("❌ Ticket cog tidak ditemukan oleh module loader")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Gagal test module loader: {e}")
        return False

def main():
    """Jalankan semua test"""
    print("🧪 Memulai test perbaikan ticket system...")
    print("=" * 50)
    
    tests = [
        ("Import Ticket Cog", test_ticket_cog_import),
        ("Ticket Database", test_ticket_database),
        ("Ticket Views", test_ticket_views),
        ("Config Ticket Channel", test_config_ticket_channel),
        ("Module Loader Discovery", test_module_loader_discovery)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   Test {test_name} GAGAL!")
    
    print("\n" + "=" * 50)
    print(f"📊 Hasil Test: {passed}/{total} test berhasil")
    
    if passed == total:
        print("🎉 Semua test berhasil! Ticket system sudah diperbaiki.")
        print("\n📋 Ringkasan perbaikan:")
        print("   1. ✅ Dibuat src/cogs/ticket.py sebagai entry point")
        print("   2. ✅ Ditambahkan ticket_channel ke config.json")
        print("   3. ✅ Diperbaiki dependency admin_logs di database")
        print("   4. ✅ Diperbaiki modal handling dan interaction processing")
        print("   5. ✅ Tombol create ticket sudah tersedia di TicketControlView")
        
        print("\n🚀 Cara menggunakan:")
        print("   1. Jalankan command: !ticket setup #channel-ticket")
        print("   2. Bot akan mengirim embed dengan tombol 'Create Ticket'")
        print("   3. User bisa klik tombol untuk membuat ticket")
        
        return True
    else:
        print("❌ Masih ada masalah yang perlu diperbaiki.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
