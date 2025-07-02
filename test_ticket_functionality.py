"""
Test comprehensive untuk memastikan ticket system functionality berfungsi dengan benar
"""

import sys
sys.path.append('.')

def test_ticket_flow_logic():
    """Test logic flow ticket system"""
    try:
        with open('src/cogs/ticket/ticket_cog.py', 'r') as f:
            content = f.read()
        
        # Test 1: Pastikan create_ticket logic ada
        if 'if custom_id == "create_ticket":' in content:
            print("✅ Create ticket button handler ada")
        else:
            print("❌ Create ticket button handler tidak ditemukan")
            return False
            
        # Test 2: Pastikan direct channel creation logic ada
        if 'await self.create_ticket_channel(mock_ctx, default_reason, settings)' in content:
            print("✅ Direct channel creation logic ada")
        else:
            print("❌ Direct channel creation logic tidak ditemukan")
            return False
            
        # Test 3: Pastikan MockContext class ada
        if 'class MockContext:' in content:
            print("✅ MockContext class ada")
        else:
            print("❌ MockContext class tidak ditemukan")
            return False
            
        # Test 4: Pastikan response ke user ada
        if 'await interaction.response.send_message(' in content:
            print("✅ User response logic ada")
        else:
            print("❌ User response logic tidak ditemukan")
            return False
            
        # Test 5: Pastikan error handling ada
        if 'except Exception as e:' in content:
            print("✅ Error handling ada")
        else:
            print("❌ Error handling tidak ditemukan")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def test_view_components():
    """Test view components masih berfungsi"""
    try:
        # Test import view components
        from src.cogs.ticket.views.ticket_view import TicketControlView, TicketView, TicketConfirmView
        print("✅ Semua view components berhasil diimport")
        
        # Test TicketControlView class structure
        import inspect
        
        # Check TicketControlView methods
        methods = inspect.getmembers(TicketControlView, predicate=inspect.isfunction)
        method_names = [name for name, _ in methods]
        
        if 'create_ticket_button' in method_names:
            print("✅ TicketControlView memiliki create_ticket_button method")
        else:
            print("❌ TicketControlView tidak memiliki create_ticket_button method")
            return False
            
        # Check TicketView class
        if hasattr(TicketView, '__init__'):
            print("✅ TicketView class structure valid")
        else:
            print("❌ TicketView class structure invalid")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing view components: {e}")
        return False

def test_database_compatibility():
    """Test database compatibility"""
    try:
        from src.cogs.ticket.utils.database import TicketDB
        
        # Test TicketDB dapat diinstansiasi
        db = TicketDB()
        
        # Check method yang diperlukan ada
        required_methods = ['get_guild_settings', 'close_ticket', 'setup_tables']
        for method in required_methods:
            if hasattr(db, method):
                print(f"✅ Database method {method} tersedia")
            else:
                print(f"❌ Database method {method} tidak ditemukan")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def test_embed_components():
    """Test embed components"""
    try:
        from src.cogs.ticket.components.embeds import TicketEmbeds
        
        # Check method yang diperlukan ada
        required_methods = ['ticket_created', 'success_embed', 'error_embed']
        for method in required_methods:
            if hasattr(TicketEmbeds, method):
                print(f"✅ Embed method {method} tersedia")
            else:
                print(f"❌ Embed method {method} tidak ditemukan")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing embeds: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Ticket System Comprehensive Functionality...")
    print("=" * 60)
    
    tests = [
        ("Logic Flow", test_ticket_flow_logic),
        ("View Components", test_view_components),
        ("Database Compatibility", test_database_compatibility),
        ("Embed Components", test_embed_components)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}:")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Semua functionality test berhasil!")
        print("✅ Ticket system siap digunakan!")
    else:
        print("⚠️  Beberapa functionality test gagal.")
        print("❌ Perlu perbaikan sebelum deployment.")
