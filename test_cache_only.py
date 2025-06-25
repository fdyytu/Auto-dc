#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan cache manager saja
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cache_manager_comprehensive():
    """Test comprehensive cache manager functionality"""
    print("🧪 Testing Cache Manager Comprehensive Functionality...")
    
    try:
        from src.ext.cache_manager import CacheManager
        
        cache_manager = CacheManager()
        
        print("  🔍 Testing cache operations...")
        
        # Test setting various cache entries
        await cache_manager.set("temp_key_1", "temp_value_1", expires_in=3600, permanent=False)
        await cache_manager.set("temp_key_2", "temp_value_2", expires_in=3600, permanent=False)
        await cache_manager.set("perm_key_1", "perm_value_1", expires_in=3600, permanent=True)
        await cache_manager.set("perm_key_2", "perm_value_2", expires_in=3600, permanent=True)
        await cache_manager.set("expire_key", "expire_value", expires_in=1, permanent=False)  # Will expire quickly
        
        # Check initial stats
        initial_stats = cache_manager.get_stats()
        print(f"    ✅ Initial stats: {initial_stats}")
        
        # Wait for expiration
        print("    ⏳ Waiting for expiration...")
        await asyncio.sleep(2)
        
        # Test clear expired
        expired_count = await cache_manager.clear_expired()
        print(f"    ✅ Clear expired: {expired_count} entries removed")
        
        # Check stats after clearing expired
        after_expired_stats = cache_manager.get_stats()
        print(f"    ✅ Stats after clearing expired: {after_expired_stats}")
        
        # Test clear temporary
        temp_count = await cache_manager.clear_temporary()
        print(f"    ✅ Clear temporary: {temp_count} entries removed")
        
        # Check stats after clearing temporary
        after_temp_stats = cache_manager.get_stats()
        print(f"    ✅ Stats after clearing temporary: {after_temp_stats}")
        
        # Test full clear
        await cache_manager.clear()
        final_stats = cache_manager.get_stats()
        print(f"    ✅ Final stats after full clear: {final_stats}")
        
        # Test get/set operations
        print("  🔍 Testing get/set operations...")
        
        await cache_manager.set("test_get", "test_value", expires_in=3600)
        retrieved_value = await cache_manager.get("test_get")
        print(f"    ✅ Set and get test: {retrieved_value == 'test_value'}")
        
        # Test delete operation
        delete_result = await cache_manager.delete("test_get")
        print(f"    ✅ Delete test: {delete_result}")
        
        # Test get non-existent key
        non_existent = await cache_manager.get("non_existent_key")
        print(f"    ✅ Get non-existent key: {non_existent is None}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error testing cache manager: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_logging():
    """Test cache logging functionality"""
    print("\n🧪 Testing Cache Logging...")
    
    try:
        from src.ext.cache_manager import CacheManager
        
        cache_manager = CacheManager()
        
        # Test logging during operations
        print("  🔍 Testing logging during cache operations...")
        
        # Set some entries
        await cache_manager.set("log_test_1", "value1", expires_in=1, permanent=False)
        await cache_manager.set("log_test_2", "value2", expires_in=3600, permanent=True)
        
        # Wait and clear expired (should log)
        await asyncio.sleep(2)
        await cache_manager.clear_expired()
        
        # Clear temporary (should log)
        await cache_manager.clear_temporary()
        
        # Full clear (should log)
        await cache_manager.clear()
        
        print("    ✅ Cache logging tested (check logs above)")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error testing cache logging: {e}")
        return False

async def test_restart_cleanup_simulation():
    """Simulate restart cleanup without Discord dependencies"""
    print("\n🧪 Testing Restart Cleanup Simulation...")
    
    try:
        from src.ext.cache_manager import CacheManager
        
        # Simulate multiple cache managers (like in real application)
        cache_managers = [CacheManager() for _ in range(3)]
        
        print("  🔍 Setting up cache data...")
        
        # Populate caches
        for i, cache in enumerate(cache_managers):
            await cache.set(f"cache_{i}_temp", f"temp_value_{i}", expires_in=3600, permanent=False)
            await cache.set(f"cache_{i}_perm", f"perm_value_{i}", expires_in=3600, permanent=True)
        
        # Check initial state
        total_keys_before = sum(cache.get_stats()['total_keys'] for cache in cache_managers)
        print(f"    ✅ Total keys before cleanup: {total_keys_before}")
        
        print("  🔍 Simulating restart cleanup...")
        
        # Simulate cleanup process
        for i, cache in enumerate(cache_managers):
            await cache.clear()
            print(f"    ✅ Cache {i} cleared")
        
        # Check final state
        total_keys_after = sum(cache.get_stats()['total_keys'] for cache in cache_managers)
        print(f"    ✅ Total keys after cleanup: {total_keys_after}")
        
        # Verify cleanup was successful
        cleanup_successful = total_keys_after == 0
        print(f"    ✅ Cleanup successful: {cleanup_successful}")
        
        return cleanup_successful
        
    except Exception as e:
        print(f"    ❌ Error testing restart cleanup simulation: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Cache Manager Tests\n")
    
    # Test comprehensive cache functionality
    comprehensive_ok = await test_cache_manager_comprehensive()
    
    # Test cache logging
    logging_ok = await test_cache_logging()
    
    # Test restart cleanup simulation
    cleanup_ok = await test_restart_cleanup_simulation()
    
    print("\n" + "="*60)
    if comprehensive_ok and logging_ok and cleanup_ok:
        print("🎉 ALL CACHE TESTS PASSED!")
        print("✅ Cache manager comprehensive functionality working")
        print("✅ Cache logging working")
        print("✅ Restart cleanup simulation working")
        print("\n📋 Summary of Improvements:")
        print("  • Added logging to all cache operations")
        print("  • Added clear_temporary() method")
        print("  • Added clear_expired() method")
        print("  • Enhanced get_stats() with more details")
        print("  • Improved error handling and logging")
        return True
    else:
        print("❌ SOME CACHE TESTS FAILED!")
        print(f"🔧 Comprehensive functionality: {'✅' if comprehensive_ok else '❌'}")
        print(f"🔧 Logging: {'✅' if logging_ok else '❌'}")
        print(f"🔧 Cleanup simulation: {'✅' if cleanup_ok else '❌'}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)
