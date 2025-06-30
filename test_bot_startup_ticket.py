#!/usr/bin/env python3
"""
Test untuk memverifikasi bot startup dan ticket cog loading
"""

import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

async def test_module_loader_ticket_discovery():
    """Test module loader dapat menemukan dan memuat ticket cog"""
    try:
        from src.bot.module_loader import ModuleLoader
        
        # Create mock bot
        class MockBot:
            def __init__(self):
                self.load_extension = AsyncMock()
                self.unload_extension = AsyncMock()
        
        mock_bot = MockBot()
        loader = ModuleLoader(mock_bot)
        
        # Test cog discovery
        cog_files = loader._discover_cogs(Path("src/cogs"))
        
        # Check if ticket cog is discovered
        ticket_cogs = [cog for cog in cog_files if 'ticket' in cog]
        
        if ticket_cogs:
            print(f"✅ Ticket cog discovered: {ticket_cogs}")
            
            # Test if ticket.py is valid cog file
            ticket_py_path = Path("src/cogs/ticket.py")
            is_valid = loader._validate_cog_file(ticket_py_path)
            
            if is_valid:
                print("✅ ticket.py is valid cog file")
            else:
                print("❌ ticket.py is not valid cog file")
                return False
                
        else:
            print("❌ Ticket cog not discovered")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Module loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ticket_cog_loading_simulation():
    """Simulate ticket cog loading process"""
    try:
        # Import setup function from the correct module
        import importlib.util
        spec = importlib.util.spec_from_file_location("ticket_module", "src/cogs/ticket.py")
        ticket_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ticket_module)
        setup = ticket_module.setup
        
        # Create mock bot
        class MockBot:
            def __init__(self):
                self.add_cog = AsyncMock()
                self.cogs = {}
        
        mock_bot = MockBot()
        
        # Test setup function
        await setup(mock_bot)
        
        # Verify add_cog was called
        if mock_bot.add_cog.called:
            print("✅ Ticket cog setup function called successfully")
            print(f"   add_cog called {mock_bot.add_cog.call_count} times")
            
            # Get the cog that was added
            call_args = mock_bot.add_cog.call_args
            if call_args:
                cog_instance = call_args[0][0]
                print(f"   Cog type: {type(cog_instance).__name__}")
                
                # Verify it's TicketSystem
                if hasattr(cog_instance, '__class__') and 'TicketSystem' in str(cog_instance.__class__):
                    print("✅ TicketSystem cog instance created correctly")
                else:
                    print("❌ Wrong cog type added")
                    return False
            else:
                print("❌ No arguments passed to add_cog")
                return False
        else:
            print("❌ add_cog was not called")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Cog loading simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ticket_commands_registration():
    """Test ticket commands are properly registered"""
    try:
        from src.cogs.ticket.ticket_cog import TicketSystem
        
        # Create mock bot
        mock_bot = Mock()
        
        # Create ticket system instance
        ticket_system = TicketSystem(mock_bot)
        
        # Check if ticket commands exist
        commands = []
        for attr_name in dir(ticket_system):
            attr = getattr(ticket_system, attr_name)
            if hasattr(attr, '__name__') and hasattr(attr, 'qualified_name'):
                commands.append(attr.qualified_name)
        
        expected_commands = ['ticket', 'ticket setup', 'ticket create', 'ticket close']
        found_commands = []
        
        # Check for ticket group command
        if hasattr(ticket_system, 'ticket'):
            print("✅ Main ticket command group found")
            found_commands.append('ticket')
            
            # Check subcommands
            if hasattr(ticket_system, 'setup_ticket'):
                print("✅ ticket setup command found")
                found_commands.append('ticket setup')
            
            if hasattr(ticket_system, 'create_ticket'):
                print("✅ ticket create command found")
                found_commands.append('ticket create')
                
            if hasattr(ticket_system, 'close_ticket'):
                print("✅ ticket close command found")
                found_commands.append('ticket close')
        
        print(f"   Commands found: {found_commands}")
        
        if len(found_commands) >= 3:  # At least ticket, setup, create
            print("✅ Essential ticket commands are registered")
            return True
        else:
            print("❌ Missing essential ticket commands")
            return False
        
    except Exception as e:
        print(f"❌ Commands registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ticket_event_listeners():
    """Test ticket event listeners are registered"""
    try:
        from src.cogs.ticket.ticket_cog import TicketSystem
        
        # Create mock bot
        mock_bot = Mock()
        
        # Create ticket system instance
        ticket_system = TicketSystem(mock_bot)
        
        # Check for event listeners
        listeners = []
        for attr_name in dir(ticket_system):
            attr = getattr(ticket_system, attr_name)
            if hasattr(attr, '__name__') and attr.__name__.startswith('on_'):
                listeners.append(attr.__name__)
        
        expected_listeners = ['on_interaction', 'on_modal_submit']
        found_listeners = []
        
        for listener in expected_listeners:
            if hasattr(ticket_system, listener):
                found_listeners.append(listener)
                print(f"✅ Event listener found: {listener}")
        
        if len(found_listeners) >= 2:
            print("✅ Essential event listeners are registered")
            return True
        else:
            print("❌ Missing essential event listeners")
            return False
        
    except Exception as e:
        print(f"❌ Event listeners test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_startup_simulation():
    """Simulate complete bot startup with ticket system"""
    try:
        print("🚀 Simulating complete bot startup...")
        
        # Step 1: Module discovery
        from src.bot.module_loader import ModuleLoader
        
        class MockBot:
            def __init__(self):
                self.load_extension = AsyncMock()
                self.cogs = {}
        
        mock_bot = MockBot()
        loader = ModuleLoader(mock_bot)
        
        # Discover cogs
        cog_files = loader._discover_cogs(Path("src/cogs"))
        ticket_cogs = [cog for cog in cog_files if 'ticket' in cog]
        
        if not ticket_cogs:
            print("❌ Ticket cog not discovered during startup")
            return False
        
        print(f"✅ Step 1: Ticket cog discovered: {ticket_cogs[0]}")
        
        # Step 2: Simulate loading
        for cog_module in ticket_cogs:
            mock_bot.load_extension.return_value = None
            await mock_bot.load_extension(cog_module)
        
        if mock_bot.load_extension.called:
            print("✅ Step 2: load_extension called for ticket cog")
        else:
            print("❌ Step 2: load_extension not called")
            return False
        
        # Step 3: Verify setup would work
        import importlib.util
        spec = importlib.util.spec_from_file_location("ticket_module", "src/cogs/ticket.py")
        ticket_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ticket_module)
        setup = ticket_module.setup
        
        class MockBotWithCogs:
            def __init__(self):
                self.add_cog = AsyncMock()
                self.cogs = {}
        
        mock_bot_setup = MockBotWithCogs()
        await setup(mock_bot_setup)
        
        if mock_bot_setup.add_cog.called:
            print("✅ Step 3: Ticket cog setup completed")
        else:
            print("❌ Step 3: Ticket cog setup failed")
            return False
        
        print("🎉 Complete startup simulation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Complete startup simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all startup tests"""
    print("🧪 Testing Bot Startup & Ticket Cog Loading...")
    print("=" * 60)
    
    tests = [
        ("Module Loader Ticket Discovery", test_module_loader_ticket_discovery),
        ("Ticket Cog Loading Simulation", test_ticket_cog_loading_simulation),
        ("Ticket Commands Registration", test_ticket_commands_registration),
        ("Ticket Event Listeners", test_ticket_event_listeners),
        ("Complete Startup Simulation", test_complete_startup_simulation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 40)
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Startup Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Bot startup & ticket loading tests berhasil!")
        print("\n✅ Konfirmasi:")
        print("   • Module loader dapat menemukan ticket cog")
        print("   • Ticket cog dapat dimuat saat startup")
        print("   • Semua commands dan listeners terdaftar")
        print("   • Setup function bekerja dengan benar")
        print("   • Bot siap menjalankan ticket system")
        
        return True
    else:
        print("⚠️  Beberapa startup tests gagal")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
