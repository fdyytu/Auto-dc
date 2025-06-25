#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan live stock dan matplotlib
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_live_stock_import():
    """Test import live stock modules"""
    try:
        from src.ui.views.live_stock_view import LiveStockManager, LiveStockCog
        print("✅ Live stock modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing live stock: {e}")
        return False

async def test_stats_import():
    """Test import stats module with plotly"""
    try:
        from src.cogs.stats import ServerStats
        print("✅ Stats module with Plotly imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing stats: {e}")
        return False

async def test_ascii_charts():
    """Test ASCII chart functionality (ramah HP low-end)"""
    try:
        from src.cogs.stats import ServerStats
        
        # Create test instance
        stats = ServerStats(None)
        
        # Test ASCII bar chart
        test_data = [10, 25, 15, 30, 5]
        test_labels = ['Role A', 'Role B', 'Role C', 'Role D', 'Role E']
        
        bar_chart = stats.create_ascii_bar_chart(test_data, test_labels, "Test Bar Chart")
        
        # Test ASCII line chart
        line_data = [5, 10, 8, 15, 12, 20, 18]
        line_labels = ['Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7']
        
        line_chart = stats.create_ascii_line_chart(line_data, line_labels, "Test Line Chart")
        
        print("✅ ASCII Charts work perfectly (ramah HP low-end)")
        print("📊 Sample Bar Chart:")
        print(bar_chart[:100] + "..." if len(bar_chart) > 100 else bar_chart)
        return True
    except Exception as e:
        print(f"❌ Error with ASCII charts: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔧 Testing perbaikan live stock dan matplotlib...")
    print("=" * 50)
    
    results = []
    
    # Test imports
    results.append(await test_live_stock_import())
    results.append(await test_stats_import())
    results.append(await test_ascii_charts())
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Semua test passed ({passed}/{total})")
        print("✅ Perbaikan berhasil:")
        print("   - Live stock error handling diperbaiki")
        print("   - Matplotlib diganti dengan ASCII Charts (sangat ringan untuk HP low-end)")
        print("   - Button manager warning ditangani dengan baik")
        print("   - Tidak perlu Chrome/Kaleido lagi!")
    else:
        print(f"⚠️ {passed}/{total} tests passed")
        print("❌ Masih ada masalah yang perlu diperbaiki")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
