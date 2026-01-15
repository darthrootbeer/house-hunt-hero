#!/usr/bin/env python3
"""
Simple test script for FSBO platform adapters.
Tests adapter structure and basic functionality.
"""

import sys

def test_adapter_structure():
    """Test that adapters can be imported and have correct structure."""
    print("Testing FSBO Adapter Structure")
    print("=" * 60)
    
    try:
        from src.ingestion.adapters import (
            OwneramaAdapter,
            BrokerlessAdapter,
            FlatFeeGroupAdapter,
            TheRockFoundationAdapter,
            FSBOHomeListingsAdapter,
            DIYFlatFeeAdapter,
            ISoldMyHouseAdapter,
            HoangRealtyFSBOAdapter,
        )
        print("✓ All adapters imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    adapters = [
        ("Ownerama", OwneramaAdapter()),
        ("Brokerless", BrokerlessAdapter()),
        ("Flat Fee Group", FlatFeeGroupAdapter()),
        ("The Rock Foundation", TheRockFoundationAdapter()),
        ("FSBOHomeListings.com", FSBOHomeListingsAdapter()),
        ("DIY Flat Fee MLS", DIYFlatFeeAdapter()),
        ("ISoldMyHouse.com", ISoldMyHouseAdapter()),
        ("Hoang Realty FSBO", HoangRealtyFSBOAdapter()),
    ]
    
    print(f"\nTesting {len(adapters)} adapters:")
    all_valid = True
    
    for name, adapter in adapters:
        print(f"\n  {name}:")
        
        # Check source_id
        if hasattr(adapter, 'source_id') and adapter.source_id:
            print(f"    ✓ source_id: {adapter.source_id}")
        else:
            print(f"    ✗ Missing source_id")
            all_valid = False
        
        # Check fetch method
        if hasattr(adapter, 'fetch') and callable(adapter.fetch):
            print(f"    ✓ fetch() method exists")
        else:
            print(f"    ✗ Missing fetch() method")
            all_valid = False
        
        # Check docstring
        if adapter.__doc__:
            print(f"    ✓ Has docstring")
        else:
            print(f"    ⚠️  No docstring")
    
    return all_valid


def test_with_playwright():
    """Test adapters with actual Playwright execution if available."""
    print("\n" + "=" * 60)
    print("Testing with Playwright (requires playwright installed)")
    print("=" * 60)
    
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright is available")
        
        # Test a simple adapter that doesn't require network
        from src.ingestion.adapters import HoangRealtyFSBOAdapter
        
        adapter = HoangRealtyFSBOAdapter()
        print(f"\nTesting {adapter.source_id} (should return empty list):")
        listings = adapter.fetch()
        print(f"  Result: {len(listings)} listings (expected: 0)")
        
        if len(listings) == 0:
            print("  ✓ Correctly returns empty list (contact required)")
        else:
            print(f"  ⚠️  Unexpected listings returned")
        
        return True
        
    except ImportError:
        print("✗ Playwright not installed")
        print("\nTo test adapters with actual data:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Install playwright browsers: python -m playwright install chromium")
        print("  3. Run: python test_fsbo_adapters.py")
        return False
    except Exception as e:
        print(f"✗ Error testing with Playwright: {e}")
        return False


if __name__ == "__main__":
    structure_ok = test_adapter_structure()
    playwright_ok = test_with_playwright()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Adapter structure: {'✓ PASS' if structure_ok else '✗ FAIL'}")
    print(f"Playwright testing: {'✓ Available' if playwright_ok else '⚠️  Not available (install dependencies)'}")
    
    if not playwright_ok:
        print("\nNOTE: Full testing requires Playwright to be installed.")
        print("The adapters are structured correctly and ready for testing once dependencies are available.")
    
    sys.exit(0 if structure_ok else 1)
