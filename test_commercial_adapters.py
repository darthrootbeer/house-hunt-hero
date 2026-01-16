"""Test script for commercial real estate adapters."""

import sys
from datetime import datetime

from src.ingestion.adapters import (
    BoulosCompanyAdapter,
    NECPEAdapter,
    MaloneCommercialAdapter,
    LoopNetAdapter,
    NAIDunhamAdapter,
)


def test_adapter(adapter_class, adapter_name):
    """Test a single adapter and print results."""
    print(f"\n{'='*70}")
    print(f"Testing: {adapter_name}")
    print(f"{'='*70}")
    
    try:
        adapter = adapter_class()
        print(f"Adapter ID: {adapter.source_id}")
        print(f"Starting fetch at {datetime.now().strftime('%H:%M:%S')}...")
        
        listings = adapter.fetch()
        
        print(f"✅ SUCCESS: Found {len(listings)} listings")
        
        if listings:
            print(f"\nSample listing:")
            sample = listings[0]
            print(f"  - Title: {sample.title}")
            print(f"  - URL: {sample.listing_url}")
            print(f"  - Source: {sample.source}")
            print(f"  - Timestamp: {sample.source_timestamp}")
            print(f"  - Payload keys: {list(sample.raw_payload.keys())}")
            if sample.raw_payload.get('price'):
                print(f"  - Price: {sample.raw_payload['price']}")
            if sample.raw_payload.get('sqft'):
                print(f"  - Sqft: {sample.raw_payload['sqft']}")
            if sample.raw_payload.get('units'):
                print(f"  - Units: {sample.raw_payload['units']}")
        
        return True, len(listings)
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0


def main():
    """Test all commercial adapters."""
    adapters = [
        (BoulosCompanyAdapter, "The Boulos Company"),
        (NECPEAdapter, "NECPE - New England Commercial Property Exchange"),
        (MaloneCommercialAdapter, "Malone Commercial Brokers"),
        (LoopNetAdapter, "LoopNet - Multi-Family"),
        (NAIDunhamAdapter, "NAI The Dunham Group"),
    ]
    
    print("="*70)
    print("COMMERCIAL REAL ESTATE ADAPTERS TEST")
    print("="*70)
    print(f"Testing {len(adapters)} commercial adapters")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    total_listings = 0
    
    for adapter_class, adapter_name in adapters:
        success, count = test_adapter(adapter_class, adapter_name)
        results.append((adapter_name, success, count))
        total_listings += count
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    for name, success, count in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name}: {count} listings")
    
    passed = sum(1 for _, success, _ in results if success)
    print(f"\n{passed}/{len(adapters)} adapters passed")
    print(f"Total listings: {total_listings}")
    
    if passed == len(adapters):
        print("\n🎉 All commercial adapters working!")
        return 0
    else:
        print(f"\n⚠️  {len(adapters) - passed} adapter(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
